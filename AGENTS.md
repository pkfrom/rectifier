# AGENTS.md — MEA Rectifier Management System

Guidelines and architecture instructions for AI coding assistants working in this repository.

---

## 1. Project Overview

This repository manages telemetry collection, configuration validation, automated parameter updates, and reporting for **Vertiv / Emerson NetSure Rectifier Controllers (M830B NCU)** across 189 MEA (Metropolitan Electricity Authority) substations.

---

## 2. Directory Structure

```
Rectifier/
├── Rectifier.xlsx                 # Primary site list: Code, Substation Name, Ring, No., IP
├── requirements.txt               # Python dependencies (openpyxl, python-docx, etc.)
├── README.md                      # Human-facing guide & command documentation
├── AGENTS.md                      # Agent rules & technical specifications
├── scripts/                       # Production scripts
│   ├── collect_rectifier_inventory.py       # Main telemetry, settings, and hardware inventory collector
│   ├── collect_all_parameters_all_sites.py  # Full raw parameter dump across all endpoints
│   ├── rebuild_reports.py                   # Generates abnormal Excel audit & Word report
│   ├── generate_comprehensive_word_report.py# Generates executive Word report
│   ├── configure_and_verify_stations.py     # Batch config updater & verifier via CGI
│   ├── apply_extra_settings.py              # Extra parameters setup (walk-in, temp sensor, etc.)
│   ├── compare_target_settings.py           # Compares station params against reference station (BAT)
│   ├── set_equalize.py                      # Template for CGI login → read → write → verify
│   ├── set_uv_cg_lnb.py                     # Specific parameter tuning script
│   └── dev/                                 # Historical inspection, exploration, and search scripts
├── reports/                       # Generated report outputs
│   ├── Rectifier_Inventory_188_Sites.xlsx
│   ├── Rectifier_All_Parameters_All_Sites_Latest.xlsx
│   ├── Rectifier_Abnormal_Report.xlsx
│   ├── Rectifier_Inspection_Report_All_Settings.docx
│   ├── Rectifier_Inspection_Comprehensive_Analysis_Report.docx
│   └── archive/                   # Timestamped historical dumps
├── web_assets/                    # Extracted NCU controller JS/HTML files for reference
└── config/                        # Controller configuration templates (SettingParam.tar)
```

---

## 3. Essential Commands

All commands should be executable from the project root:

```bash
# 1. Collect Telemetry + Settings + Hardware Inventory (189 stations, ~30s)
python scripts/collect_rectifier_inventory.py --workers 16

# 2. Extract All Parameters Raw Dump
python scripts/collect_all_parameters_all_sites.py

# 3. Generate Inspection & Abnormal Reports
python scripts/rebuild_reports.py
python scripts/generate_comprehensive_word_report.py

# 4. Apply Configuration Updates
python scripts/configure_and_verify_stations.py
python scripts/apply_extra_settings.py
```

---

## 4. Hardware & Controller API Specifications

### Controller Architecture
- **Hardware:** Emerson / Vertiv NetSure NCU (Model M830B)
- **Web Interface:** Embedded CGI webserver running on port 80
- **Firmware Variations:**
  - Config v1.02A / SW 5.2.14B (Standard)
  - Config v1.00 / SW 5.1.x (Legacy, some endpoints return empty or use fallback signal IDs)

### Authentication
```http
POST http://<IP>/app/www_user/html/cgi-bin/web_cgi_main.cgi?_=<timestamp>
Content-Type: application/x-www-form-urlencoded

user_name=YWRtaW4=&user_password=NjQwMjc1
```
- Credential format: base64 encoded (`admin` -> `YWRtaW4=`, default password -> `NjQwMjc1`)
- Auth response: `Set-Cookie: sessionId=<token>`

### Reading Parameters
Data endpoints return pseudo-JSON terminated by `"%__data_end__%"`:
```http
GET http://<IP>/var/datas/data.setting.html?_=<timestamp>
GET http://<IP>/var/datas/data.system_inventory.html?_=<timestamp>
GET http://<IP>/var/datas/data.sys_setting.html?_=<timestamp>
```
- Arrays format: `[name, equip_ID, signal_type, signal_id, level, timestamp, max, min, value_type, current_val, options_or_unit]`
- **Value Types:**
  - `2`: Float (e.g. Voltage, Current)
  - `3`: Integer
  - `5`: Enum / Option index (0-indexed list from options array)

### Writing / Setting Parameters
```http
POST http://<IP>/app/www_user/html/cgi-bin/web_cgi_control.cgi?_=<timestamp>
Content-Type: application/x-www-form-urlencoded
Cookie: sessionId=<token>

control_value=<val>&equip_ID=<id>&signal_type=<type>&signal_id=<id>&value_type=<vt>&control_type=1&sessionId=<token>
```

---

## 5. Development & Engineering Standards

1. **Path Resolution:**
   - Always resolve paths relative to `Path(__file__).resolve().parent.parent` (project root) or check both `reports/` and cwd to support running scripts from any directory.
2. **Data Parsing:**
   - Always use `parse_device_data()` with robust handling for `nan`, `undefined`, `null`, and trailing comments before attempting JSON/eval deserialization.
3. **Safety First:**
   - Before applying settings to live substation equipment, verify targeting by Station Code and IP address.
   - Always perform verification read-back after setting any value via CGI.
4. **Encoding:**
   - Ensure `sys.stdout.reconfigure(encoding='utf-8')` is set for terminal output in scripts dealing with Thai substation names.
5. **Report Integrity:**
   - Generated reports must reside in `reports/` or `reports/archive/`. Do not pollute the repository root.
