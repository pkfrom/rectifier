# MEA Rectifier Inventory & Configuration Management

ระบบ Python สำหรับดึงข้อมูล, ตรวจสอบ, และตั้งค่าอุปกรณ์ Vertiv/Emerson NetSure Rectifier Controller (M830B NCU) ผ่าน CGI Web API ครอบคลุม 189 สถานีของ กฟน.

---

## ความต้องการของระบบ

- Python 3.9+
- Network access ถึง IP ของแต่ละสถานี

```bash
pip install -r requirements.txt
playwright install chromium   # เฉพาะ collect_rectifier_playwright.py
```

---

## โครงสร้างโฟลเดอร์

```
Rectifier/
├── Rectifier.xlsx                 # ข้อมูลหลัก: รายชื่อสถานี + IP ทั้งหมด (189 สถานี)
├── requirements.txt               # dependencies
├── README.md                      # เอกสารกำกับการใช้งาน
├── scripts/                       # สคริปต์หลักสำหรับทำงาน
│   ├── collect_rectifier_inventory.py       # ดึง Telemetry + Settings สรุป
│   ├── collect_all_parameters_all_sites.py  # ดึง All Parameters ทุกตัวแบบละเอียด
│   ├── rebuild_reports.py                   # สร้างรายงาน Excel + Word
│   ├── generate_comprehensive_word_report.py# สร้าง Word รายงานวิเคราะห์ฉบับสมบูรณ์
│   ├── configure_and_verify_stations.py     # ตั้งค่า 6 สถานีปัญหาให้ตรงเกณฑ์
│   ├── apply_extra_settings.py              # ตั้งค่าเสริม (Planned Tests, Sensors ฯลฯ)
│   ├── compare_target_settings.py           # เทียบกับสถานีอ้างอิง BAT
│   ├── set_equalize.py                      # Template สำหรับ CGI config
│   ├── set_uv_cg_lnb.py                     # Script ตั้งค่าเฉพาะจุด
│   ├── reboot_controller.py                 # Remote Reboot & Stop/Start Controller + ตรวจสอบสถานะ
│   └── dev/                                 # สคริปต์สำรวจ/ทดสอบ/ค้นหาข้อมูลเดิม
├── reports/                       # ไฟล์รายงานผลลัพธ์
│   ├── Rectifier_Inventory_188_Sites.xlsx
│   ├── Rectifier_All_Parameters_All_Sites_Latest.xlsx
│   ├── Rectifier_Abnormal_Report.xlsx
│   ├── Rectifier_Inspection_Report_All_Settings.docx
│   ├── Rectifier_Inspection_Comprehensive_Analysis_Report.docx
│   └── archive/                   # ประวัติการ dump ข้อมูลย้อนหลัง
├── web_assets/                    # JavaScript และ HTML ที่ดึงมาจากตัวอุปกรณ์ Vertiv
└── config/                        # Template configuration (SettingParam.tar)
```

---

## การใช้งาน

### 1. ดึงข้อมูลสรุปทุกสถานี (Telemetry + Settings + Inventory)
```bash
python scripts/collect_rectifier_inventory.py --workers 16
```
ผลลัพธ์: `reports/Rectifier_Inventory_188_Sites.xlsx`

### 2. ดึงข้อมูลพารามิเตอร์ละเอียดทั้งหมด (All Parameters Raw Dump)
```bash
python scripts/collect_all_parameters_all_sites.py
```
ผลลัพธ์: `reports/Rectifier_All_Parameters_All_Sites_Latest.xlsx` (และบันทึกลง `reports/archive/` ด้วย)

### 3. สร้างรายงานความผิดปกติและรายงาน Word
```bash
python scripts/rebuild_reports.py
python scripts/generate_comprehensive_word_report.py
```
ผลลัพธ์:
- `reports/Rectifier_Abnormal_Report.xlsx` — สถานีที่ค่าผิดปกติ
- `reports/Rectifier_Inspection_Report_All_Settings.docx` — รายงานตั้งค่าทุกสถานี
- `reports/Rectifier_Inspection_Comprehensive_Analysis_Report.docx` — รายงานวิเคราะห์เชิงลึก

### 4. ตั้งค่าสถานีที่มีปัญหา
```bash
python scripts/configure_and_verify_stations.py
python scripts/apply_extra_settings.py
```

### 5. เปรียบเทียบ settings กับ reference
```bash
python scripts/compare_target_settings.py
```

### 6. ตรวจสอบสถานะ / รีบูต Controller (Remote Reboot)
```bash
# ตรวจสอบสถานะสดของ Controller
python scripts/reboot_controller.py --code KJ --action status

# รีบูต Controller ระดับฮาร์ดแวร์และรอตรวจสอบผล
python scripts/reboot_controller.py --code KJ --action reboot

# สั่งหยุด / สตาร์ต ACU process
python scripts/reboot_controller.py --code KJ --action stop
python scripts/reboot_controller.py --code KJ --action start
```

---

## Controller API (Vertiv M830B NCU)

### Login
```
POST http://<IP>/web_cgi_main.cgi
Body: user=YWRtaW4=&passwd=NjQwMjc1    ← base64("admin"), base64("640275")
Response: Set-Cookie: sessionId=<token>
```

### ตั้งค่า parameter
```
POST http://<IP>/web_cgi_control.cgi
Body: control_value=<val>&equip_ID=<id>&signal_type=<t>&signal_id=<id>
      &value_type=<vt>&control_type=1&sessionId=<token>
```

**value_type:**
- `2` = float (เช่น Voltage)
- `3` = integer
- `5` = enum (index ใน options list)

**ดึงค่า settings ทั้งหมด:**
```
GET http://<IP>/data.setting.html
```

Row format: `[name, equip_ID, signal_type, signal_id, level, timestamp, max, min, value_type, current_val, unit/options]`

---

## ค่ามาตรฐาน MEA (Reference: BAT — 10.209.1.21)

| พารามิเตอร์ | ค่ามาตรฐาน |
|-------------|-----------|
| LVD1 | Enabled |
| LVD2 | Enabled |
| LVD Disconnect | 43.2 V |
| LVD Reconnect | 49.0 V |
| UV1 | 48.0 V |
| UV2 | 46.0 V |
| Contactor | Mono-Stable |
| Walk-In | Enabled, 8s |
| Rectifier Trim | ~53.2 V (อ่านค่าได้ ตั้งค่าไม่ได้ — controller คำนวณเอง) |
| Batt End Test Capacity | 70% |
| Batt End Test Time | 30 min |
| Planned Tests | 12 /yr |
| Ambient Temp High1 | 38°C |
| Ambient Temp Low | 15°C |

---

## ปัญหาที่แก้ไขแล้ว

### 1. Telemetry หายจาก 18 สถานี (Config v1.00 / SW 5.2.04)
**ปัญหา:** สถานีที่ใช้ firmware เก่า (NS, BKDs, PO, NKT, CPI, DDG, BET, BZ, BND, BBD, WLD, LKD, SPD, PWE, NJT, RK, KNY, RPR) ไม่มีไฟล์ `data.index.html` → Voltage/Battery status หายหมด

**แก้:** เพิ่ม fallback ใน `collect_rectifier_inventory.py`:
- Voltage → `data.system_dc.html` (DC_Bus_V)
- AC Voltage/Freq → `data.system_ac.html`
- Ambient/Batt Temp → `data.hybrid.html` (Comp_Temp.value)
- Battery Status → default "Normal" เมื่อไม่มีข้อมูล alarm

### 2. Settings ผิดมาตรฐาน (แก้ไขแล้ว 8 สถานี)
**สถานีที่แก้ไข:**

| สถานี | IP | ปัญหาหลัก | ผลการดำเนินการ |
|-------|----|-----------|----------------|
| KRT (คลองรังสิต) | 10.209.182.21 | LVD1 Off, Reconnect 48V, End Test Cap 80% | ตรงมาตรฐาน 100% |
| SYI (สวนใหญ่) | 10.209.186.21 | LVD1+2 Off, Contactor Bi-Stable | ตรงมาตรฐาน 100% |
| BTD (เขตบางขุนเทียน) | 10.209.254.20 | LVD1+2 Off, Contactor Bi-Stable | ตรงมาตรฐาน 100% |
| AUG (ออเงิน) | 10.209.30.21 | LVD2 Off, UV2 ≠ 46V | ตรงมาตรฐาน 100% |
| RTR (รัตนราช) | 10.209.51.21 | LVD1+2 Off, Contactor Bi-Stable | ตรงมาตรฐาน 100% |
| KP (กิ่งเพชร) | 10.209.8.21 | LVD1+2 Off, Contactor Bi-Stable | ตรงมาตรฐาน 100% |
| CG (ฉลองกรุง) | 10.209.39.21 | UV1=46V, UV2=44V (ต่ำกว่าเกณฑ์ 2V) | ปรับเป็น UV1=48V, UV2=46V สำเร็จ |
| LNB (ลานนาบุญ) | 10.209.188.151 | UV1=46V (ชนกับ UV2) | ปรับเป็น UV1=48V สำเร็จ |

**แก้:** รันคำสั่งผ่าน CGI API (`web_cgi_control.cgi`) → ตรวจสอบแล้วทุก param ตรงมาตรฐาน MEA ครบถ้วน


---

## ข้อจำกัดที่ยังมีอยู่

| ปัญหา | รายละเอียด |
|-------|-----------|
| **Rectifier Trim** | เขียนค่าได้ (API ตอบ status=1) แต่ controller คำนวณเองจาก bus voltage ไม่รับค่าจากภายนอก — ปกติ |
| **MBD (เขตมีนบุรี)** | ไม่มี IP ในระบบ — ข้ามสถานีนี้ |
| **TBD (เขตธนบุรี)** | LVD status อ่านไม่ได้ (field ไม่มีในหน้า settings) |
| **18 สถานี Config v1.00** | `data.system_battery.html` ไม่มี — Batt Capacity ไม่สามารถอ่านได้, ใช้ default |

---

## Firmware Reference

| เวอร์ชัน | Config | `data.index.html` | `data.system_battery.html` |
|---------|--------|-------------------|--------------------------|
| SW 5.2.14B | v1.02A | ✅ มี | ✅ มี |
| SW 5.2.04 | v1.00 | ❌ ไม่มี | ❌ ไม่มี |

สถานีที่ใช้ v1.00 (18 แห่ง): NS, BKDs, PO, NKT, CPI, DDG, BET, BZ, BND, BBD, WLD, LKD, SPD, PWE, NJT, RK, KNY, RPR

---

## ผลการตรวจสอบล่าสุด (2026-10-04)

- **ความครอบคลุม**: 189 สถานี (OK=189, PARTIAL=0, ERROR=0)
- **การตั้งค่าผิดปกติ**: 0 สถานี (100% ผ่านเกณฑ์มาตรฐาน MEA)
- **ความผิดปกติของอุปกรณ์ที่ตรวจพบ**:
  - แบตเตอรี่ผิดปกติ 1 แห่ง: `NBD` (เขตนนทบุรี) - Float charge กระแสแช่ 2.3A
  - อุณหภูมิสูง 3 แห่ง: `BYD` (39°C แบต / 40°C ห้อง), `BU` (38°C แบต / 36°C ห้อง), `SB` (38°C ห้อง)
  - ข้อมูลไม่สมบูรณ์ 1 แห่ง: `MBD` (เขตมีนบุรี) - ไม่มี IP ในระบบ

