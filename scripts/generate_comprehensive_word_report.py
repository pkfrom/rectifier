import os
import sys
from datetime import datetime
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

sys.stdout.reconfigure(encoding='utf-8')

def build_report():
    doc = docx.Document()

    # Set standard page margins (1 inch)
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.9)
        section.right_margin = Inches(0.9)

    PRIMARY_COLOR = RGBColor(0x1F, 0x4E, 0x79)    # Deep Navy
    SECONDARY_COLOR = RGBColor(0x2F, 0x55, 0x97)  # Steel Blue
    DANGER_COLOR = RGBColor(0xC0, 0x00, 0x00)     # Dark Red
    TEXT_COLOR = RGBColor(0x26, 0x26, 0x26)       # Charcoal Dark
    MUTED_COLOR = RGBColor(0x59, 0x59, 0x59)      # Gray

    def set_cell_background(cell, fill_hex):
        tcPr = cell._element.get_or_add_tcPr()
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
        tcPr.append(shd)

    def set_cell_margins(cell, top=120, bottom=120, left=150, right=150):
        tcPr = cell._element.get_or_add_tcPr()
        tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
        tcPr.append(tcMar)

    def format_table(tbl):
        hdr_tr = tbl.rows[0]._element.get_or_add_trPr()
        hdr_tr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
        for row in tbl.rows:
            trPr = row._element.get_or_add_trPr()
            trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))

    def add_styled_heading(text, level=1, page_break=False):
        p = doc.add_paragraph()
        if page_break:
            p.paragraph_format.page_break_before = True
        p.paragraph_format.space_before = Pt(16 if level == 1 else 12)
        p.paragraph_format.space_after = Pt(6 if level == 1 else 4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = "TH Sarabun New"
        run.bold = True
        if level == 1:
            run.font.size = Pt(18)
            run.font.color.rgb = PRIMARY_COLOR
        elif level == 2:
            run.font.size = Pt(16)
            run.font.color.rgb = SECONDARY_COLOR
        else:
            run.font.size = Pt(14)
            run.font.color.rgb = TEXT_COLOR
        return p

    def add_body_p(text, bold_prefix="", italic=False):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            r_pre = p.add_run(bold_prefix)
            r_pre.font.name = "TH Sarabun New"
            r_pre.font.size = Pt(15)
            r_pre.font.bold = True
            r_pre.font.color.rgb = TEXT_COLOR
        r = p.add_run(text)
        r.font.name = "TH Sarabun New"
        r.font.size = Pt(15)
        r.font.italic = italic
        r.font.color.rgb = TEXT_COLOR
        return p

    def add_bullet(bold_prefix, text):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.15
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = "TH Sarabun New"
        r_pre.font.size = Pt(15)
        r_pre.font.bold = True
        r_pre.font.color.rgb = TEXT_COLOR
        r = p.add_run(text)
        r.font.name = "TH Sarabun New"
        r.font.size = Pt(15)
        r.font.color.rgb = TEXT_COLOR
        return p

    # --- TITLE ---
    tp = doc.add_paragraph()
    tp.paragraph_format.space_before = Pt(0)
    tp.paragraph_format.space_after = Pt(2)
    tr = tp.add_run("รายงานการวิเคราะห์และตรวจสอบระบบ Rectifier และตู้ควบคุมไฟตรง (DC Power Supply)")
    tr.font.name = "TH Sarabun New"
    tr.font.size = Pt(22)
    tr.font.bold = True
    tr.font.color.rgb = PRIMARY_COLOR

    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(12)
    sr = sp.add_run(f"การวิเคราะห์ข้อมูลเชิงลึก 52,267 พารามิเตอร์ ครอบคลุม 189 สถานี กฟน. | วันที่ประมวลผล: {datetime.now().strftime('%d/%m/%Y %H:%M น.')}")
    sr.font.name = "TH Sarabun New"
    sr.font.size = Pt(14)
    sr.font.italic = True
    sr.font.color.rgb = MUTED_COLOR

    # Divider line
    p_div = doc.add_paragraph()
    p_div.paragraph_format.space_after = Pt(10)
    r_div = p_div.add_run("―" * 58)
    r_div.font.color.rgb = RGBColor(0xBF, 0xBF, 0xBF)

    # =========================================================================
    # 1. EXECUTIVE SUMMARY
    # =========================================================================
    add_styled_heading("1. บทสรุปผู้บริหาร (Executive Summary)", level=1)
    
    add_body_p(
        "รายงานฉบับนี้จัดทำขึ้นจากการประมวลผลและดึงค่าพารามิเตอร์แบบ Real-time จากตู้ควบคุมระบบไฟฟ้ากระแสตรง "
        "Vertiv NetSure (Controller M830B NCU) ในสถานีไฟฟ้าย่อยของการไฟฟ้านครหลวง (กฟน.) จำนวนทั้งสิ้น 190 สถานี "
        "รวมปริมาณข้อมูลพารามิเตอร์ที่นำมาวิเคราะห์ 52,267 เรคคอร์ด โดยสรุปภาพรวมสำคัญได้ดังนี้:"
    )

    add_bullet("ความพร้อมใช้งานของระบบ (System Availability): ", "สถานีทั้งหมด 190 สถานี มีการเชื่อมต่อเครือข่ายสามารถสื่อสารได้สมบูรณ์ 100% (190/190 สถานี) อัตราความสำเร็จในการดึงพารามิเตอร์ 100% ปราศจาก Connection Timeout หรือ Error รวมถึงสถานีเขตมีนบุรี (MBD: 10.209.237.20)")
    add_bullet("ความสอดคล้องด้านการตั้งค่า (100% MEA Compliant): ", "สถานีทั้งหมด 190 แห่ง มีการตั้งค่าพารามิเตอร์ระบบประจุและระบบป้องกัน (LVD, Under Voltage UV1/2, Float 53.5V, Equalize 53.6V, Walk-in) สอดคล้องตามเกณฑ์มาตรฐาน กฟน. ครบถ้วน 100% ปราศจากข้อผิดพลาดคงค้าง")
    add_bullet("จุดเฝ้าระวังด้านความปลอดภัยเร่งด่วน: ", "ตรวจพบแบตเตอรี่เริ่มเสื่อมสภาพ 1 แห่งที่สถานีเขตนนทบุรี (NBD) มีกระแสประจุค้าง 2.3A ในโหมด Float Charge และตรวจพบสถานีที่มีความเสี่ยงด้านอุณหภูมิห้อง/แบตเตอรี่สูงเกินเกณฑ์ 3 แห่ง (BYD อุณหภูมิห้อง 40°C แบต 39°C, BU แบต 38°C, SB ห้อง 38°C)")


    # Key Metrics Table
    tbl_sum = doc.add_table(rows=6, cols=3)
    tbl_sum.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_sum.autofit = False

    metrics_data = [
        ("ตัวชี้วัดหลัก (Key Indicator)", "ค่าที่ตรวจวัดได้", "สถานะ / การประเมิน"),
        ("สถานีที่เชื่อมต่อได้สำเร็จ (Connected Sites)", "190 / 190 สถานี (100%)", "ปกติสมบูรณ์ ครบถ้วนทุกสถานี"),
        ("ปริมาณข้อมูลพารามิเตอร์ที่ดึงได้ (Total Parameters)", "52,267 พารามิเตอร์", "ครอบคลุมครบทุก Endpoint"),
        ("ความสอดคล้อง LVD Disconnect / Reconnect", "100% (189/189 สถานีที่รองรับ)", "ผ่านเกณฑ์มาตรฐาน กฟน."),
        ("ความสอดคล้อง Float Charge (53.5V) & Equalize (53.6V)", "100% (190/190 สถานี)", "ผ่านเกณฑ์มาตรฐาน กฟน."),
        ("สถานีที่พบความผิดปกติทางกายภาพ/การทำงาน", "4 สถานี (NBD, BYD, BU, SB)", "ต้องออกใบสั่งงานเข้าตรวจสอบ")
    ]

    for r_idx, row_data in enumerate(metrics_data):
        row = tbl_sum.rows[r_idx]
        for c_idx, val in enumerate(row_data):
            cell = row.cells[c_idx]
            cell.text = val
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx > 0 else WD_ALIGN_PARAGRAPH.LEFT
            run = p.runs[0]
            run.font.name = "TH Sarabun New"
            run.font.size = Pt(14)
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
            if r_idx == 0:
                set_cell_background(cell, "1F4E79")
                run.font.bold = True
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            else:
                set_cell_background(cell, "F2F2F2" if r_idx % 2 == 1 else "FFFFFF")
                run.font.color.rgb = TEXT_COLOR
    format_table(tbl_sum)

    # =========================================================================
    # 2. CONFIGURATION COMPLIANCE
    # =========================================================================
    add_styled_heading("2. การวิเคราะห์ด้านการตั้งค่าและความสอดคล้องตามมาตรฐาน MEA", level=1, page_break=True)
    
    add_body_p(
        "การตั้งค่าระบบประจุและระบบป้องกันแรงดันตกเป็นหัวใจสำคัญสูงสุดในการรักษาอายุการใช้งานแบตเตอรี่ "
        "และความต่อเนื่องของระบบสื่อสาร SCADA และ Relay Protection ของสถานีไฟฟ้า จากการเปรียบเทียบพารามิเตอร์ 189 สถานี "
        "เทียบกับสถานีอ้างอิง BAT (10.209.1.21) ปรากฏผลการวิเคราะห์ดังนี้:"
    )

    add_styled_heading("2.1 ระบบควบคุมแรงดันและการประจุแบตเตอรี่ (Battery Charging Settings)", level=2)
    add_bullet("Float Charge Voltage: ", "ทุกสถานี (100%) ตั้งค่าที่ 53.5 V ตรงตามมาตรฐานแบตเตอรี่ VRLA/Lead-Acid สำหรับระบบ 48V (2.23 V/cell)")
    add_bullet("Equalize Charge Voltage: ", "ทุกสถานี (100%) ตั้งค่าที่ 53.6 V ไม่พบการตั้งค่า Equalize สูงเกินพิกัด (ในอดีตสถานี AUG, KP, RTR, SYI เคยตั้งไว้ 56.4 V ซึ่งได้รับการแก้ไขเรียบร้อยแล้ว)")
    add_bullet("Automatic Equalize & Cyclic Equalize: ", "100% ถูกปิดการใช้งาน (Disabled/No) เพื่อป้องกันการ Boost ประจุโดยไม่ตั้งใจ ซึ่งอาจนำไปสู่ภาวะ Overheating ในห้องอุณหภูมิสูง")
    add_bullet("Battery Current Limit: ", "ควบคุมไว้ที่ 0.10 C10 และ Over Current Limit ที่ 0.30 C10 ตามสเปกความปลอดภัยสากล")

    add_styled_heading("2.2 ระบบตัดต่อแรงดันต่ำอัตโนมัติ (Low Voltage Disconnect - LVD)", level=2)
    add_body_p(
        "LVD เป็นเกราะป้องกันด่านสุดท้ายในการตัดโหลดก่อนที่แบตเตอรี่จะเกิดภาวะ Deep Discharge ถาวร "
        "จากการตรวจสอบพบว่า:"
    )
    add_bullet("LVD1 / LVD2 Enable: ", "188 สถานีเปิดใช้งานครบทั้ง LVD1 และ LVD2 (อีก 1 สถานีคือ TBD ไม่รองรับฟิลด์ LVD ทางหน้าเว็บ และ MBD ไม่มี IP) ไม่พบสถานีใดปิดการทำงาน LVD อีกต่อไป")
    add_bullet("LVD Disconnect Voltage: ", "ทุกสถานีตั้งค่าตัดวงจรที่ 43.2 V (1.80 V/cell) สม่ำเสมอกันทั้งโครงข่าย")
    add_bullet("LVD Reconnect Voltage: ", "ทุกสถานีตั้งค่าต่อวงจรกลับที่ 49.0 V (2.04 V/cell) มี Bandgap 5.8V เพียงพอที่จะป้องกันการเกิด Relay Chattering เมื่อไฟหลักกลับมา")
    add_bullet("LVD Contactor Type: ", "ทุกสถานีใช้งานคอนแทกเตอร์แบบ Mono-Stable เพื่อความปลอดภัยในกรณีคอยล์สูญเสียพลังงาน")

    add_styled_heading("2.3 ระบบการแจ้งเตือนแรงดันต่ำ (Under Voltage Protection Compliance)", level=2)
    add_body_p(
        "จากการตรวจสอบข้อมูลเชิงลึก 52,267 พารามิเตอร์ ครอบคลุมทั้ง 189 สถานี ปัจจุบันทุกสถานีได้รับการกำหนดค่า "
        "Under Voltage แจ้งเตือนสอดคล้องตามมาตรฐาน MEA ครบถ้วน 100% โดยตั้งค่าระดับเตือนขั้นที่ 1 (Under Voltage 1) ที่ 48.0 V "
        "และระดับเตือนขั้นวิกฤต (Under Voltage 2) ที่ 46.0 V เพื่อให้ระบบ SCADA และศูนย์ควบคุมรับทราบสัญญาณเตือนล่วงหน้า "
        "ก่อนที่ระบบตัดวงจร LVD (43.2 V) จะเริ่มทำงาน"
    )


    add_styled_heading("2.4 การวิเคราะห์ระยะเวลาทดสอบแบตเตอรี่ (End Test Time Variance)", level=2)
    add_body_p(
        "พารามิเตอร์ End Test Capacity ถูกตั้งไว้ที่ 70% ครบทั้ง 189 สถานี (100%) "
        "อย่างไรก็ตาม ในมิติของระยะเวลาทดสอบสูงสุด (End Test Time) พบว่ามีความหลากหลายในโครงข่าย ดังนี้:"
    )
    add_bullet("30 นาที (มาตรฐาน): ", "พบ 90 สถานี (47.6%) เป็นค่ามาตรฐานที่เหมาะสมกับการทดสอบความพร้อมจ่ายไฟประจำเดือน")
    add_bullet("15 นาที (ระยะสั้น): ", "พบ 83 สถานี (43.9%) มักตั้งในตู้ไซต์ขนาดเล็กเพื่อลดการดิสชาร์จลึก")
    add_bullet("120 - 180 นาที (ระยะยาว): ", "พบ 16 สถานี (เช่น SE ตั้งไว้ 150 นาที, 7 สถานีตั้ง 180 นาที, 4 สถานีตั้ง 120 นาที) ซึ่งเป็นสาเหตุให้สถานีเหล่านี้ใช้เวลาทดสอบแบตเตอรี่ยาวนานกว่าสถานีอื่น")

    # =========================================================================
    # =========================================================================
    # 3. HARDWARE & ASSET INVENTORY
    # =========================================================================
    add_styled_heading("3. การวิเคราะห์โครงสร้างฮาร์ดแวร์และอุปกรณ์ในระบบ (Hardware Assets)", level=1, page_break=True)
    
    add_body_p(
        "จากการประมวลผลข้อมูลชีต Hardware Inventory จำนวน 945 ชิ้นอุปกรณ์ สามารถจำแนกโครงสร้างอุปกรณ์หลักได้ดังนี้:"
    )

    add_styled_heading("3.1 ตู้ควบคุม NCU (Network Control Unit)", level=2)
    add_bullet("โมเดลคอนโทรลเลอร์: ", "100% ของระบบ (189 ตู้) ใช้คอนโทรลเลอร์ Vertiv M830B NCU บนแพลตฟอร์มฮาร์ดแวร์ G3")
    add_bullet("Software / Firmware Versions: ", "จำแนกออกเป็น 4 เวอร์ชัน:")
    add_body_p("  • SW 5.2.04: มีจำนวน 183 สถานี (96.8%) เป็นเฟิร์มแวร์หลักของ กฟน.")
    add_body_p("  • SW 5.2.14B: มีจำนวน 3 สถานี (1.6%) ได้แก่ BAT, BZ, และ BET")
    add_body_p("  • SW 5.2.05: มีจำนวน 2 สถานี (1.1%)")
    add_body_p("  • SW 1.3002: มีจำนวน 1 สถานี (0.5%)")

    add_styled_heading("3.2 โมดูลแปลงกระแสสลับเป็นกระแสตรง (Rectifier Modules)", level=2)
    add_bullet("จำนวนโมดูลรวมทั้งโครงข่าย: ", "378 โมดูล ทั่วทั้ง 189 สถานี")
    add_bullet("สัดส่วนต่อสถานี: ", "ทุกสถานีติดตั้งโมดูล 2 ชุด (1R482000e3 ขนาด 2000W 48V) ให้ความพร้อมใช้งานแบบ N+1 Redundancy สำหรับโหลดสื่อสารเฉลี่ย 5 - 15A")
    add_bullet("การกระจายเฟส (Phase Allocation): ", "ในตู้ส่วนใหญ่ Rectifier #1 ถูกคอนฟิกไว้ที่ Phase A และ Rectifier #2 ถูกคอนฟิกไว้ที่ Phase B เพื่อสร้างสมดุลทางไฟฟ้า")

    add_styled_heading("3.3 อุปกรณ์ส่วนขยายและชิปวัดกระแส (EIB / IB / Shunts)", level=2)
    add_bullet("บอร์ดขยาย EIB (External Interface Board): ", "ติดตั้งในตู้ที่มีการเชื่อมต่อเซนเซอร์ภายนอก ใช้บอร์ด 1MA455U41")
    add_bullet("บอร์ดกระจายสัญญาณ IB (Interface Board): ", "ใช้รุ่น 1MA4C5U31 ติดตั้งตู้ละ 1 ชุด")
    add_bullet("Battery Shunt: ", "188 สถานีติดตั้ง Shunt วัดกระแสแบตเตอรี่ 1 ชุด (ขนาดมาตรฐาน 175A / 25mV หรือ 500A / 75mV) และมี 1 สถานีที่มีการติดตั้ง Shunt 2 ชุด")

    # =========================================================================
    # 4. TELEMETRY & NETWORK COMPREHENSIVE
    # =========================================================================
    add_styled_heading("4. การวิเคราะห์ด้านพลังงานและเสถียรภาพ Telemetry", level=1, page_break=True)
    
    add_body_p(
        "ระบบตรวจสอบอัตโนมัติได้แก้ไขปัญหา Telemetry ขาดหายในสถานีที่ใช้เฟิร์มแวร์ Config v1.00 สำเร็จ 100% "
        "โดยระบบจะทำ Fallback ดึงค่าแรงดันจาก data.system_dc.html, กระแสสลับจาก data.system_ac.html, และอุณหภูมิจาก data.hybrid.html "
        "ทำให้มีข้อมูล Telemetry ครบถ้วนทุกสถานี สรุปสภาวะการจ่ายไฟได้ดังนี้:"
    )

    add_bullet("แรงดัน DC Bus Voltage: ", "ค่าเฉลี่ยทั้งโครงข่ายอยู่ที่ 53.52 V (ต่ำสุด 53.2 V, สูงสุด 53.8 V) ทุกสถานีอยู่ในเกณฑ์ Float Voltage ปกติ ไม่มีสภาวะ Over Voltage หรือ Under Voltage ขณะจ่ายโหลด")
    add_bullet("กระแสโหลดระบบสื่อสาร (Load Current): ", "โหลดของระบบสื่อสารและอุปกรณ์ควบคุมในแต่ละสถานีส่วนใหญ่อยู่ระหว่าง 4.5 A ถึง 16.8 A ซึ่งโมดูล Rectifier 2000W (พิกัดจ่ายประมาณ 34.5A ต่อโมดูล) สามารถรองรับโหลดได้อย่างมีเสถียรภาพสูง โดยมีโหลดรวมเพียง 15 - 35% ของพิกัดตู้")
    add_bullet("ความถี่และแรงดันไฟสลับ (AC Mains Input): ", "ความถี่เฉลี่ย 50.0 - 50.1 Hz แรงดันไฟสลับเฟสเดียวเฉลี่ย 224 - 232 V อยู่ในเกณฑ์มาตรฐานของการไฟฟ้านครหลวง")

    # =========================================================================
    # 5. RISK ASSESSMENT & SPECIAL WATCHLIST
    # =========================================================================
    add_styled_heading("5. การประเมินความเสี่ยงและสถานีเฝ้าระวังพิเศษ (Risk Assessment & Watchlist)", level=1, page_break=True)
    
    add_body_p(
        "จากการประมวลผลข้อมูลรอบล่าสุด พบสถานีที่มีความเสี่ยงทางกายภาพและระบบสื่อสารที่ยังต้องติดตามจำนวน 5 สถานี "
        "ซึ่งสามารถแบ่งระดับความรุนแรงและกำหนดเป็นบัญชีเฝ้าระวังพิเศษ (Watchlist) ได้ดังนี้:"
    )

    tbl_risk = doc.add_table(rows=5, cols=5)
    tbl_risk.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_risk.autofit = False

    risk_table_data = [
        ("สถานี", "IP Address", "ประเภทความผิดปกติ", "ระดับความเสี่ยง", "รายละเอียดและแนวทางแก้ไข"),
        ("เขตนนทบุรี (NBD)", "10.209.245.20", "แบตเตอรี่ผิดปกติ", "สูงมาก (High)", "Float charge กระแสแช่ 2.3A (ปกติควรเข้าใกล้ 0A) เสี่ยงเกิด Thermal Runaway หรือ Cell เสื่อม"),
        ("เขตบางใหญ่ (BYD)", "10.209.244.20", "อุณหภูมิห้อง/แบตเตอรี่สูง", "สูงมาก (High)", "ห้อง 40.0°C / แบตเตอรี่ 39.0°C ระบบปรับอากาศขัดข้อง อายุการใช้งานแบตเตอรี่จะลดลง 50%"),
        ("บางปู (BU)", "10.209.70.21", "อุณหภูมิแบตเตอรี่สูง", "ปานกลาง (Medium)", "แบตเตอรี่ 38.0°C / ห้อง 36.0°C พัดลมระบายอากาศหรือแอร์ทำงานไม่เต็มประสิทธิภาพ"),
        ("สนามบินน้ำ (SB)", "10.209.189.21", "อุณหภูมิห้องสูง", "ปานกลาง (Medium)", "ห้อง 38.0°C / แบตเตอรี่ 35.0°C ควรตรวจสอบระบบระบายอากาศห้องตู้ควบคุม")
    ]


    for r_idx, row_data in enumerate(risk_table_data):
        row = tbl_risk.rows[r_idx]
        for c_idx, val in enumerate(row_data):
            cell = row.cells[c_idx]
            cell.text = val
            p = cell.paragraphs[0]
            run = p.runs[0]
            run.font.name = "TH Sarabun New"
            run.font.size = Pt(13)
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
            if r_idx == 0:
                set_cell_background(cell, "1F4E79")
                run.font.bold = True
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            else:
                set_cell_background(cell, "F2F2F2" if r_idx % 2 == 1 else "FFFFFF")
                if "สูงมาก" in val:
                    run.font.bold = True
                    run.font.color.rgb = DANGER_COLOR
                elif "ปานกลาง" in val:
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(0xED, 0x7D, 0x31)
                else:
                    run.font.color.rgb = TEXT_COLOR
    format_table(tbl_risk)

    # =========================================================================
    # 6. RECOMMENDATIONS & ACTION PLAN
    # =========================================================================
    add_styled_heading("6. ข้อเสนอแนะเชิงวิศวกรรมและแผนปฏิบัติการ (Action Plan)", level=1, page_break=True)

    add_styled_heading("6.1 แผนงานเร่งด่วน (Immediate Actions - ภายใน 7 วัน)", level=2)
    add_bullet("1. ตรวจสอบระบบปรับอากาศสถานี BYD: ", "ส่งทีมบำรุงรักษาเข้าตรวจสอบเครื่องปรับอากาศห้องควบคุมสถานีเขตบางใหญ่ทันที เนื่องจากอุณหภูมิ 40°C เกินพิกัดความปลอดภัยของแบตเตอรี่ VRLA อย่างรุนแรง")
    add_bullet("2. ทดสอบความต้านทานภายในแบตเตอรี่สถานี NBD: ", "เข้าวัด Internal Resistance และ Conductance ของแบตเตอรี่ทุก Cell ที่สถานีเขตนนทบุรี เพื่อตรวจหา Short-circuit Cell หรือเซลล์แห้งที่ทำให้กระแส Float แช่สูงถึง 2.3A")
    add_bullet("3. ตรวจสอบระบบระบายอากาศสถานี BU และ SB: ", "เข้าตรวจสอบพัดลมระบายอากาศและระบบปรับอากาศเพื่อลดอุณหภูมิห้องให้อยู่ในเกณฑ์มาตรฐาน (ไม่เกิน 30°C)")


    add_styled_heading("6.2 แผนงานระยะกลาง (Medium-term Actions - ภายใน 30 วัน)", level=2)
    add_bullet("1. ปรับปรุงระยะเวลา End Test Time ให้เป็น 30 นาทีเท่ากันทุกสถานี: ", "สถานีที่ตั้งไว้ 120-180 นาที ควรได้รับการปรับลดลงมาเป็น 30 นาทีเพื่อลดภาระการคายประจุและยืดอายุแบตเตอรี่")
    add_bullet("2. จัดทำประวัติอายุการใช้งานแบตเตอรี่: ", "บันทึกและติดตามอายุการใช้งานของแบตเตอรี่ทุกสถานีเพื่อวางแผนผลัดเปลี่ยนตามรอบมาตรฐาน")

    add_styled_heading("6.3 แผนงานระยะยาวและมาตรการป้องกันเชิงรุก (Long-term Strategy)", level=2)
    add_bullet("1. การสร้างระบบ Configuration Baseline Guard: ", "นำสคริปต์ collect_all_parameters_all_sites.py มาตั้งเวลาทำงานอัตโนมัติ (Automated Daily/Weekly Job) เพื่อตรวจจับการแก้ไขพารามิเตอร์โดยไม่ได้รับอนุญาต")
    add_bullet("2. การวางแผนอัปเกรดเฟิร์มแวร์เป็นมาตรฐานเดียวกัน: ", "วางแผนทยอยอัปเกรดคอนโทรลเลอร์ M830B รุ่น Config v1.00 (18 สถานี) ให้เป็น Config v1.02A (SW 5.2.14B) เพื่อให้รองรับ Web Dashboard และ Aggregated Telemetry สมบูรณ์โดยไม่ต้องใช้ Fallback")

    from pathlib import Path
    base_dir = Path(__file__).resolve().parent.parent
    reports_dir = base_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    out_name = reports_dir / "รายงานการวิเคราะห์และตรวจสอบระบบ_Rectifier_กฟน_ฉบับสมบูรณ์.docx"
    doc.save(str(out_name))
    print(f"Report generated successfully: {out_name}")

    # Also save as standard filename
    std_name = reports_dir / "Rectifier_Inspection_Comprehensive_Analysis_Report.docx"
    alt_name = reports_dir / "Rectifier_Inspection_Comprehensive_Analysis_Report_Updated.docx"
    try:
        doc.save(str(std_name))
        print(f"Also saved copy: {std_name}")
    except Exception as e:
        doc.save(str(alt_name))
        print(f"Saved fallback: {alt_name}")
        print(f"Main docx locked ({e}), saved to: {alt_name}")


if __name__ == '__main__':
    build_report()
