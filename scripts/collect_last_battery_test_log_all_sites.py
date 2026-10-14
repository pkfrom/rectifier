# -*- coding: utf-8 -*-
from __future__ import annotations
import sys
if sys.stdout.encoding.lower() != 'utf-8':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass

import time, json, re, ast, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

PROJECT_ROOT = Path(r"Y:\Rectifier")
DATA_MARKER = '"%__data_end__%"'

def parse_device_data(raw: bytes) -> dict[str, Any]:
    text = raw.decode("utf-8-sig", errors="replace")
    text = re.sub(r"/\*[\s\S]*?\*/|//.*", "", text).strip()
    text = text.split(DATA_MARKER, 1)[0].strip()
    try:
        return json.loads(text)
    except Exception:
        python_text = re.sub(r"\btrue\b", "True", text)
        python_text = re.sub(r"\bfalse\b", "False", python_text)
        python_text = re.sub(r"\bnull\b", "None", python_text)
        python_text = re.sub(r"\bundefined\b", "None", python_text)
        python_text = re.sub(r"\bnan\b", "None", python_text, flags=re.IGNORECASE)
        return ast.literal_eval(python_text)

def get_json(ip: str, path: str, timeout: float = 3.5) -> dict[str, Any]:
    url = f"http://{ip}{path}?_={int(time.time() * 1000)}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "MEA-Rectifier/1.0", "Cache-Control": "no-cache"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return parse_device_data(resp.read())

def parse_telemetry_num(raw: Any) -> str:
    if isinstance(raw, list) and len(raw) >= 4:
        val, alarm, unvalid, not_config = raw[0], raw[1], raw[2], raw[3]
        if unvalid == 1 or not_config == 1: return ""
        if isinstance(val, list) and len(val) > 0: val = val[0]
        val_str = str(val).strip()
        m = re.search(r"[-+]?\d+(?:\.\d+)?", val_str)
        return f"{float(m.group(0)):g}" if m else val_str
    elif isinstance(raw, list) and len(raw) > 0:
        val = raw[0]
        if isinstance(val, list) and len(val) > 0: val = val[0]
        val_str = str(val).strip()
        m = re.search(r"[-+]?\d+(?:\.\d+)?", val_str)
        return f"{float(m.group(0)):g}" if m else val_str
    elif isinstance(raw, (int, float)): return f"{raw:g}"
    elif isinstance(raw, str):
        val_str = raw.strip()
        m = re.search(r"[-+]?\d+(?:\.\d+)?", val_str)
        return f"{float(m.group(0)):g}" if m else val_str
    return ""

def parse_telemetry_text(raw: Any) -> str:
    if isinstance(raw, list) and len(raw) >= 4:
        val, alarm, unvalid, not_config = raw[0], raw[1], raw[2], raw[3]
        if unvalid == 1 or not_config == 1: return ""
        if isinstance(val, list) and len(val) > 0: val = val[0]
        return str(val).strip()
    elif isinstance(raw, list) and len(raw) > 0:
        val = raw[0]
        if isinstance(val, list) and len(val) > 0: val = val[0]
        return str(val).strip()
    elif raw is not None:
        return str(raw).strip()
    return ""

def poll_site(site: dict[str, Any], timeout: float = 3.5) -> dict[str, Any]:
    ip = str(site.get("IP", "")).strip()
    res = {
        "No": site.get("No", ""),
        "Code": site.get("Code", ""),
        "Name": site.get("Name", ""),
        "Ring": site.get("Ring", ""),
        "IP": ip,
        "Status": "ONLINE",
        "LastTestTime": "--",
        "LastTestTimestamp": 0,
        "BattTestControlVal": "",
        "BattState": "",
        "BattCapacity": "",
        "BattRating": "",
        "BattCurrent": "",
        "BattTemp": "",
        "EstimatedBackup": "",
        "SystemDCVoltage": "",
        "TestsPerYear": "",
        "EndTestVoltage": "",
        "EndTestTime": "",
        "EndTestCapacity": "",
        "TestVoltageLevel": "",
        "TotalAlarms": 0,
        "BatteryAlarms": "",
        "AllAlarms": "",
        "AuditConfig": "PASS",
        "AuditHealth": "NORMAL",
        "Error": ""
    }
    if not ip or ip == "nan":
        res["Status"] = "NO_IP"
        res["AuditConfig"] = "N/A"
        res["AuditHealth"] = "N/A"
        res["Error"] = "No IP"
        return res

    try:
        s = get_json(ip, "/var/datas/data.setting.html", timeout=timeout)
        batt_test_list = s.get("BATT_TEST", {}).get("list", [])
        for item in batt_test_list:
            if not isinstance(item, list) or len(item) < 10: continue
            name = item[0][0] if isinstance(item[0], list) else str(item[0])
            name = name.strip()
            ts = item[5]
            val = item[9]
            if name == "Battery Test Control":
                res["BattTestControlVal"] = str(val)
                res["LastTestTimestamp"] = ts
                if ts > 0:
                    res["LastTestTime"] = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
            elif name == "Number of Planned Tests per Year":
                res["TestsPerYear"] = str(val)
            elif name == "End Test Voltage":
                res["EndTestVoltage"] = str(val)
            elif name == "End Test Time":
                res["EndTestTime"] = str(val)
            elif name == "End Test Capacity":
                res["EndTestCapacity"] = str(val)
            elif name == "Test Voltage Level":
                res["TestVoltageLevel"] = str(val)
    except Exception as e:
        res["Error"] = f"Setting: {e}"

    try:
        b = get_json(ip, "/var/datas/data.system_battery.html", timeout=timeout)
        grp = b.get("group", {})
        chart = grp.get("chart", {})
        res["BattTemp"] = parse_telemetry_num(chart.get("Battery_Temperature", ""))
        res["EstimatedBackup"] = parse_telemetry_num(chart.get("Estimated_Remaining_Time", ""))
        for item in grp.get("list", []):
            if isinstance(item, list) and len(item) >= 2:
                nm = item[0][0] if isinstance(item[0], list) else str(item[0])
                if "management state" in nm.lower():
                    res["BattState"] = parse_telemetry_text(item[1])
                elif "current" in nm.lower():
                    res["BattCurrent"] = parse_telemetry_num(item[1])
        cnt = b.get("BATT_CONTENT", {}).get("ID_COM_BATT_CONTENT", [])
        if len(cnt) >= 2 and isinstance(cnt[1], list) and len(cnt[1]) > 0 and len(cnt[1][0]) >= 4:
            res["BattCapacity"] = parse_telemetry_num(cnt[1][0][3])
            res["BattRating"] = parse_telemetry_text(cnt[1][0][2])
    except Exception as e:
        if not res["Error"]: res["Error"] = f"Battery: {e}"

    try:
        al = get_json(ip, "/var/datas/data.alarms.html", timeout=timeout)
        res["TotalAlarms"] = al.get("AllAlarms", 0)
        alarm_strs = []
        batt_alarm_strs = []
        for a in al.get("Content", []):
            astr = str(a[0] if isinstance(a, list) and a else a)
            alarm_strs.append(astr)
            if any(k in astr.lower() for k in ["batt", "test", "capacity", "discharge", "fuse", "temp"]):
                batt_alarm_strs.append(astr)
        res["AllAlarms"] = "; ".join(alarm_strs)
        res["BatteryAlarms"] = "; ".join(batt_alarm_strs)
        if "status" in al and len(al["status"]) > 0:
            res["SystemDCVoltage"] = parse_telemetry_num(al["status"][0])
    except Exception as e:
        if not res["Error"]: res["Error"] = f"Alarms: {e}"

    if not res["BattState"] and not res["SystemDCVoltage"] and not res["TestsPerYear"]:
        res["Status"] = "OFFLINE"
        res["AuditConfig"] = "N/A"
        res["AuditHealth"] = "N/A"
        return res

    cfg_errs = []
    if res["TestsPerYear"] and res["TestsPerYear"] != "12": cfg_errs.append(f"Tests={res['TestsPerYear']}")
    if res["EndTestVoltage"] and res["EndTestVoltage"] not in ("45.2", "45.20"): cfg_errs.append(f"EndV={res['EndTestVoltage']}")
    if res["EndTestTime"] and res["EndTestTime"] not in ("30", "15"): cfg_errs.append(f"Time={res['EndTestTime']}")
    if res["EndTestCapacity"] and res["EndTestCapacity"] not in ("70", "70.0"): cfg_errs.append(f"Cap={res['EndTestCapacity']}")
    if cfg_errs: res["AuditConfig"] = "MISMATCH: " + ", ".join(cfg_errs)
    elif not res["TestsPerYear"]: res["AuditConfig"] = "UNVERIFIED"

    hlth_errs = []
    if res["BatteryAlarms"]: hlth_errs.append(f"Alarm: {res['BatteryAlarms']}")
    try:
        if res["BattCapacity"] and float(res["BattCapacity"]) < 90: hlth_errs.append(f"Cap={res['BattCapacity']}%")
    except Exception: pass
    try:
        if res["BattTemp"] and float(res["BattTemp"]) > 45: hlth_errs.append(f"Temp={res['BattTemp']}C")
    except Exception: pass
    if res["BattState"] and res["BattState"].lower() in ["discharge", "alarm", "battery fail"]:
        hlth_errs.append(f"State={res['BattState']}")
    if hlth_errs: res["AuditHealth"] = "WARNING: " + "; ".join(hlth_errs)

    return res

def main():
    excel_path = PROJECT_ROOT / "Rectifier.xlsx"
    wb_in = openpyxl.load_workbook(excel_path, data_only=True)
    ws_in = wb_in.active
    rows = list(ws_in.iter_rows(values_only=True))
    sites = []
    for r in rows[1:]:
        if not r or not r[0]: continue
        sites.append({
            "Code": str(r[0]).strip(),
            "Name": str(r[1]).strip() if len(r) > 1 and r[1] else "",
            "Ring": str(r[2]).strip() if len(r) > 2 and r[2] is not None else "",
            "No": str(r[3]).strip() if len(r) > 3 and r[3] is not None else "",
            "IP": str(r[4]).strip() if len(r) > 4 and r[4] else ""
        })

    print(f"Starting live poll for {len(sites)} sites across MEA network...")
    t0 = time.time()
    results = [None] * len(sites)
    with ThreadPoolExecutor(max_workers=25) as ex:
        futs = {ex.submit(poll_site, s, 3.5): i for i, s in enumerate(sites)}
        done = 0
        for f in as_completed(futs):
            idx = futs[f]
            try: results[idx] = f.result()
            except Exception as e:
                s = sites[idx]
                results[idx] = {"No": s["No"], "Code": s["Code"], "Name": s["Name"], "Ring": s["Ring"], "IP": s["IP"], "Status": "ERROR", "Error": str(e)}
            done += 1
            if done % 30 == 0 or done == len(sites):
                print(f"Progress: {done}/{len(sites)} sites ({time.time()-t0:.1f}s)")

    elapsed = time.time() - t0
    print(f"All {len(sites)} sites polled in {elapsed:.2f} seconds.")

    ts_now = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = PROJECT_ROOT / "reports" / f"Rectifier_Last_Battery_Test_Log_All_Sites_{ts_now}.xlsx"
    wb_out = openpyxl.Workbook()

    ws_s = wb_out.active
    ws_s.title = "Summary"
    ws_s.views.sheetView[0].showGridLines = True
    f_title = Font(name="Calibri", size=15, bold=True, color="1F497D")
    f_hdr = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    f_b = Font(name="Calibri", size=11, bold=True)
    f_n = Font(name="Calibri", size=10)
    p_hdr = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
    p_grn = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    f_grn = Font(name="Calibri", size=10, color="006100", bold=True)
    p_red = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
    f_red = Font(name="Calibri", size=10, color="9C0006", bold=True)
    p_yel = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
    f_yel = Font(name="Calibri", size=10, color="9C6500", bold=True)
    brd = Border(left=Side(style="thin", color="D3D3D3"), right=Side(style="thin", color="D3D3D3"), top=Side(style="thin", color="D3D3D3"), bottom=Side(style="thin", color="D3D3D3"))

    ws_s.cell(row=1, column=1, value="รายงานสดประวัติและการทดสอบแบตเตอรี่ (Last Battery Test Log All Sites)").font = f_title
    ws_s.cell(row=2, column=1, value=f"เวลาที่ดึงข้อมูลสด: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | จำนวนสถานีทั้งหมด: {len(results)} สถานี").font = Font(size=11, italic=True)

    online = sum(1 for r in results if r["Status"] == "ONLINE")
    offline = sum(1 for r in results if r["Status"] == "OFFLINE")
    no_ip = sum(1 for r in results if r["Status"] == "NO_IP")
    pass_cfg = sum(1 for r in results if r["AuditConfig"] == "PASS")
    mismatch_cfg = sum(1 for r in results if str(r["AuditConfig"]).startswith("MISMATCH"))
    healthy = sum(1 for r in results if r["AuditHealth"] == "NORMAL" and r["Status"] == "ONLINE")
    warn = sum(1 for r in results if str(r["AuditHealth"]).startswith("WARNING"))
    float_cnt = sum(1 for r in results if "float" in str(r["BattState"]).lower())
    planned_cnt = sum(1 for r in results if "planned" in str(r["BattState"]).lower() or "test" in str(r["BattState"]).lower())
    alarms_cnt = sum(1 for r in results if r.get("BatteryAlarms"))

    tested_oct = sum(1 for r in results if str(r["LastTestTime"]).startswith("2026-10"))
    tested_sep = sum(1 for r in results if str(r["LastTestTime"]).startswith("2026-09"))
    tested_older = sum(1 for r in results if r["LastTestTime"] != "--" and not str(r["LastTestTime"]).startswith("2026-10") and not str(r["LastTestTime"]).startswith("2026-09"))

    summary_data = [
        ("หัวข้อสรุปภาพรวม (Metric)", "จำนวน (สถานี)", "ร้อยละ (%)", "คำอธิบาย"),
        ("จำนวนสถานีทั้งหมดในฐานข้อมูล", len(results), "100.0%", "สถานี Rectifier ทั้งหมด"),
        ("สถานีออนไลน์ดึงข้อมูลสำเร็จ (Online)", online, f"{online/len(results)*100:.1f}%", "เชื่อมต่ออ่านค่าสดได้ครบ"),
        ("สถานีออฟไลน์/ติดต่อไม่ได้ (Offline/Timeout)", offline, f"{offline/len(results)*100:.1f}%", "คอนโทรลเลอร์หรือเน็ตเวิร์กไม่ตอบสนอง"),
        ("สถานีไม่มี IP ในระบบ (No IP)", no_ip, f"{no_ip/len(results)*100:.1f}%", "สถานีที่รอจัดสรร IP"),
        ("", "", "", ""),
        ("การตั้งค่า Battery Test 12 ครั้ง/ปี ถูกต้อง (Config PASS)", pass_cfg, f"{pass_cfg/len(results)*100:.1f}%", "12 ครั้ง/ปี, 45.0V, 45.2V, 30m, 70%"),
        ("การตั้งค่า Battery Test มีความต่าง (Config Mismatch)", mismatch_cfg, f"{mismatch_cfg/len(results)*100:.1f}%", "เช่น รุ่นเก่าใช้ 15 นาที"),
        ("", "", "", ""),
        ("บันทึกการสั่งทดสอบแบตเตอรี่ในเดือนนี้ (Last Test Oct 2026)", tested_oct, f"{tested_oct/len(results)*100:.1f}%", "มีการสั่งหรือรันการทดสอบ 01-10 ต.ค. 2026"),
        ("บันทึกการสั่งทดสอบแบตเตอรี่เดือนก่อน (Last Test Sep 2026)", tested_sep, f"{tested_sep/len(results)*100:.1f}%", "บันทึกล่าสุดในเดือน ก.ย. 2026"),
        ("บันทึกการสั่งทดสอบช่วงก่อนหน้า (Older Test Records)", tested_older, f"{tested_older/len(results)*100:.1f}%", "บันทึกการทดสอบเดิมก่อนเริ่มรอบปี"),
        ("", "", "", ""),
        ("สถานะแบตเตอรี่ปกติสมบูรณ์ (Healthy Battery 100%)", healthy, f"{healthy/len(results)*100:.1f}%", "ความจุ 100%, อุณหภูมิปกติ, ไร้ Alarm"),
        ("สถานะแบตเตอรี่ประจุลอยปกติ (Float Charge)", float_cnt, f"{float_cnt/len(results)*100:.1f}%", "โหมด Float ประจุเต็ม"),
        ("สถานะกำลังอยู่ในรอบทดสอบ (Planned Test)", planned_cnt, f"{planned_cnt/len(results)*100:.1f}%", "โหมดทดสอบแบตตามรอบ"),
        ("สถานีที่มี Battery Alarm แจ้งเตือน", alarms_cnt, f"{alarms_cnt/len(results)*100:.1f}%", "สัญญาณเตือนเกี่ยวกับแบตเตอรี่"),
    ]

    for r_i, s_r in enumerate(summary_data, start=4):
        for c_i, val in enumerate(s_r, start=1):
            c = ws_s.cell(row=r_i, column=c_i, value=val)
            if r_i == 4:
                c.fill = p_hdr; c.font = f_hdr; c.alignment = Alignment(horizontal="center", vertical="center")
            else:
                c.font = f_b if c_i == 1 else f_n; c.border = brd
                c.alignment = Alignment(horizontal="left" if c_i in (1, 4) else "center", vertical="center")

    for col in ws_s.columns:
        mx = max(len(str(cell.value or "")) for cell in col)
        ws_s.column_dimensions[get_column_letter(col[0].column)].width = max(mx + 4, 16)

    ws_d = wb_out.create_sheet(title="Last Battery Test Log")
    ws_d.views.sheetView[0].showGridLines = True
    hdrs = [
        "No.", "Code", "Substation Name", "Ring", "IP", "Online Status",
        "Last Batt Test Time", "Test Ctrl State", "Batt Op State",
        "Batt Cap (%)", "Batt Rating (Ah)", "Batt Curr (A)", "Batt Temp (°C)", "Backup Time (h)", "System DC (V)",
        "Tests/Year", "End Voltage (V)", "End Time (min)", "End Cap (%)", "Test Volt Level (V)",
        "Config Audit", "Battery Health", "Battery Alarms", "Total Alarms", "All Alarms List", "Error Detail"
    ]
    for c_i, h in enumerate(hdrs, start=1):
        c = ws_d.cell(row=1, column=c_i, value=h)
        c.fill = p_hdr; c.font = f_hdr; c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for r_i, r in enumerate(results, start=2):
        row_v = [
            r["No"], r["Code"], r["Name"], r["Ring"], r["IP"], r["Status"],
            r["LastTestTime"], r["BattTestControlVal"], r["BattState"],
            r["BattCapacity"], r["BattRating"], r["BattCurrent"], r["BattTemp"], r["EstimatedBackup"], r["SystemDCVoltage"],
            r["TestsPerYear"], r["EndTestVoltage"], r["EndTestTime"], r["EndTestCapacity"], r["TestVoltageLevel"],
            r["AuditConfig"], r["AuditHealth"], r["BatteryAlarms"], r["TotalAlarms"], r["AllAlarms"], r["Error"]
        ]
        for c_i, val in enumerate(row_v, start=1):
            cell = ws_d.cell(row=r_i, column=c_i, value=val)
            cell.font = f_n; cell.border = brd
            cell.alignment = Alignment(horizontal="left" if c_i in (2, 3, 23, 25, 26) else "center", vertical="center")

            if c_i == 6:
                if val == "ONLINE": cell.fill, cell.font = p_grn, f_grn
                else: cell.fill, cell.font = p_red, f_red
            elif c_i == 21:
                if val == "PASS": cell.fill, cell.font = p_grn, f_grn
                elif str(val).startswith("MISMATCH"): cell.fill, cell.font = p_yel, f_yel
                else: cell.fill, cell.font = p_red, f_red
            elif c_i == 22:
                if val == "NORMAL": cell.fill, cell.font = p_grn, f_grn
                elif str(val).startswith("WARNING"): cell.fill, cell.font = p_yel, f_yel
                else: cell.fill, cell.font = p_red, f_red

    for col in ws_d.columns:
        col_letter = get_column_letter(col[0].column)
        if col[0].column in (3, 7, 23, 25, 26):
            ws_d.column_dimensions[col_letter].width = 24
        else:
            ws_d.column_dimensions[col_letter].width = 15

    import shutil
    temp_wb = Path(r"C:\Users\Prajuktra\AppData\Local\Temp") / f"Rectifier_Last_Battery_Test_Log_All_Sites_{ts_now}.xlsx"
    wb_out.save(str(temp_wb))
    print(f"Local workbook saved: {temp_wb}")
    shutil.copyfile(str(temp_wb), str(out_file))
    print(f"Report successfully generated: {out_file}")
    latest_file = PROJECT_ROOT / "reports" / "Rectifier_Last_Battery_Test_Log_All_Sites_Latest.xlsx"
    shutil.copyfile(str(temp_wb), str(latest_file))
    print(f"Latest report copy updated: {latest_file}")

    print("\n" + "="*70)
    print("EXECUTIVE SUMMARY: LAST BATTERY TEST LOG ALL SITES")
    print("="*70)
    for title, cnt, pct, desc in summary_data:
        if title:
            print(f"{title:50} | {str(cnt):6} | {str(pct):7} | {desc}")
    print("="*70)
    print("\nSites with Recent Tests (Oct 2026):")
    for r in results:
        if r and str(r.get("LastTestTime", "")).startswith("2026-10"):
            print(f"  [{r['Code']}] {r['Name']} ({r['IP']}): Last Test={r['LastTestTime']}, State={r['BattState']}, Cap={r['BattCapacity']}%, Volt={r['SystemDCVoltage']}V")
    print("="*70)
    print("\nSites with Active Alarms or Warnings:")
    for r in results:
        if r and (r.get("BatteryAlarms") or str(r.get("AuditHealth")).startswith("WARNING") or str(r.get("AuditConfig")).startswith("MISMATCH")):
            print(f"  [{r['Code']}] {r['Name']} ({r['IP']}): Config={r['AuditConfig']}, Health={r['AuditHealth']}, Alarms={r['BatteryAlarms']}")
    print("="*70)

if __name__ == "__main__":
    main()
