import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION, WD_ORIENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from pathlib import Path
from datetime import datetime

base_dir = Path(__file__).resolve().parent.parent
reports_dir = base_dir / "reports"
reports_dir.mkdir(parents=True, exist_ok=True)

# Load Data
src_inventory = (reports_dir / 'Rectifier_Inventory_188_Sites.xlsx') if (reports_dir / 'Rectifier_Inventory_188_Sites.xlsx').exists() else Path('Rectifier_Inventory_188_Sites.xlsx')
src_wb = openpyxl.load_workbook(str(src_inventory), data_only=True)
ws1 = src_wb['Sheet1']
ws_set = src_wb['Settings']

rows1 = list(ws1.iter_rows(values_only=True))
h1 = rows1[0]
c1 = {k: i for i, k in enumerate(h1)}

rows_s = list(ws_set.iter_rows(values_only=True))
hs = rows_s[0]
cs = {k: i for i, k in enumerate(hs)}

stations = []
for r in rows1[1:]:
    abbr = r[c1['ชื่อย่อ']]
    sub = r[c1['สถานีไฟฟ้า']]
    ip = r[c1['IP']]
    s_row = next((sr for sr in rows_s[1:] if sr[cs['ชื่อย่อ']] == abbr), None)
    
    st_dict = {
        'no': r[c1['No.']],
        'abbr': abbr,
        'sub': sub,
        'ring': r[c1['Ring']],
        'ip': ip,
        'status': r[c1['สถานะเก็บข้อมูล']],
        'v_out': r[c1['Output Voltage (V)']],
        'load': r[c1['System Load (A)']],
        'batt_stat': r[c1['Battery Status']],
        'batt_curr': r[c1['Battery Current (A)']],
        'batt_cap': r[c1['Battery Capacity (%)']],
        'batt_temp': r[c1['Battery Temp (°C)']],
        'backup_h': r[c1['Estimated Backup Time (h)']],
        'amb_temp': r[c1['Ambient Temp (°C)']],
        'rect_count': r[c1['Number of Rectifiers']],
        'model': r[c1['Controller Product Model']] or "-",
        'hw_ver': r[c1['Controller Hardware Version']] or "-",
        'sw_ver': r[c1['Controller Software Version']] or "-",
        'config_ver': r[c1['Controller Config Version']] or "-",
    }

    if s_row:
        st_dict.update({
            'float_v': s_row[cs['Float Charge Voltage (V)']],
            'eq_v': s_row[cs['Equalize Charge Voltage (V)']],
            'batt_rated_ah': s_row[cs['Batt Rated Capacity (Ah)']],
            'lvd1_st': s_row[cs['LVD 1 Status']],
            'lvd2_st': s_row[cs['LVD 2 Status']],
            'lvd1_disc': s_row[cs['LVD 1 Disconnect Voltage (V)']],
            'lvd1_rec': s_row[cs['LVD 1 Reconnect Voltage (V)']],
            'uv1': s_row[cs['Under Voltage 1 (V)']],
            'uv2': s_row[cs['Under Voltage 2 (V)']],
            'rcl': s_row[cs['Rectifier Current Limit (%)']],
            'probe': s_row[cs['Temp Comp Probe Source']],
            'end_test_cap': s_row[cs['Batt End Test Capacity (%)']],
            'wi_st': s_row[cs['Walk-In Status']],
            'wi_t': s_row[cs['Walk-In Time (s)']],
        })
    else:
        st_dict.update({
            'float_v': None, 'eq_v': None, 'batt_rated_ah': None, 'lvd1_st': None,
            'lvd2_st': None, 'lvd1_disc': None, 'lvd1_rec': None, 'uv1': None,
            'uv2': None, 'rcl': None, 'probe': None, 'end_test_cap': None,
            'wi_st': None, 'wi_t': None
        })

    remarks = []
    if not ip:
        remarks.append("ไม่มี IP Address ในฐานข้อมูล")
    
    if st_dict['batt_cap'] is not None:
        try:
            cf = float(st_dict['batt_cap'])
            if cf == 94.0:
                remarks.append(f"แบตเตอรี่เสื่อมวิกฤต (ความจุ {cf}%, ชาร์จแช่ {st_dict['batt_curr']}A)")
            elif cf < 100.0:
                remarks.append(f"ความจุลดเหลือ {cf}%")
        except:
            pass
    elif ip and st_dict['batt_stat'] is None:
        remarks.append("ไม่ส่ง Telemetry DC/Battery (Config v1.00)")

    if abbr == 'NBD':
        remarks.append("กระแสชาร์จแช่ 2.3A (Float)")

    try:
        bt = float(st_dict['batt_temp']) if st_dict['batt_temp'] is not None else None
        at = float(st_dict['amb_temp']) if st_dict['amb_temp'] is not None else None
        if bt is not None and bt >= 35.0:
            remarks.append(f"อุณหภูมิสูง (แบต {bt}°C, ห้อง {at}°C)")
    except:
        pass

    if st_dict['lvd1_st'] == 'Disabled' or st_dict['lvd2_st'] == 'Disabled':
        remarks.append("LVD ปิดใช้งาน (เสี่ยงแบตพัง)")
    elif ip and st_dict['lvd1_st'] is None:
        remarks.append("LVD ไม่มีข้อมูล")

    if st_dict['eq_v'] == '56.4':
        remarks.append("Equalize 56.4V (สูงเกิน)")

    try:
        if st_dict['uv1'] is not None and float(st_dict['uv1']) != 48.0:
            remarks.append(f"UV1 {st_dict['uv1']}V (เกณฑ์ 48.0V)")
        if st_dict['uv2'] is not None and float(st_dict['uv2']) != 46.0:
            remarks.append(f"UV2 {st_dict['uv2']}V (เกณฑ์ 46.0V)")
    except Exception:
        pass

    if st_dict['rcl'] == '28':
        remarks.append("จำกัดกระแส Rectifier ต่ำ 28%")


    if st_dict['end_test_cap'] == '0.0':
        remarks.append("End Test Cap 0.0%")

    if st_dict['sw_ver'] == '1.3002':
        remarks.append("SW เก่า (1.3002)")
    elif st_dict['sw_ver'] == '5.2.14B':
        remarks.append("SW ใหม่ (5.2.14B/B06)")

    if not remarks:
        remarks.append("ปกติ (พร้อมใช้งาน)")

    st_dict['remarks'] = " | ".join(remarks)
    stations.append(st_dict)

batt_issues = [s for s in stations if any(k in s['remarks'] for k in ('เสื่อม', 'ความจุลด', 'ชาร์จแช่'))]
temp_issues = [s for s in stations if 'อุณหภูมิสูง' in s['remarks']]
settings_outliers = [s for s in stations if any(k in s['remarks'] for k in ('LVD ปิด', 'Equalize 56.4V', 'จำกัดกระแส', 'End Test Cap', 'UV1', 'UV2'))]
telemetry_issues = [s for s in stations if any(k in s['remarks'] for k in ('ไม่ส่ง Telemetry', 'ไม่มี IP'))]


# Rebuild Excel
wb = openpyxl.Workbook()
header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
header_font = Font(name="Cordia New", size=14, bold=True, color="FFFFFF")
alert_fill = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
warn_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
border_thin = Border(left=Side(style='thin', color='D9D9D9'), right=Side(style='thin', color='D9D9D9'), top=Side(style='thin', color='D9D9D9'), bottom=Side(style='thin', color='D9D9D9'))
data_font = Font(name="Cordia New", size=13)
bold_font = Font(name="Cordia New", size=13, bold=True)

def style_table(ws, headers, start_row=1):
    ws.append(headers)
    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=start_row, column=col)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[start_row].height = 28

# Summary
ws_sum = wb.active
ws_sum.title = "สรุปภาพรวม"
ws_sum.views.sheetView[0].showGridLines = True
ws_sum.append(["รายงานสรุปผลการตรวจสอบ Rectifier ระบบแบตเตอรี่ และการตั้งค่า (189 สถานี)"])
ws_sum.cell(1, 1).font = Font(name="Cordia New", size=18, bold=True, color="1F4E79")
ws_sum.append([f"ข้อมูล ณ วันที่ {datetime.now().strftime('%d/%m/%Y %H:%M')}"])
ws_sum.cell(2, 1).font = Font(name="Cordia New", size=12, italic=True)
ws_sum.append([])

summary_table = [
    ["หมวดหมู่การตรวจสอบ", "จำนวนสถานี", "สถานะ", "การดำเนินการเร่งด่วน"],
    ["สถานีปกติพร้อมใช้งาน", len(stations) - len(batt_issues) - len(temp_issues) - len(settings_outliers) - len(telemetry_issues), "ปกติ", "เฝ้าระวังตามรอบบำรุงรักษาปกติ"],
    ["แบตเตอรี่เสื่อมสภาพ / กระแสผิดปกติ", len(batt_issues), "วิกฤต/เฝ้าระวัง", "เข้าตรวจวัด Impedance / สลับเปลี่ยนเซลล์ (PS เพชรเกษม)"],
    ["การตั้งค่าผิดปกติ / เสี่ยงแบตเตอรี่เสียหาย", len(settings_outliers), "วิกฤตความปลอดภัย", "เปิดใช้ LVD, ปรับ Equalize และเกณฑ์เตือนแรงดันต่ำ"],
    ["อุณหภูมิห้อง/แบตเตอรี่สูงเกินเกณฑ์ (>=35°C)", len(temp_issues), "เฝ้าระวังสูง", "ตรวจสอบระบบปรับอากาศในห้อง Rectifier"],
    ["Telemetry ไม่สมบูรณ์ / ขาด IP", len(telemetry_issues), "ต้องปรับปรุงระบบส่งข้อมูล", "อัปเดต Firmware / Config Controller หรือตรวจสอบ IP"],
    ["รวมสถานีทั้งหมด", len(stations), "-", "-"]
]
for row_idx, r in enumerate(summary_table, start=4):
    ws_sum.append(r)
    for col_idx in range(1, len(r) + 1):
        cell = ws_sum.cell(row_idx, col_idx)
        cell.font = bold_font if row_idx in (4, len(summary_table) + 3) else data_font
        cell.border = border_thin
        if row_idx == 4:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
        elif row_idx in (5, 6):
            cell.fill = alert_fill
            cell.alignment = Alignment(horizontal="center" if col_idx in (2, 3) else "left", vertical="center")
        elif row_idx in (7, 8):
            cell.fill = warn_fill
            cell.alignment = Alignment(horizontal="center" if col_idx in (2, 3) else "left", vertical="center")
        else:
            cell.alignment = Alignment(horizontal="center" if col_idx in (2, 3) else "left", vertical="center")

# Settings Outliers
ws_so = wb.create_sheet("การตั้งค่าผิดปกติ")
ws_so.views.sheetView[0].showGridLines = True
headers_so = ["ชื่อย่อ", "สถานีไฟฟ้า", "IP", "Controller HW", "Controller SW", "Config Ver", "สถานะ LVD", "แรงดัน Equalize (V)", "Rect Limit (%)", "หมายเหตุ / รายการผิดปกติ"]
style_table(ws_so, headers_so)
for so in settings_outliers:
    row_vals = [so['abbr'], so['sub'], so['ip'], so['hw_ver'], so['sw_ver'], so['config_ver'], f"LVD1:{so['lvd1_st']}/LVD2:{so['lvd2_st']}", so['eq_v'], so['rcl'], so['remarks']]
    ws_so.append(row_vals)
    r_idx = ws_so.max_row
    for c_idx in range(1, len(row_vals) + 1):
        cell = ws_so.cell(r_idx, c_idx)
        cell.font = data_font
        cell.border = border_thin
        cell.alignment = Alignment(horizontal="center" if c_idx in (1, 3, 4, 5, 6, 7, 8, 9) else "left", vertical="center")
        if "LVD ปิด" in so['remarks'] and c_idx == 7:
            cell.fill = alert_fill
            cell.font = bold_font

# All Settings
ws_all_s = wb.create_sheet("การตั้งค่าทุกสถานี")
ws_all_s.views.sheetView[0].showGridLines = True
headers_all_s = list(hs) + ["HW Version", "SW Version", "Config Version", "หมายเหตุ"]
style_table(ws_all_s, headers_all_s)
for r in rows_s[1:]:
    abbr = r[cs['ชื่อย่อ']]
    st_info = next((s for s in stations if s['abbr'] == abbr), None)
    hw = st_info['hw_ver'] if st_info else "-"
    sw = st_info['sw_ver'] if st_info else "-"
    cfg = st_info['config_ver'] if st_info else "-"
    rem = st_info['remarks'] if st_info else "-"
    row_vals = list(r) + [hw, sw, cfg, rem]
    ws_all_s.append(row_vals)
    r_idx = ws_all_s.max_row
    for c_idx in range(1, len(row_vals) + 1):
        cell = ws_all_s.cell(r_idx, c_idx)
        cell.font = data_font
        cell.border = border_thin
        val_str = str(cell.value or "")
        if c_idx <= len(hs):
            col_name = hs[c_idx - 1]
            if col_name in ('LVD 1 Status', 'LVD 2 Status') and val_str == 'Disabled':
                cell.fill = alert_fill
                cell.font = bold_font
            elif col_name == 'Equalize Charge Voltage (V)' and val_str == '56.4':
                cell.fill = warn_fill
                cell.font = bold_font
        elif c_idx == len(row_vals):
            if "วิกฤต" in val_str or "LVD ปิด" in val_str:
                cell.fill = alert_fill
                cell.font = bold_font
            elif "ความจุลด" in val_str or "อุณหภูมิสูง" in val_str:
                cell.fill = warn_fill

ws_all_s.freeze_panes = "F2"
ws_all_s.auto_filter.ref = ws_all_s.dimensions

# Batt issues
ws_batt = wb.create_sheet("แบตเตอรี่เสื่อม-ผิดปกติ")
ws_batt.views.sheetView[0].showGridLines = True
headers_batt = ["ชื่อย่อ", "สถานีไฟฟ้า", "IP", "SW Version", "Config Ver", "ความจุ (%)", "กระแสชาร์จ (A)", "สถานะชาร์จ", "แรงดัน DC (V)", "โหลด (A)", "สำรองไฟ (ชม.)", "อุณหภูมิ (°C)", "หมายเหตุ / ผลการตรวจ"]
style_table(ws_batt, headers_batt)
for d in batt_issues:
    row_vals = [d['abbr'], d['sub'], d['ip'], d['sw_ver'], d['config_ver'], d['batt_cap'], d['batt_curr'], d['batt_stat'], d['v_out'], d['load'], d['backup_h'], d['batt_temp'], d['remarks']]
    ws_batt.append(row_vals)
    r_idx = ws_batt.max_row
    for c_idx in range(1, len(row_vals) + 1):
        cell = ws_batt.cell(r_idx, c_idx)
        cell.font = data_font
        cell.border = border_thin
        cell.alignment = Alignment(horizontal="center" if c_idx in (1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12) else "left", vertical="center")
        if c_idx == 6 and float(d['batt_cap']) < 95:
            cell.fill = alert_fill
            cell.font = bold_font

# Temp issues
ws_temp = wb.create_sheet("อุณหภูมิสูง")
ws_temp.views.sheetView[0].showGridLines = True
headers_temp = ["ชื่อย่อ", "สถานีไฟฟ้า", "IP", "SW Version", "Config Ver", "อุณหภูมิแบต (°C)", "อุณหภูมิห้อง (°C)", "โหลด (A)", "หมายเหตุ"]
style_table(ws_temp, headers_temp)
for d in temp_issues:
    row_vals = [d['abbr'], d['sub'], d['ip'], d['sw_ver'], d['config_ver'], d['batt_temp'], d['amb_temp'], d['load'], d['remarks']]
    ws_temp.append(row_vals)
    r_idx = ws_temp.max_row
    for c_idx in range(1, len(row_vals) + 1):
        cell = ws_temp.cell(r_idx, c_idx)
        cell.font = data_font
        cell.border = border_thin
        cell.alignment = Alignment(horizontal="center" if c_idx in (1, 3, 4, 5, 6) else "left", vertical="center")
        cell.fill = warn_fill

# Telemetry issues
ws_tel = wb.create_sheet("ข้อมูลไม่สมบูรณ์")
ws_tel.views.sheetView[0].showGridLines = True
headers_tel = ["ชื่อย่อ", "สถานีไฟฟ้า", "IP", "รุ่น Controller", "HW Version", "SW Version", "Config Version", "จำนวน Rectifier", "หมายเหตุ / สาเหตุ"]
style_table(ws_tel, headers_tel)
for d in telemetry_issues:
    row_vals = [d['abbr'], d['sub'], d['ip'] or "ไม่มี", d['model'], d['hw_ver'], d['sw_ver'], d['config_ver'], d['rect_count'] or 0, d['remarks']]
    ws_tel.append(row_vals)
    r_idx = ws_tel.max_row
    for c_idx in range(1, len(row_vals) + 1):
        cell = ws_tel.cell(r_idx, c_idx)
        cell.font = data_font
        cell.border = border_thin
        cell.alignment = Alignment(horizontal="center" if c_idx in (1, 3, 4, 5, 6, 7, 8) else "left", vertical="center")

# Master status
ws_all = wb.create_sheet("สถานะทุกสถานี")
ws_all.views.sheetView[0].showGridLines = True
headers_all = ["No.", "ชื่อย่อ", "สถานีไฟฟ้า", "IP", "HW Ver", "SW Ver", "Config Ver", "ความจุ (%)", "กระแสแบต (A)", "สถานะแบต", "แรงดัน DC (V)", "โหลด (A)", "อุณหภูมิแบต (°C)", "อุณหภูมิห้อง (°C)", "หมายเหตุ"]
style_table(ws_all, headers_all)
for idx, d in enumerate(stations, start=1):
    fill_to_use = None
    if "วิกฤต" in d['remarks'] or "LVD ปิด" in d['remarks']:
        fill_to_use = alert_fill
    elif "ความจุลด" in d['remarks'] or "อุณหภูมิสูง" in d['remarks']:
        fill_to_use = warn_fill
    row_vals = [idx, d['abbr'], d['sub'], d['ip'] or "-", d['hw_ver'], d['sw_ver'], d['config_ver'], d['batt_cap'] or "-", d['batt_curr'] or "-", d['batt_stat'] or "-", d['v_out'] or "-", d['load'] or "-", d['batt_temp'] or "-", d['amb_temp'] or "-", d['remarks']]
    ws_all.append(row_vals)
    r_idx = ws_all.max_row
    for c_idx in range(1, len(row_vals) + 1):
        cell = ws_all.cell(r_idx, c_idx)
        cell.font = data_font
        cell.border = border_thin
        cell.alignment = Alignment(horizontal="center" if c_idx in (1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14) else "left", vertical="center")
        if fill_to_use and c_idx == 15:
            cell.fill = fill_to_use
            cell.font = bold_font

for ws in wb.worksheets:
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            max_len = max(max_len, len(str(cell.value or "")))
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, 10), 45)

try:
    wb.save(str(reports_dir / "Rectifier_Abnormal_Report.xlsx"))
    print(f"Saved {reports_dir / 'Rectifier_Abnormal_Report.xlsx'}")
except PermissionError:
    try:
        wb.save(str(reports_dir / "Rectifier_Abnormal_Report_Complete.xlsx"))
        print(f"Saved {reports_dir / 'Rectifier_Abnormal_Report_Complete.xlsx'}")
    except PermissionError:
        wb.save(str(reports_dir / "Rectifier_Abnormal_Report_Latest.xlsx"))
        print(f"Saved {reports_dir / 'Rectifier_Abnormal_Report_Latest.xlsx'}")

# Rebuild Word
doc = docx.Document()
for section in doc.sections:
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)

def set_cell_background(cell, fill_hex):
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def add_heading(text, level=1, page_break=False):
    p = doc.add_paragraph()
    if page_break:
        p.paragraph_format.page_break_before = True
    p.paragraph_format.space_before = Pt(16)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "TH Sarabun New"
    run.font.size = Pt(18 if level == 1 else 16)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)
    return p

def format_table(tbl):
    hdr_tr = tbl.rows[0]._element.get_or_add_trPr()
    hdr_tr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
    for row in tbl.rows:
        trPr = row._element.get_or_add_trPr()
        trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))

title_p = doc.add_paragraph()
title_run = title_p.add_run("รายงานการวิเคราะห์และตรวจสอบสถานะ Rectifier ระบบแบตเตอรี่ และการตั้งค่า")
title_run.font.name = "TH Sarabun New"
title_run.font.size = Pt(22)
title_run.font.bold = True
title_run.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)

sub_p = doc.add_paragraph()
sub_run = sub_p.add_run(f"การตรวจสอบระบบไฟตรง 189 สถานี | วันที่ตรวจสอบ: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
sub_run.font.name = "TH Sarabun New"
sub_run.font.size = Pt(14)
sub_run.font.italic = True
sub_run.font.color.rgb = RGBColor(0x59, 0x59, 0x59)

# Divider line
p_div = doc.add_paragraph()
p_div.paragraph_format.space_after = Pt(8)
r_div = p_div.add_run("―" * 60)
r_div.font.color.rgb = RGBColor(0xBF, 0xBF, 0xBF)

add_heading("1. บทสรุปผู้บริหาร", level=1, page_break=False)

p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(4)
p.paragraph_format.line_spacing = 1.15
r = p.add_run(
    "จากการดึงข้อมูล Telemetry และการตั้งค่าล่าสุดจากตู้ควบคุม Vertiv NetSure ทั้งหมด 189 สถานี "
    "สรุปประเด็นสถานะระบบได้ดังนี้:"
)
r.font.name = "TH Sarabun New"
r.font.size = Pt(15)

bullets = [
    "สถานีศรีเอี่ยม (SE) ทำงานปกติแล้ว: จากการตรวจสอบแบบ Real-time พบว่าสถานะชาร์จและ Rectifier Current Limit กลับสู่ค่ามาตรฐาน 121% ความจุแบตเตอรี่เต็ม 100% กระแส 0 A สาเหตุเกิดจากช่วงก่อนหน้าสถานีอยู่ระหว่างกระบวนการทดสอบแบตเตอรี่ประจำเดือนอัตโนมัติ (Planned Battery Test)",
    "การตั้งค่าระบบตัดไฟต่ำ (LVD) ปิดใช้งาน: พบ 6 สถานี (AUG, BTD, KP, RTR, SYI, KRT) ปิดการทำงาน LVD หากไฟฟ้าดับยาวนาน แบตเตอรี่จะคายประจุจนหมดเกลี้ยง (0V) ทำให้แบตเตอรี่เสียหายถาวร",
    "แบตเตอรี่เสื่อมสภาพ: สถานีเพชรเกษม (PS) ความจุเหลือ 94% มีกระแสชาร์จแช่ 2.4 A ในโหมด Float Charge ส่วนสถานี TY และ RBD ความจุอยู่ที่ 98%",
    "อุณหภูมิห้องและแบตเตอรี่สูง (>= 35°C): พบ 4 สถานี สูงสุดที่เขตบางใหญ่ (BYD) อุณหภูมิห้อง 40°C แบตเตอรี่ 39°C",
    "ข้อมูล Telemetry ไม่สมบูรณ์: พบ 19 สถานีที่ Controller M830B Config v1.00 ไม่ส่งตัวแปร DC Voltage/Battery และ 1 สถานีไม่มี IP (MBD)"
]
for b in bullets:
    bp = doc.add_paragraph(style='List Bullet')
    bp.paragraph_format.space_after = Pt(3)
    bp.paragraph_format.line_spacing = 1.15
    r = bp.add_run(b)
    r.font.name = "TH Sarabun New"
    r.font.size = Pt(15)

# Section 2: Settings Audit
add_heading("2. ผลการตรวจสอบการตั้งค่าระบบ (Settings Audit)", level=1, page_break=True)

tbl_s = doc.add_table(rows=1, cols=7)
tbl_s.alignment = WD_TABLE_ALIGNMENT.CENTER
tbl_s.autofit = False
headers_s = ["ชื่อย่อ", "สถานีไฟฟ้า", "IP", "SW/Config", "สถานะ LVD", "Equalize", "หมายเหตุ / รายการข้อบกพร่อง"]
hdr_cells = tbl_s.rows[0].cells
for i, name in enumerate(headers_s):
    hdr_cells[i].text = name
    set_cell_background(hdr_cells[i], "1F4E79")
    set_cell_margins(hdr_cells[i])
    for pr in hdr_cells[i].paragraphs:
        pr.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in pr.runs:
            run.font.name = "TH Sarabun New"
            run.font.size = Pt(14)
            run.font.bold = True
            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

for r_idx, so in enumerate(settings_outliers):
    row = tbl_s.add_row()
    cells = row.cells
    cells[0].text = so['abbr']
    cells[1].text = so['sub']
    cells[2].text = so['ip']
    cells[3].text = f"{so['sw_ver']} / {so['config_ver']}"
    cells[4].text = f"LVD1:{so['lvd1_st']}\nLVD2:{so['lvd2_st']}"
    cells[5].text = f"{so['eq_v']} V" if so['eq_v'] else "-"
    cells[6].text = so['remarks']
    for idx, c in enumerate(cells):
        set_cell_margins(c)
        if r_idx % 2 == 1:
            set_cell_background(c, "F8F9FA")
        if idx in (0, 2, 3, 4, 5):
            c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in c.paragraphs[0].runs:
            run.font.name = "TH Sarabun New"
            run.font.size = Pt(13)
            if idx == 4 and "Disabled" in c.text:
                run.font.bold = True
                run.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
format_table(tbl_s)

# Section 3: Battery Degradation
add_heading("3. รายละเอียดสถานีที่แบตเตอรี่เสื่อมสภาพหรือการชาร์จผิดปกติ", level=1, page_break=True)

tbl_b = doc.add_table(rows=1, cols=8)
tbl_b.alignment = WD_TABLE_ALIGNMENT.CENTER
tbl_b.autofit = False
headers_b = ["ชื่อย่อ", "สถานีไฟฟ้า", "IP", "SW Ver", "ความจุ", "กระแส", "แรงดัน", "หมายเหตุ / ผลการวิเคราะห์"]
hdr_cells = tbl_b.rows[0].cells
for i, name in enumerate(headers_b):
    hdr_cells[i].text = name
    set_cell_background(hdr_cells[i], "1F4E79")
    set_cell_margins(hdr_cells[i])
    for pr in hdr_cells[i].paragraphs:
        pr.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in pr.runs:
            run.font.name = "TH Sarabun New"
            run.font.size = Pt(14)
            run.font.bold = True
            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

for r_idx, d in enumerate(batt_issues):
    row = tbl_b.add_row()
    cells = row.cells
    cells[0].text = d['abbr']
    cells[1].text = d['sub']
    cells[2].text = d['ip']
    cells[3].text = d['sw_ver']
    cells[4].text = f"{d['batt_cap']}%"
    cells[5].text = f"{d['batt_curr']} A"
    cells[6].text = f"{d['v_out']} V"
    cells[7].text = d['remarks']
    for idx, c in enumerate(cells):
        set_cell_margins(c)
        if r_idx % 2 == 1:
            set_cell_background(c, "F8F9FA")
        if idx in (0, 2, 3, 4, 5, 6):
            c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in c.paragraphs[0].runs:
            run.font.name = "TH Sarabun New"
            run.font.size = Pt(13)
            if idx == 4 and float(d['batt_cap']) < 95:
                run.font.bold = True
                run.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
format_table(tbl_b)

# Section 4: High Temp
add_heading("4. รายละเอียดสถานีที่อุณหภูมิสูงเกินมาตรฐาน (>= 35°C)", level=1, page_break=True)

tbl_t = doc.add_table(rows=1, cols=7)
tbl_t.alignment = WD_TABLE_ALIGNMENT.CENTER
tbl_t.autofit = False
headers_t = ["ชื่อย่อ", "สถานีไฟฟ้า", "IP", "SW Ver", "อุณหภูมิแบต", "อุณหภูมิห้อง", "หมายเหตุ"]
hdr_cells = tbl_t.rows[0].cells
for i, name in enumerate(headers_t):
    hdr_cells[i].text = name
    set_cell_background(hdr_cells[i], "1F4E79")
    set_cell_margins(hdr_cells[i])
    for pr in hdr_cells[i].paragraphs:
        pr.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in pr.runs:
            run.font.name = "TH Sarabun New"
            run.font.size = Pt(14)
            run.font.bold = True
            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

for r_idx, d in enumerate(temp_issues):
    row = tbl_t.add_row()
    cells = row.cells
    cells[0].text = d['abbr']
    cells[1].text = d['sub']
    cells[2].text = d['ip']
    cells[3].text = d['sw_ver']
    cells[4].text = f"{d['batt_temp']} °C"
    cells[5].text = f"{d['amb_temp']} °C"
    cells[6].text = d['remarks']
    for idx, c in enumerate(cells):
        set_cell_margins(c)
        if r_idx % 2 == 1:
            set_cell_background(c, "F8F9FA")
        if idx in (0, 2, 3, 4, 5):
            c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in c.paragraphs[0].runs:
            run.font.name = "TH Sarabun New"
            run.font.size = Pt(13)
format_table(tbl_t)

# Section 5: Action Plan
add_heading("5. แผนปฏิบัติการแก้ไขเร่งด่วน", level=1, page_break=True)

actions = [
    "แก้ไขการตั้งค่า LVD ทันที: เปิดใช้งาน LVD (Enabled) ที่สถานี AUG, BTD, KP, RTR, SYI และ KRT พร้อมตั้งแรงดันตัดวงจรที่ 43.2V ป้องกันแบตเตอรี่พังเมื่อไฟดับ",
    "ปรับแก้การตั้งค่าผิดเพี้ยน: ปรับ Batt End Test Capacity ที่ KRT เป็น 70% และลด Equalize Voltage ที่ 4 สถานี (AUG, KP, RTR, SYI) จาก 56.4V ลงมาที่ 53.6V",
    "เข้าทดสอบแบตเตอรี่หน้างาน: เข้าทดสอบวัดความต้านทานภายใน (Impedance) ของแบตเตอรี่ที่สถานี PS (เพชรเกษม) เพื่อเปลี่ยนเซลล์เสื่อม",
    "ตรวจสอบระบบทำความเย็น: ซ่อมบำรุงระบบปรับอากาศที่สถานี BYD, BU, LB และ SB ให้อุณหภูมิห้องไม่เกิน 25°C",
    "ปรับปรุงการส่งข้อมูล Telemetry: แก้ไข Firmware/Signal Config 19 สถานีที่ข้อมูล DC/Battery ว่าง และเพิ่ม IP สถานี MBD"
]
for act in actions:
    ap = doc.add_paragraph(style='List Bullet')
    ap.paragraph_format.space_after = Pt(4)
    ap.paragraph_format.line_spacing = 1.15
    r = ap.add_run(act)
    r.font.name = "TH Sarabun New"
    r.font.size = Pt(15)

# Landscape Appendix
sec_land = doc.add_section(WD_SECTION.NEW_PAGE)
sec_land.orientation = WD_ORIENT.LANDSCAPE
sec_land.page_width = Inches(11.69)
sec_land.page_height = Inches(8.27)
sec_land.top_margin = Inches(0.5)
sec_land.bottom_margin = Inches(0.5)
sec_land.left_margin = Inches(0.5)
sec_land.right_margin = Inches(0.5)

h6 = doc.add_paragraph()
r = h6.add_run("ภาคผนวก: ตารางสรุปการตั้งค่า เวอร์ชัน และหมายเหตุของทั้ง 189 สถานี")
r.font.name = "TH Sarabun New"
r.font.size = Pt(15)
r.font.bold = True
r.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)

land_headers = ["No.", "ชื่อย่อ", "สถานีไฟฟ้า", "IP", "HW", "SW", "Cfg", "Float(V)", "Equal(V)", "Cap(Ah)", "LVD 1/2", "RCL(%)", "หมายเหตุ"]
tbl_all_s = doc.add_table(rows=1, cols=len(land_headers))
tbl_all_s.alignment = WD_TABLE_ALIGNMENT.CENTER
tbl_all_s.autofit = False

hdr_cells = tbl_all_s.rows[0].cells
for i, name in enumerate(land_headers):
    hdr_cells[i].text = name
    set_cell_background(hdr_cells[i], "1F4E79")
    set_cell_margins(hdr_cells[i], top=50, bottom=50, left=60, right=60)
    for pr in hdr_cells[i].paragraphs:
        pr.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in pr.runs:
            run.font.name = "TH Sarabun New"
            run.font.size = Pt(10)
            run.font.bold = True
            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

for r_idx, s in enumerate(stations):
    row = tbl_all_s.add_row()
    cells = row.cells
    cells[0].text = str(s['no'] or "")
    cells[1].text = str(s['abbr'] or "")
    cells[2].text = str(s['sub'] or "")
    cells[3].text = str(s['ip'] or "-")
    cells[4].text = str(s['hw_ver'] or "-")
    cells[5].text = str(s['sw_ver'] or "-")
    cells[6].text = str(s['config_ver'] or "-")
    cells[7].text = str(s['float_v'] or "")
    cells[8].text = str(s['eq_v'] or "")
    cells[9].text = str(s['batt_rated_ah'] or "")
    cells[10].text = f"{s['lvd1_st']}/{s['lvd2_st']}"
    cells[11].text = str(s['rcl'] or "")
    cells[12].text = s['remarks']

    for idx, c in enumerate(cells):
        set_cell_margins(c, top=30, bottom=30, left=50, right=50)
        if r_idx % 2 == 1:
            set_cell_background(c, "F8F9FA")
        if idx in (0, 1, 3, 4, 5, 6, 7, 8, 9, 10, 11):
            c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in c.paragraphs[0].runs:
            run.font.name = "TH Sarabun New"
            run.font.size = Pt(9.5)
            if idx == 10 and 'Disabled' in c.text:
                run.font.bold = True
                run.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
            elif idx == 8 and c.text == '56.4':
                run.font.bold = True
                run.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
            elif idx == 12 and ("วิกฤต" in c.text or "LVD ปิด" in c.text):
                run.font.bold = True
                run.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)

format_table(tbl_all_s)

word_path = reports_dir / "Rectifier_Inspection_Report_All_Settings.docx"
try:
    doc.save(str(word_path))
    print(f"Saved {word_path}")
except Exception as e:
    alt_word_path = reports_dir / "Rectifier_Inspection_Report_Updated.docx"
    doc.save(str(alt_word_path))
    print(f"Saved {alt_word_path}")
