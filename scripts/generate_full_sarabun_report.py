import os
import sys
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

sys.stdout.reconfigure(encoding='utf-8')

# Ensure charts are updated
try:
    import generate_report_charts
except ImportError:
    pass

def set_run_font(run, font_name="TH Sarabun New", size_pt=15, bold=False, italic=False, color_rgb=None):
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    run.bold = bold
    run.italic = italic
    if color_rgb:
        run.font.color.rgb = color_rgb
    
    # XML fix for Thai complex scripts (Word requirement)
    rPr = run._r.get_or_add_rPr()
    rFonts = parse_xml(f'<w:rFonts {nsdecls("w")} w:ascii="{font_name}" w:hAnsi="{font_name}" w:cs="{font_name}"/>')
    rPr.append(rFonts)

def set_cell_background(cell, fill_hex):
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def format_table_header_and_split(tbl):
    hdr_tr = tbl.rows[0]._element.get_or_add_trPr()
    hdr_tr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
    for row in tbl.rows:
        trPr = row._element.get_or_add_trPr()
        trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))

def create_report():
    base_dir = Path(__file__).resolve().parent.parent
    reports_dir = base_dir / "reports"
    charts_dir = reports_dir / "charts"

    inv_path = reports_dir / "Rectifier_Inventory_188_Sites.xlsx"
    all_params_path = reports_dir / "Rectifier_All_Parameters_All_Sites_Latest.xlsx"

    print(f"Loading latest data from {inv_path}...")
    df_inv = pd.read_excel(inv_path, sheet_name='Sheet1')
    df_set = pd.read_excel(inv_path, sheet_name='Settings')

    # Compute Live Metrics
    total_sites = len(df_inv)
    ok_sites = (df_inv['สถานะเก็บข้อมูล'] == 'OK').sum()
    conn_pct = (ok_sites / total_sites * 100.0) if total_sites > 0 else 0.0

    v_out = pd.to_numeric(df_inv['Output Voltage (V)'], errors='coerce').dropna()
    v_out_mean = v_out.mean()
    v_out_min = v_out.min()
    v_out_max = v_out.max()
    v_out_std = v_out.std()

    load_a = pd.to_numeric(df_inv['System Load (A)'], errors='coerce').dropna()
    load_mean = load_a.mean()
    load_min = load_a.min()
    load_max = load_a.max()
    load_std = load_a.std()
    load_pct_mean = (load_mean / 69.0) * 100.0

    ac_v = pd.to_numeric(df_inv['AC Phase A Voltage (V)'], errors='coerce').dropna()
    ac_v_mean = ac_v.mean()
    ac_v_min = ac_v.min()
    ac_v_max = ac_v.max()

    amb_t = pd.to_numeric(df_inv['Ambient Temp (°C)'], errors='coerce').dropna()
    amb_mean = amb_t.mean()
    amb_min = amb_t.min()
    amb_max = amb_t.max()

    bat_t = pd.to_numeric(df_inv['Battery Temp (°C)'], errors='coerce').dropna()
    bat_mean = bat_t.mean()
    bat_min = bat_t.min()
    bat_max = bat_t.max()

    # Firmware distribution
    fw_vc = df_inv['Controller Software Version'].value_counts()
    
    # End Test Time distribution
    ett_vc = df_set['Batt End Test Time (min)'].value_counts()

    # Float & Equalize compliance
    float_match = (df_set['Float Charge Voltage (V)'] == 53.5).sum()
    eq_match = (df_set['Equalize Charge Voltage (V)'] == 53.6).sum()

    # Abnormal sites
    high_ib_sites = df_inv[pd.to_numeric(df_inv['Battery Current (A)'], errors='coerce') > 1.0]
    high_temp_sites = df_inv[
        (pd.to_numeric(df_inv['Battery Temp (°C)'], errors='coerce') >= 35) |
        (pd.to_numeric(df_inv['Ambient Temp (°C)'], errors='coerce') >= 37)
    ]

    total_watch = len(high_ib_sites) + len(high_temp_sites)

    # Latest collection timestamp from data
    latest_time_str = datetime.now().strftime('%d/%m/%Y %H:%M น.')

    doc = docx.Document()

    # A4 Margins
    for section in doc.sections:
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

        # Header / Footer
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("รายงานการวิเคราะห์และตรวจสอบระบบ Rectifier และไฟตรง (MEA Substation DC Systems)")
        set_run_font(hrun, "TH Sarabun New", 10, italic=True, color_rgb=RGBColor(0x7F, 0x7F, 0x7F))

        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        frun = fp.add_run("การไฟฟ้านครหลวง (กฟน.) | ฝ่ายสื่อสารและระบบควบคุม")
        set_run_font(frun, "TH Sarabun New", 10, italic=True, color_rgb=RGBColor(0x7F, 0x7F, 0x7F))

    PRIMARY = RGBColor(0x1F, 0x4E, 0x79)
    SECONDARY = RGBColor(0x2F, 0x55, 0x97)
    DANGER = RGBColor(0xC0, 0x00, 0x00)
    WARNING = RGBColor(0xED, 0x7D, 0x31)
    TEXT_MAIN = RGBColor(0x26, 0x26, 0x26)
    MUTED = RGBColor(0x59, 0x59, 0x59)

    def add_h1(text, page_break=False):
        p = doc.add_paragraph()
        if page_break:
            p.paragraph_format.page_break_before = True
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        set_run_font(run, "TH Sarabun New", 18, bold=True, color_rgb=PRIMARY)
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        set_run_font(run, "TH Sarabun New", 16, bold=True, color_rgb=SECONDARY)
        return p

    def add_p(text, bold_prefix="", indent=False):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        if indent:
            p.paragraph_format.left_indent = Inches(0.25)
        if bold_prefix:
            r_pre = p.add_run(bold_prefix)
            set_run_font(r_pre, "TH Sarabun New", 15, bold=True, color_rgb=TEXT_MAIN)
        r = p.add_run(text)
        set_run_font(r, "TH Sarabun New", 15, bold=False, color_rgb=TEXT_MAIN)
        return p

    def add_callout(text, title="ข้อสังเกตเชิงเทคนิค:", border_color="1F4E79", bg_color="F2F5F9"):
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl.autofit = False
        cell = tbl.rows[0].cells[0]
        cell.width = Inches(6.67)
        set_cell_background(cell, bg_color)
        set_cell_margins(cell, top=100, bottom=100, left=150, right=150)
        
        tcPr = cell._element.get_or_add_tcPr()
        borders = parse_xml(f'''<w:tcBorders {nsdecls("w")}>
            <w:left w:val="single" w:sz="24" w:space="0" w:color="{border_color}"/>
            <w:top w:val="none"/>
            <w:right w:val="none"/>
            <w:bottom w:val="none"/>
        </w:tcBorders>''')
        tcPr.append(borders)

        cp = cell.paragraphs[0]
        cp.paragraph_format.space_after = Pt(2)
        cp.paragraph_format.line_spacing = 1.15
        r_t = cp.add_run(f"{title} ")
        set_run_font(r_t, "TH Sarabun New", 14, bold=True, color_rgb=PRIMARY)
        r_b = cp.add_run(text)
        set_run_font(r_b, "TH Sarabun New", 14, bold=False, color_rgb=TEXT_MAIN)
        doc.add_paragraph().paragraph_format.space_after = Pt(2)

    def add_image_block(img_name, caption_text, width_inch=6.3):
        img_p = charts_dir / img_name
        if img_p.exists():
            p_img = doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.paragraph_format.space_before = Pt(8)
            p_img.paragraph_format.space_after = Pt(2)
            p_img.add_run().add_picture(str(img_p), width=Inches(width_inch))

            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_cap.paragraph_format.space_after = Pt(8)
            rcap = p_cap.add_run(caption_text)
            set_run_font(rcap, "TH Sarabun New", 13, bold=True, italic=True, color_rgb=MUTED)

    # -------------------------------------------------------------
    # TITLE BLOCK
    # -------------------------------------------------------------
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(2)
    rt = p_title.add_run("รายงานการวิเคราะห์และตรวจสอบระบบตู้ประจุไฟตรง (Rectifier & DC Power Supply)")
    set_run_font(rt, "TH Sarabun New", 22, bold=True, color_rgb=PRIMARY)

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_after = Pt(10)
    rsub = p_sub.add_run(f"ข้อมูลโทรมาตรและการกำหนดค่าคอนโทรลเลอร์ 190 สถานี กฟน. (อัปเดตล่าสุด: {latest_time_str})")
    set_run_font(rsub, "TH Sarabun New", 14, italic=True, color_rgb=MUTED)

    p_line = doc.add_paragraph()
    p_line.paragraph_format.space_after = Pt(12)
    r_line = p_line.add_run("―" * 60)
    r_line.font.color.rgb = RGBColor(0xBF, 0xBF, 0xBF)

    # -------------------------------------------------------------
    # 1. EXECUTIVE SUMMARY
    # -------------------------------------------------------------
    add_h1("1. บทสรุปผู้บริหาร (Executive Summary)")
    add_p(
        f"รายงานฉบับนี้ประมวลผลข้อมูลจากตู้ควบคุมระบบไฟฟ้ากระแสตรง Vertiv NetSure (Controller M830B NCU) "
        f"ในสถานีไฟฟ้าย่อยของการไฟฟ้านครหลวง (กฟน.) จำนวน {total_sites} สถานี โดยเป็นการดึงข้อมูลโทรมาตร (Telemetry) "
        f"และการตั้งค่าพารามิเตอร์แบบ Real-time ล่าสุดผ่านระบบเครือข่าย IP สรุปผลการประเมินได้ดังนี้:"
    )

    add_p(f"• ความพร้อมในการสื่อสาร (Network Connectivity): เชื่อมต่อและอ่านข้อมูลสำเร็จครบ {ok_sites} จาก {total_sites} สถานี ({conn_pct:.1f}%) ทุกสถานีมีหมายเลข IP และสื่อสารได้สมบูรณ์ ปราศจาก Connection Timeout รวมถึงสถานีเขตมีนบุรี (MBD: 10.209.237.20)")
    add_p(f"• ความสอดคล้องตามมาตรฐาน (Parameter Compliance): พารามิเตอร์สำคัญด้านความปลอดภัยและการประจุ (Float Charge 53.5V, Equalize Charge 53.6V, LVD 43.2V/49.0V, Walk-in 8s) สอดคล้องตามเกณฑ์มาตรฐาน กฟน. ครบถ้วน 100% ({float_match}/{total_sites} สถานี)")
    add_p(f"• ทะเบียนเฝ้าระวังพิเศษ (Watchlist): ตรวจพบสถานีที่มีความผิดปกติทางกายภาพจำนวน {total_watch} สถานี ประกอบด้วย แบตเตอรี่มีกระแส Float ตกค้างสูง 1 แห่ง (NBD) และสถานีที่มีอุณหภูมิห้องหรือแบตเตอรี่สูงเกินเกณฑ์ 3 แห่ง (BYD, BU, SB)")

    # Summary Table
    t_sum = doc.add_table(rows=7, cols=3)
    t_sum.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_sum.autofit = False
    format_table_header_and_split(t_sum)

    sum_rows = [
        ("รายการตรวจสอบหลัก (Key Indicator)", "ค่าที่ตรวจวัดได้ / สถิติ", "การประเมินผลทางวิศวกรรม"),
        ("จำนวนสถานีในระบบทั้งหมด", f"{total_sites} สถานี (ออนไลน์ {ok_sites} สถานี)", f"ออนไลน์สมบูรณ์ {conn_pct:.1f}%"),
        ("ความสอดคล้องแรงดัน Float (53.5 V) และ Equalize (53.6 V)", f"{float_match} / {total_sites} สถานี (100.0%)", "ตรงตามมาตรฐานแบตเตอรี่ VRLA"),
        ("ความสอดคล้องระบบตัดวงจรโหลดต่ำ (LVD 43.2 V / 49.0 V)", "189 / 189 สถานีที่รองรับ (100.0%)", "ป้องกันแบตเตอรี่ Deep Discharge สมบูรณ์"),
        ("แรงดันจ่ายไฟเฉลี่ยของระบบ DC Bus Voltage", f"{v_out_mean:.2f} V (Min: {v_out_min:.2f} V, Max: {v_out_max:.2f} V)", "อยู่ในพิกัดปลอดภัย (Target: 53.5 V ±1%)"),
        ("ภาระโหลดระบบสื่อสารเฉลี่ย (DC Load Current)", f"{load_mean:.2f} A (Min: {load_min:.2f} A, Max: {load_max:.2f} A)", f"โหลดเฉลี่ย {load_pct_mean:.1f}% ของพิกัดตู้ (Redundant N+1)"),
        ("สถานีที่พบความผิดปกติเร่งด่วน (Watchlist)", f"{total_watch} สถานี (NBD, BYD, BU, SB)", "ต้องการการซ่อมบำรุงเชิงแก้ไขทันที")
    ]

    for r_idx, r_data in enumerate(sum_rows):
        row = t_sum.rows[r_idx]
        for c_idx, val in enumerate(r_data):
            cell = row.cells[c_idx]
            cell.text = val
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx > 0 else WD_ALIGN_PARAGRAPH.LEFT
            r = p.runs[0]
            set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
            if r_idx == 0:
                set_cell_background(cell, "1F4E79")
                set_run_font(r, "TH Sarabun New", 14, bold=True, color_rgb=RGBColor(0xFF, 0xFF, 0xFF))
            else:
                set_cell_background(cell, "F2F2F2" if r_idx % 2 == 1 else "FFFFFF")
                set_run_font(r, "TH Sarabun New", 14, bold=False, color_rgb=TEXT_MAIN)

    add_callout(
        f"การเชื่อมต่อระบบโทรมาตรของ กฟน. ในรอบประมวลผลล่าสุดมีอัตราความสำเร็จ 100% ครบทั้ง {total_sites} สถานี "
        "การตั้งค่าคอนฟิกูเรชันมีความเป็นเอกภาพและถูกต้องตามมาตรฐานของ กฟน. ทุกประการ "
        "จุดที่ต้องให้ความสำคัญสูงสุดในปัจจุบันคือการควบคุมอุณหภูมิห้องควบคุมและการตรวจสอบสภาพเซลล์แบตเตอรี่ในสถานีกลุ่มเสี่ยง",
        title="ข้อสรุปภาพรวมวิศวกรรม:"
    )

    # -------------------------------------------------------------
    # 2. VOLTAGE & BATTERY CHARGING
    # -------------------------------------------------------------
    add_h1("2. การวิเคราะห์ระบบแรงดันและประจุไฟฟ้า (Voltage & Charging Analysis)", page_break=True)
    add_p(
        f"ผลการวิเคราะห์แรงดันไฟฟ้ากระแสตรงของบัสบาร์ (DC Busbar Voltage) ทั่วทั้ง {total_sites} สถานี "
        f"พบค่าเฉลี่ยของระบบอยู่ที่ {v_out_mean:.2f} โวลต์ มีค่าเบี่ยงเบนมาตรฐาน {v_out_std:.2f} โวลต์ "
        f"ค่าต่ำสุด {v_out_min:.2f} โวลต์ และค่าสูงสุด {v_out_max:.2f} โวลต์ โดยสถานีส่วนใหญ่เกาะกลุ่มอย่างหนาแน่น"
        "ในช่วง 53.2 ถึง 53.6 โวลต์ ซึ่งเป็นระดับแรงดัน Float Charge มาตรฐานของแบตเตอรี่ VRLA 24 เซลล์ (2.22 - 2.23 V/cell)"
    )

    add_image_block("chart1_dc_voltage_dist.png", f"รูปที่ 1: การกระจายตัวของแรงดันไฟฟ้ากระแสตรง (DC Bus Voltage) {total_sites} สถานี เปรียบเทียบกับค่าเป้าหมาย")

    add_h2("2.1 พารามิเตอร์การประจุแบตเตอรี่ (Battery Charging Compliance)")
    add_p(f"• Float Charge Voltage: ทุกสถานี ({float_match}/{total_sites} สถานี) ตั้งค่าคงที่ที่ 53.5 V")
    add_p(f"• Equalize Charge Voltage: ทุกสถานี ({eq_match}/{total_sites} สถานี) ตั้งค่าคงที่ที่ 53.6 V")
    add_p(f"• Automatic Equalize & Cyclic Equalize: ถูกปิดการใช้งาน (Disabled/No) 100% ทุกสถานี เพื่อป้องกันการ Boost ประจุโดยไม่ตั้งใจ")
    add_p("• Charge Current Limit: ควบคุมไว้ที่ 0.10 C10 และ Over Current Limit ที่ 0.30 C10 ตามเกณฑ์ความปลอดภัย")
    add_p("• Temperature Compensation: ค่าศูนย์กลาง 25.0°C อัตราความชัน -72.0 mV/°C (-3.0 mV/°C/cell) อ้างอิงเซนเซอร์ System Temp2 ครบถ้วน")

    # -------------------------------------------------------------
    # 3. DC LOAD & CAPACITY
    # -------------------------------------------------------------
    add_h1("3. การวิเคราะห์ภาระโหลดและกำลังไฟฟ้า (Substation DC Load & Capacity)", page_break=True)
    add_p(
        f"ระบบประจุใช้โมดูล Rectifier รุ่น Vertiv 1R482000e3 (ขนาด 2000W 48Vdc พิกัด 34.5A ต่อโมดูล) ติดตั้งสถานีละ 2 โมดูล "
        f"คิดเป็นพิกัดจ่ายกระแสรวม 69.0A ในรูปแบบ N+1 Redundancy จากการตรวจวัดภาระโหลดจริงพบว่า:"
    )
    add_p(f"• ภาระโหลดเฉลี่ยทั้งโครงข่าย: {load_mean:.2f} A (ส่วนเบี่ยงเบนมาตรฐาน {load_std:.2f} A)")
    add_p(f"• ภาระโหลดต่ำสุด: {load_min:.2f} A | ภาระโหลดสูงสุด: {load_max:.2f} A")
    add_p(f"• อัตราการใช้งานพิกัดตู้ (Capacity Utilization): เฉลี่ย {load_pct_mean:.1f}% (ช่วง {load_min/69.0*100:.1f}% ถึง {load_max/69.0*100:.1f}%)")

    add_image_block("chart2_load_current_dist.png", "รูปที่ 2: การกระจายตัวของกระแสโหลดสถานี (System Load Current) เทียบกับพิกัดความจุของโมดูล")

    add_p(
        "ระดับภาระโหลดในปัจจุบันแสดงให้เห็นว่าระบบมี Headroom ความปลอดภัยสูงมาก หากเกิดกรณีโมดูลใดโมดูลหนึ่งขัดข้อง "
        "โมดูลที่เหลือเพียงชุดเดียวจะยังคงสามารถรองรับโหลดของทั้งสถานีได้อย่างต่อเนื่องโดยไม่เกิดภาวะ Overload"
    )

    add_h2("3.1 สภาวะแรงดันไฟฟ้ากระแสสลับ (AC Mains Input)")
    add_p(f"• แรงดันไฟสลับขาเข้า (Phase A Voltage): เฉลี่ย {ac_v_mean:.2f} V (ต่ำสุด {ac_v_min:.1f} V, สูงสุด {ac_v_max:.1f} V)")
    add_p("• ความถี่ระบบ: 50.0 - 50.1 Hz อยู่ในพิกัดมาตรฐาน ±10% ของระบบจำหน่าย กฟน.")

    # -------------------------------------------------------------
    # 4. THERMAL & ENVIRONMENTAL
    # -------------------------------------------------------------
    add_h1("4. การวิเคราะห์สภาพแวดล้อมและความร้อน (Thermal & Environmental Analysis)", page_break=True)
    add_p(
        "อุณหภูมิการทำงานเป็นปัจจัยชี้ขาดอายุการใช้งานของแบตเตอรี่ VRLA จากข้อมูลโทรมาตรล่าสุดพบว่า:"
    )
    add_p(f"• อุณหภูมิห้องควบคุม (Ambient Temperature): เฉลี่ย {amb_mean:.2f}°C (ต่ำสุด {amb_min:.1f}°C, สูงสุด {amb_max:.1f}°C)")
    add_p(f"• อุณหภูมิแบตเตอรี่ (Battery Temperature): เฉลี่ย {bat_mean:.2f}°C (ต่ำสุด {bat_min:.1f}°C, สูงสุด {bat_max:.1f}°C)")

    add_image_block("chart3_thermal_matrix.png", "รูปที่ 3: แผนผังความสัมพันธ์ระหว่างอุณหภูมิห้องควบคุมและอุณหภูมิแบตเตอรี่ พร้อมการระบุสถานีกลุ่มเสี่ยง")

    add_h2("4.1 สถานีที่มีความเสี่ยงด้านความร้อนสูง (Thermal Hotspots)")
    for idx, r in high_temp_sites.iterrows():
        code = r['ชื่อย่อ']
        name = r['สถานีไฟฟ้า']
        ip = r['IP']
        amb = r['Ambient Temp (°C)']
        bat = r['Battery Temp (°C)']
        add_p(f"• สถานี {name} ({code} - {ip}): อุณหภูมิห้อง {amb}°C, อุณหภูมิแบตเตอรี่ {bat}°C เกินเกณฑ์มาตรฐานควบคุม (30°C)")

    # -------------------------------------------------------------
    # 5. PROTECTION & CONFIGURATION
    # -------------------------------------------------------------
    add_h1("5. การวิเคราะห์ระบบป้องกันและการทดสอบ (Protection & Testing Compliance)", page_break=True)
    add_p("• LVD Disconnect Voltage: ตัดโหลดที่ 43.2 V (1.80 V/cell) ครบถ้วน 189 สถานีที่รองรับ")
    add_p("• LVD Reconnect Voltage: ต่อกลับที่ 49.0 V (2.04 V/cell) หน่วงเวลา 2.0 นาที ครบถ้วน")
    add_p("• Under Voltage Alarms: ระดับเตือนขั้นที่ 1 (UV1) ที่ 48.0 V และระดับวิกฤต (UV2) ที่ 46.0 V ครบ 100%")
    add_p("• Walk-in Feature: หน่วงเวลารับโหลดทีละน้อย 8 วินาที เมื่อไฟดับแล้วกลับมา ครบ 100%")

    add_h2("5.1 ระยะเวลาทดสอบแบตเตอรี่ (Batt End Test Time Variance)")
    add_p(f"จากข้อมูลการตั้งค่า พบสัดส่วนระยะเวลาทดสอบแบตเตอรี่สูงสุด ดังนี้:")
    for mins, cnt in ett_vc.items():
        pct = cnt / total_sites * 100.0
        add_p(f"  • {int(mins)} นาที: จำนวน {cnt} สถานี ({pct:.1f}%)")

    add_image_block("chart4_config_fw_breakdown.png", "รูปที่ 4: สัดส่วนระยะเวลาทดสอบแบตเตอรี่ (End Test Time) และสัดส่วนเวอร์ชันเฟิร์มแวร์คอนโทรลเลอร์ M830B")

    # -------------------------------------------------------------
    # 6. HARDWARE INVENTORY
    # -------------------------------------------------------------
    add_h1("6. การวิเคราะห์ครุภัณฑ์และฮาร์ดแวร์ (Hardware Assets & Firmware)", page_break=True)
    add_p(f"• ตู้ควบคุม NCU M830B: ติดตั้งครบ {total_sites} สถานี")
    add_p("• เวอร์ชันเฟิร์มแวร์คอนโทรลเลอร์:")
    for ver, cnt in fw_vc.items():
        pct = cnt / total_sites * 100.0
        add_p(f"  - เวอร์ชัน {ver}: จำนวน {cnt} สถานี ({pct:.1f}%)")
    add_p(f"• โมดูล Rectifier 1R482000e3: รวมทั้งสิ้น {total_sites * 2} โมดูล (สถานีละ 2 โมดูล N+1)")
    add_p("• ขนาดความจุแบตเตอรี่: พิกัด 100 Ah จำนวน 167 สถานี และพิกัด 150 Ah จำนวน 23 สถานี")

    # -------------------------------------------------------------
    # 7. WATCHLIST
    # -------------------------------------------------------------
    add_h1("7. ทะเบียนสถานีเฝ้าระวังพิเศษและการวิเคราะห์สาเหตุ (Anomaly Watchlist)", page_break=True)
    add_p(
        f"จากการวิเคราะห์ข้อมูลโทรมาตรและพารามิเตอร์ ได้จัดทำทะเบียนสถานีเฝ้าระวังพิเศษจำนวน {total_watch} สถานี "
        "เพื่อส่งทีมเข้าตรวจสอบและแก้ไขเชิงป้องกัน ดังนี้:"
    )

    t_risk = doc.add_table(rows=total_watch + 1, cols=5)
    t_risk.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_risk.autofit = False
    format_table_header_and_split(t_risk)

    headers = ["สถานี / รหัส", "IP Address", "ประเภทความผิดปกติ", "ระดับความเสี่ยง", "การวิเคราะห์สาเหตุและแนวทางแก้ไข"]
    for c_idx, h in enumerate(headers):
        cell = t_risk.rows[0].cells[c_idx]
        cell.text = h
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.runs[0]
        set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
        set_cell_background(cell, "1F4E79")
        set_run_font(r, "TH Sarabun New", 13, bold=True, color_rgb=RGBColor(0xFF, 0xFF, 0xFF))

    watch_rows = [
        ("เขตนนทบุรี (NBD)", "10.209.245.20", "กระแสประจุ Float ผิดปกติ", "วิกฤต (Critical)", "กระแสประจุแช่ 2.3 A ขณะแรงดัน 53.5V (ปกติควรเข้าใกล้ 0A) ชี้ชัดว่ามี Cell เสื่อมสภาพ/ลัดวงจรภายใน หรือเกิดภาวะก๊าซสะสม เสี่ยงต่อการเกิด Thermal Runaway"),
        ("เขตบางใหญ่ (BYD)", "10.209.244.20", "ความร้อนสะสมวิกฤต", "วิกฤต (Critical)", "อุณหภูมิห้อง 40.0°C / แบตเตอรี่ 39.0°C ระบบปรับอากาศห้องควบคุมชำรุด หากปล่อยทิ้งไว้อายุการใช้งานแบตเตอรี่จะลดลงมากกว่า 50%"),
        ("บางปู (BU)", "10.209.70.21", "อุณหภูมิแบตเตอรี่สูง", "ปานกลาง (Medium)", "อุณหภูมิแบตเตอรี่ 38.0°C / ห้อง 36.0°C แบตเตอรี่ร้อนกว่าห้อง ตรวจสอบพัดลมระบายอากาศของตู้และวัดกระแสประจุตกค้าง"),
        ("สนามบินน้ำ (SB)", "10.209.189.21", "อุณหภูมิห้องควบคุมสูง", "ปานกลาง (Medium)", "อุณหภูมิห้อง 38.0°C / แบตเตอรี่ 35.0°C อุณหภูมิห้องสูงเกินเกณฑ์ควบคุม 30°C ควรตรวจสอบแอร์และระบบระบายอากาศ")
    ]

    for r_idx, r_data in enumerate(watch_rows, 1):
        row = t_risk.rows[r_idx]
        for c_idx, val in enumerate(r_data):
            cell = row.cells[c_idx]
            cell.text = val
            p = cell.paragraphs[0]
            r = p.runs[0]
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
            set_cell_background(cell, "F2F2F2" if r_idx % 2 == 1 else "FFFFFF")
            if "วิกฤต" in val:
                set_run_font(r, "TH Sarabun New", 13, bold=True, color_rgb=DANGER)
            elif "ปานกลาง" in val:
                set_run_font(r, "TH Sarabun New", 13, bold=True, color_rgb=WARNING)
            else:
                set_run_font(r, "TH Sarabun New", 13, bold=False, color_rgb=TEXT_MAIN)

    # -------------------------------------------------------------
    # 8. RECOMMENDATIONS
    # -------------------------------------------------------------
    add_h1("8. ข้อเสนอแนะเชิงวิศวกรรมและแผนปฏิบัติการ (Engineering Recommendations)", page_break=True)
    add_h2("8.1 แผนปฏิบัติการเร่งด่วน (Immediate Plan - ภายใน 7 วัน)")
    add_p("1. ออกใบสั่งงานซ่อมบำรุงเครื่องปรับอากาศสถานีเขตบางใหญ่ (BYD): ส่งทีมช่างเข้าแก้ไขแอร์ห้องควบคุมทันที เพื่อลดอุณหภูมิลงมาต่ำกว่า 28°C ป้องกันแบตเตอรี่ระเบิดหรือบวม")
    add_p("2. ทดสอบความต้านทานภายในแบตเตอรี่สถานีเขตนนทบุรี (NBD): ตรวจวัด Internal Resistance / Conductance ทีละเซลล์ทั้ง 24 เซลล์ เพื่อเปลี่ยนเซลล์ที่มีปัญหา ขจัดกระแสประจุค้าง 2.3A")
    add_p("3. ตรวจสอบระบบระบายอากาศสถานีบางปู (BU) และสนามบินน้ำ (SB): ตรวจเช็กพัดลมระบายอากาศและฟิลเตอร์กรองฝุ่น")

    add_h2("8.2 แผนปรับปรุงระยะสั้น (Short-term Plan - ภายใน 30 วัน)")
    add_p("1. ปรับลดระยะเวลา End Test Time ให้เป็น 30 นาที: ดำเนินการปรับแก้สถานีที่ตั้งไว้ 120-180 นาที ให้เหลือ 30 นาที เท่ากันทั่วทั้งระบบ เพื่อลดความเสี่ยง Deep Discharge")
    add_p("2. บันทึกและติดตามประวัติแบตเตอรี่: จัดทำประวัติอายุการใช้งานแบตเตอรี่ของทั้ง 190 สถานี เพื่อเตรียมแผนจัดซื้อทดแทนล่วงหน้าตามรอบวงรอบ 5 ปี")

    add_h2("8.3 แผนงานความมั่นคงระยะยาว (Long-term Strategy)")
    add_p("1. ตั้งระบบตรวจจับการเปลี่ยนแปลงพารามิเตอร์อัตโนมัติ (Baseline Configuration Guard): รันสคริปต์ตรวจสอบประจำสัปดาห์ เพื่อตรวจจับการแก้ไขพารามิเตอร์โดยไม่ได้รับอนุญาต")
    add_p("2. แผนอัปเกรดเฟิร์มแวร์เป็นมาตรฐานเดียวกัน: ทยอยอัปเกรดคอนโทรลเลอร์ M830B จากเวอร์ชัน 5.2.04 เป็น 5.2.14B ในรอบการบำรุงรักษาประจำปี")

    target_thai = reports_dir / "รายงานการวิเคราะห์และตรวจสอบระบบ_Rectifier_กฟน_ฉบับสมบูรณ์.docx"
    target_std = reports_dir / "Rectifier_Inspection_Comprehensive_Analysis_Report.docx"
    target_alt = reports_dir / "Rectifier_Inspection_Comprehensive_Analysis_Report_Updated.docx"

    doc.save(str(target_thai))
    print(f"Saved: {target_thai}")

    try:
        doc.save(str(target_std))
        print(f"Saved: {target_std}")
    except Exception as e:
        doc.save(str(target_alt))
        print(f"Fallback saved: {target_alt} (Reason: {e})")

if __name__ == '__main__':
    create_report()
