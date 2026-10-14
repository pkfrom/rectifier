# -*- coding: utf-8 -*-
"""
scripts/collect_master_consolidated_live_report.py — MEA Rectifier Master Live Consolidated Collector

Consolidates ALL operational data across all 190 MEA substations into a SINGLE Excel workbook:
  1. All_Parameters_Raw     (Pivoted Matrix: 1 row per station, 221 parameter columns across 4 categories)
  2. Live_Telemetry         (DC Voltage, Current, Load, Mains, Battery, Temps, Rectifiers, Alarms, FW)
  3. Battery_Test_Logs      (Last Battery Test timestamp, Control, Planned Tests, End Test Settings, Health)
  4. Battery_Charge_Settings(Matrix of Battery Charge settings across all stations)
  5. Rectifier_Settings     (Matrix of Rectifier settings across all stations)
  6. Temperature_Settings   (Matrix of Temperature settings across all stations)
  7. System_Settings        (Matrix of System / PowerSystem settings across all stations)
  8. Hardware_Inventory     (All hardware modules: NCU, Rectifier 1/2, EIB, IB with Serial, Model, Rev)
  9. All_Parameters_List    (Long format raw key-value table: 40,000+ rows)
"""
from __future__ import annotations
import sys
import time
import json
import re
import ast
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
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
        try:
            parsed = ast.literal_eval(python_text)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
    return {}


def fetch_json(ip: str, path: str, timeout: float = 3.5) -> dict[str, Any]:
    url = f"http://{ip}{path}?_={int(time.time() * 1000)}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "MEA-Rectifier/1.0", "Cache-Control": "no-cache"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return parse_device_data(resp.read())
    except Exception:
        return {}


def parse_telemetry_num(raw: Any) -> str:
    if isinstance(raw, list) and len(raw) >= 4:
        val, alarm, unvalid, not_config = raw[0], raw[1], raw[2], raw[3]
        if unvalid == 1 or not_config == 1:
            return ""
        if isinstance(val, list) and len(val) > 0:
            val = val[0]
        val_str = str(val).strip()
        m = re.search(r"[-+]?\d+(?:\.\d+)?", val_str)
        return f"{float(m.group(0)):g}" if m else val_str
    elif isinstance(raw, list) and len(raw) > 0:
        val = raw[0]
        if isinstance(val, list) and len(val) > 0:
            val = val[0]
        val_str = str(val).strip()
        m = re.search(r"[-+]?\d+(?:\.\d+)?", val_str)
        return f"{float(m.group(0)):g}" if m else val_str
    elif isinstance(raw, (int, float)):
        return f"{raw:g}"
    elif isinstance(raw, str):
        val_str = raw.strip()
        m = re.search(r"[-+]?\d+(?:\.\d+)?", val_str)
        return f"{float(m.group(0)):g}" if m else val_str
    return ""


def parse_telemetry_text(raw: Any) -> str:
    if isinstance(raw, list) and len(raw) >= 4:
        val, alarm, unvalid, not_config = raw[0], raw[1], raw[2], raw[3]
        if unvalid == 1 or not_config == 1:
            return ""
        if isinstance(val, list) and len(val) > 0:
            val = val[0]
        return str(val).strip()
    elif isinstance(raw, list) and len(raw) > 0:
        val = raw[0]
        if isinstance(val, list) and len(val) > 0:
            val = val[0]
        return str(val).strip()
    elif raw is not None:
        return str(raw).strip()
    return ""


def interpret_param_row(item: list) -> dict[str, Any]:
    raw_name = item[0]
    name = raw_name[0] if isinstance(raw_name, list) else str(raw_name)
    eq_id = item[1] if len(item) > 1 else None
    sig_type = item[2] if len(item) > 2 else None
    sig_id = item[3] if len(item) > 3 else None
    val_type = item[8] if len(item) > 8 else None
    val = item[9] if len(item) > 9 else None
    opts = item[10] if len(item) > 10 else None

    interpreted = str(val) if val is not None else ""
    unit_str = ""

    if val_type == 5 and isinstance(opts, list):
        try:
            idx = int(val)
            if 0 <= idx < len(opts):
                o = opts[idx]
                interpreted = o[0] if isinstance(o, list) else str(o)
        except Exception:
            pass
        unit_str = "enum"
    elif val_type == 2 and isinstance(opts, str):
        unit_str = opts.strip()
    elif isinstance(opts, str):
        unit_str = opts.strip()

    return {
        "name": name.strip(),
        "raw_value": val,
        "interpreted_value": interpreted.strip(),
        "unit": unit_str,
        "val_type": val_type,
        "equip_id": eq_id,
        "sig_type": sig_type,
        "sig_id": sig_id,
    }


def collect_station_complete(site: dict[str, Any], timeout: float = 3.5) -> dict[str, Any]:
    code = site.get("code", "")
    name = site.get("name", "")
    ring = site.get("ring", "")
    no = site.get("no", "")
    ip = str(site.get("ip", "")).strip()
    collected_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    res = {
        "site": site,
        "collected_at": collected_at,
        "status": "OFFLINE",
        "error": "",
        # Dimensions
        "telemetry": {},
        "batt_test": {},
        "inventory": [],
        "settings": {
            "Battery Charge": {},
            "Rectifiers": {},
            "Temperature": {},
            "System": {}
        },
        "all_params": []
    }

    if not ip or ip.lower() in ("none", "nan", "ไม่มี", "-", ""):
        res["status"] = "NO_IP"
        res["error"] = "No IP Address"
        return res

    # 1. Fetch Endpoints Concurrently within station thread
    d_set = fetch_json(ip, "/var/datas/data.setting.html", timeout=timeout)
    d_sys = fetch_json(ip, "/var/datas/data.sys_setting.html", timeout=timeout)
    d_inv = fetch_json(ip, "/var/datas/data.system_inventory.html", timeout=timeout)
    d_idx = fetch_json(ip, "/var/datas/data.index.html", timeout=timeout)
    d_bat = fetch_json(ip, "/var/datas/data.system_battery.html", timeout=timeout)
    d_alm = fetch_json(ip, "/var/datas/data.alarms.html", timeout=timeout)
    d_rec = fetch_json(ip, "/var/datas/data.system_rectifier.html", timeout=timeout)

    # Fallback for Config v1.00 legacy
    if not d_idx:
        d_dc = fetch_json(ip, "/var/datas/data.system_dc.html", timeout=timeout)
        d_ac = fetch_json(ip, "/var/datas/data.system_ac.html", timeout=timeout)
        d_hyb = fetch_json(ip, "/var/datas/data.hybrid.html", timeout=timeout)
    else:
        d_dc, d_ac, d_hyb = {}, {}, {}

    if not d_set and not d_sys and not d_idx and not d_inv and not d_alm:
        res["status"] = "OFFLINE"
        res["error"] = "Connection Timeout / Unreachable"
        return res

    res["status"] = "ONLINE"

    # --- Dimension A: Telemetry ---
    main_content = d_idx.get("mainContent", {})
    sys_block = main_content.get("system", {})
    dc_volt = parse_telemetry_num(main_content.get("VAmeter", {}).get("value", {}).get("outer", ""))
    dc_curr = parse_telemetry_num(sys_block.get("DC", ""))
    if not dc_curr:
        dc_curr = parse_telemetry_num(main_content.get("PAmeter", {}).get("value", {}).get("inner", ""))
    if not dc_volt and d_alm.get("status"):
        dc_volt = parse_telemetry_num(d_alm["status"][0])
    if not dc_volt and d_dc.get("group", {}).get("list"):
        for item in d_dc["group"]["list"]:
            if isinstance(item, list) and len(item) >= 2 and "voltage" in str(item[0]).lower():
                dc_volt = parse_telemetry_num(item[1])
                break

    mains = sys_block.get("Mains", [])
    ac_curr = sys_block.get("ACCurrent", [])
    ac_v_a = parse_telemetry_num(mains[0]) if len(mains) > 0 else ""
    ac_v_b = parse_telemetry_num(mains[1]) if len(mains) > 1 else ""
    ac_v_c = parse_telemetry_num(mains[2]) if len(mains) > 2 else ""
    ac_i_a = parse_telemetry_num(ac_curr[0]) if len(ac_curr) > 0 else ""
    ac_i_b = parse_telemetry_num(ac_curr[1]) if len(ac_curr) > 1 else ""
    ac_i_c = parse_telemetry_num(ac_curr[2]) if len(ac_curr) > 2 else ""

    batt_stat = parse_telemetry_text(sys_block.get("Battery_status", ""))
    batt_curr = parse_telemetry_num(sys_block.get("Battery", ""))
    batt_cap = parse_telemetry_num(sys_block.get("BATT_CAPACITY", ""))
    batt_chart = d_bat.get("group", {}).get("chart", {})
    batt_temp = parse_telemetry_num(batt_chart.get("Battery_Temperature", ""))
    batt_backup = parse_telemetry_num(batt_chart.get("Estimated_Remaining_Time", ""))
    if not batt_stat and d_bat.get("group", {}).get("list"):
        for itm in d_bat["group"]["list"]:
            if isinstance(itm, list) and len(itm) >= 2 and "management state" in str(itm[0]).lower():
                batt_stat = parse_telemetry_text(itm[1])
                break

    amb_temp = parse_telemetry_num(main_content.get("drawThermometer", {}).get("value", ""))

    # Rectifiers block
    rect_chart = d_rec.get("group", {}).get("chart", {})
    rect_curr = parse_telemetry_num(rect_chart.get("curr", ""))
    rect_cap = parse_telemetry_num(rect_chart.get("used_cap", ""))
    rect_list = d_rec.get("group", {}).get("list", [])
    rect_count = 0
    for itm in rect_list:
        if isinstance(itm, list) and len(itm) >= 2 and "rectifiers" in str(itm[0]).lower():
            rect_count = parse_telemetry_num(itm[1])

    # Controller HW/SW from inventory
    ctrl_model, ctrl_serial, ctrl_hw, ctrl_sw, ctrl_cfg = "", "", "", "", ""
    raw_inv = d_inv.get("inventory", [])
    for inv_item in raw_inv:
        if isinstance(inv_item, list) and len(inv_item) >= 5:
            eq_name = str(inv_item[0]).strip()
            if "NCU" in eq_name or "M830B" in eq_name:
                ctrl_model = str(inv_item[1]).strip()
                ctrl_hw = str(inv_item[2]).strip()
                ctrl_serial = str(inv_item[3]).strip()
                ctrl_sw = str(inv_item[4]).strip()
            res["inventory"].append({
                "equipment": eq_name,
                "model": str(inv_item[1]).strip(),
                "hw_rev": str(inv_item[2]).strip(),
                "serial": str(inv_item[3]).strip(),
                "sw_rev": str(inv_item[4]).strip(),
            })

    sider_data = d_idx.get("sider", {}).get("system", [])
    if isinstance(sider_data, list) and len(sider_data) >= 5:
        if not ctrl_model: ctrl_model = str(sider_data[0]).strip()
        if not ctrl_serial: ctrl_serial = str(sider_data[1]).strip()
        if not ctrl_hw: ctrl_hw = str(sider_data[2]).strip()
        if not ctrl_sw: ctrl_sw = str(sider_data[3]).strip()
        if not ctrl_cfg: ctrl_cfg = str(sider_data[4]).strip()

    # Alarms
    all_alarms_cnt = d_alm.get("AllAlarms", 0)
    alm_strs = []
    for a in d_alm.get("Content", []):
        alm_strs.append(str(a[0] if isinstance(a, list) and a else a))

    res["telemetry"] = {
        "dc_voltage": dc_volt,
        "dc_current": dc_curr,
        "ac_v_a": ac_v_a,
        "ac_v_b": ac_v_b,
        "ac_v_c": ac_v_c,
        "ac_i_a": ac_i_a,
        "ac_i_b": ac_i_b,
        "ac_i_c": ac_i_c,
        "battery_status": batt_stat,
        "battery_current": batt_curr,
        "battery_capacity": batt_cap,
        "battery_temp": batt_temp,
        "estimated_backup": batt_backup,
        "ambient_temp": amb_temp,
        "rectifier_count": rect_count,
        "rectifier_current": rect_curr,
        "rectifier_used_capacity": rect_cap,
        "all_alarms_count": all_alarms_cnt,
        "alarms_summary": "; ".join(alm_strs[:5]),
        "ctrl_model": ctrl_model,
        "ctrl_serial": ctrl_serial,
        "ctrl_hw": ctrl_hw,
        "ctrl_sw": ctrl_sw,
        "ctrl_cfg": ctrl_cfg,
    }

    # --- Dimension B: Battery Test Logs ---
    bt_ctrl, bt_ts, bt_time_str = "", 0, ""
    bt_tests_yr, bt_end_v, bt_end_t, bt_end_cap, bt_level = "", "", "", "", ""

    batt_test_list = d_set.get("BATT_TEST", {}).get("list", [])
    for itm in batt_test_list:
        if isinstance(itm, list) and len(itm) >= 10:
            nm = itm[0][0] if isinstance(itm[0], list) else str(itm[0])
            nm = nm.strip()
            ts = itm[5] if len(itm) > 5 else 0
            val = itm[9]
            if nm == "Battery Test Control":
                bt_ctrl = str(val)
                bt_ts = ts
                if ts and ts > 0:
                    bt_time_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
            elif nm == "Number of Planned Tests per Year":
                bt_tests_yr = str(val)
            elif nm == "End Test Voltage":
                bt_end_v = str(val)
            elif nm == "End Test Time":
                bt_end_t = str(val)
            elif nm == "End Test Capacity":
                bt_end_cap = str(val)
            elif nm == "Test Voltage Level":
                bt_level = str(val)

    # Battery Health Assessment
    b_health = "NORMAL"
    try:
        f_volt = float(dc_volt) if dc_volt else 0.0
        f_temp = float(batt_temp) if batt_temp else 0.0
        f_cap = float(batt_cap) if batt_cap else 100.0
        if f_temp >= 40.0:
            b_health = "HIGH TEMP"
        elif f_cap < 70.0:
            b_health = "LOW CAPACITY"
        elif f_volt > 0 and f_volt < 48.0:
            b_health = "LOW VOLTAGE"
    except Exception:
        pass

    res["batt_test"] = {
        "last_test_time": bt_time_str,
        "test_control": bt_ctrl,
        "tests_per_year": bt_tests_yr,
        "end_test_voltage": bt_end_v,
        "end_test_time": bt_end_t,
        "end_test_capacity": bt_end_cap,
        "test_voltage_level": bt_level,
        "batt_temp": batt_temp,
        "batt_capacity": batt_cap,
        "health_assessment": b_health,
    }

    # --- Dimension C & D: Settings Parameters ---
    cat_map = {
        "CHARGE": "Battery Charge",
        "RECT": "Rectifiers",
        "TEMPERATURE": "Temperature"
    }

    for src_key, target_cat in cat_map.items():
        sub_list = d_set.get(src_key, {}).get("list", [])
        for item in sub_list:
            if isinstance(item, list) and len(item) >= 10:
                parsed = interpret_param_row(item)
                p_name = parsed["name"]
                res["settings"][target_cat][p_name] = parsed["interpreted_value"]
                res["all_params"].append({
                    "category": target_cat,
                    **parsed
                })

    ps = d_sys.get("PowerSystem", {})
    def walk_sys(node, group_label=""):
        if isinstance(node, dict):
            for k, v in node.items():
                lbl = k[0] if isinstance(k, list) else str(k)
                walk_sys(v, lbl)
        elif isinstance(node, list):
            for itm in node:
                if isinstance(itm, list) and len(itm) >= 10 and isinstance(itm[1], int) and isinstance(itm[2], int):
                    parsed = interpret_param_row(itm)
                    p_name = parsed["name"]
                    res["settings"]["System"][p_name] = parsed["interpreted_value"]
                    res["all_params"].append({
                        "category": "System",
                        **parsed
                    })
                elif isinstance(itm, (dict, list)):
                    walk_sys(itm, group_label)

    walk_sys(ps)

    return res


def main():
    print("=" * 80)
    print("MEA RECTIFIER CONSOLIDATED MASTER LIVE COLLECTOR (ALL SITES)")
    print("Telemetry | Battery Test | Hardware Inventory | Complete Settings Matrix")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # 1. Load Station List
    excel_path = PROJECT_ROOT / "Rectifier.xlsx"
    if not excel_path.exists():
        print(f"[-] Rectifier.xlsx not found at {excel_path}")
        return

    wb_in = openpyxl.load_workbook(excel_path, read_only=True)
    ws_in = wb_in.active

    sites = []
    for row in ws_in.iter_rows(values_only=True):
        if not row or not row[0] or str(row[0]).strip().lower() in ("ชื่อย่อ", "code", "station"):
            continue
        code = str(row[0]).strip()
        name = str(row[1]).strip() if len(row) > 1 and row[1] is not None else ""
        ring = str(row[2]).strip() if len(row) > 2 and row[2] is not None else ""
        no = str(row[3]).strip() if len(row) > 3 and row[3] is not None else ""
        ip = str(row[4]).strip() if len(row) > 4 and row[4] is not None else ""
        sites.append({"code": code, "name": name, "ring": ring, "no": no, "ip": ip})
    wb_in.close()

    print(f"[*] Loaded {len(sites)} stations from Rectifier.xlsx")
    print(f"[*] Launching concurrent live collectors (workers=25, timeout=3.5s)...")

    t_start = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=25) as executor:
        future_to_site = {executor.submit(collect_station_complete, s): s for s in sites}
        for future in as_completed(future_to_site):
            results.append(future.result())

    # Sort results by original site order
    site_order = {s["code"]: idx for idx, s in enumerate(sites)}
    results.sort(key=lambda r: site_order.get(r["site"]["code"], 999))

    elapsed = time.time() - t_start
    online_count = sum(1 for r in results if r["status"] == "ONLINE")
    offline_count = sum(1 for r in results if r["status"] == "OFFLINE")
    no_ip_count = sum(1 for r in results if r["status"] == "NO_IP")

    print(f"\n[+] Live extraction completed in {elapsed:.2f} seconds!")
    print(f"    - Online  : {online_count}/{len(sites)}")
    print(f"    - Offline : {offline_count}")
    print(f"    - No IP   : {no_ip_count}\n")

    # 2. Build Master Excel Workbook
    wb = openpyxl.Workbook()
    wb.remove(wb.active) # Remove default sheet

    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    fill_brand_orange = PatternFill(start_color="F26522", end_color="F26522", fill_type="solid") # MEA Orange
    fill_navy = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")         # Navy Blue
    fill_steel_blue = PatternFill(start_color="2E75B6", end_color="2E75B6", fill_type="solid")   # Steel Blue
    fill_green = PatternFill(start_color="375623", end_color="375623", fill_type="solid")        # Forest Green
    fill_gray = PatternFill(start_color="595959", end_color="595959", fill_type="solid")          # Charcoal Gray
    thin_border = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9")
    )

    base_cols = ["No.", "Code", "Station Name", "Ring", "IP", "Status"]

    # Gather all unique parameters per category
    cat_keys = ["Battery Charge", "Rectifiers", "Temperature", "System"]
    sorted_cat_params = {c: sorted(list({p for r in results if r["status"] == "ONLINE" for p in r["settings"].get(c, {}).keys()})) for c in cat_keys}

    cat_fills = {
        "Battery Charge": fill_brand_orange,
        "Rectifiers": fill_steel_blue,
        "Temperature": fill_green,
        "System": fill_gray
    }

    # =========================================================================
    # TAB 1: All_Parameters_Raw (PIVOTED MATRIX: 1 ROW PER STATION)
    # =========================================================================
    print("[*] Generating Sheet 1: All_Parameters_Raw (Pivoted Matrix)...")
    ws_all_pivoted = wb.create_sheet(title="All_Parameters_Raw")

    all_cat_param_pairs = []
    for c in cat_keys:
        for p in sorted_cat_params[c]:
            all_cat_param_pairs.append((c, p))

    all_pivoted_headers = base_cols + [f"[{c}] {p}" for c, p in all_cat_param_pairs]
    ws_all_pivoted.append(all_pivoted_headers)

    for col_idx in range(1, len(base_cols) + 1):
        cell = ws_all_pivoted.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = fill_navy
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for idx, (c, p) in enumerate(all_cat_param_pairs, start=len(base_cols) + 1):
        cell = ws_all_pivoted.cell(row=1, column=idx)
        cell.font = header_font
        cell.fill = cat_fills.get(c, fill_navy)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for r_idx, r in enumerate(results, start=2):
        s = r["site"]
        row_data = [
            s.get("no", ""),
            s.get("code", ""),
            s.get("name", ""),
            s.get("ring", ""),
            s.get("ip", ""),
            r["status"]
        ]
        s_dict = r.get("settings", {}) if r["status"] == "ONLINE" else {}
        for c, p in all_cat_param_pairs:
            row_data.append(s_dict.get(c, {}).get(p, "-"))
        ws_all_pivoted.append(row_data)

        for col_idx in range(1, len(all_pivoted_headers) + 1):
            cell = ws_all_pivoted.cell(row=r_idx, column=col_idx)
            cell.border = thin_border
            if col_idx in [1, 2, 4, 6]:
                cell.alignment = Alignment(horizontal="center")

    ws_all_pivoted.freeze_panes = "G2"
    ws_all_pivoted.auto_filter.ref = ws_all_pivoted.dimensions
    for col in ws_all_pivoted.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = max(len(str(cell.value or "")) for cell in col[:15])
        ws_all_pivoted.column_dimensions[col_letter].width = max(max_len + 3, 13)

    # =========================================================================
    # TAB 2: Live_Telemetry (Voltages, Currents, Temps, Alarms, FW/HW)
    # =========================================================================
    print("[*] Generating Sheet 2: Live_Telemetry...")
    ws_telem = wb.create_sheet(title="Live_Telemetry")
    telem_headers = base_cols + [
        "DC Voltage (V)", "DC Load Current (A)",
        "AC Volt Phase A (V)", "AC Volt Phase B (V)", "AC Volt Phase C (V)",
        "AC Curr Phase A (A)", "AC Curr Phase B (A)", "AC Curr Phase C (A)",
        "Battery Status", "Battery Current (A)", "Battery Capacity (%)", "Battery Temp (°C)", "Backup Est. (h)",
        "Ambient Temp (°C)", "Rectifier Modules", "Rectifier Current (A)", "Rectifier Used Cap (%)",
        "Active Alarms Count", "Alarms Summary",
        "Controller Model", "Serial Number", "HW Version", "SW Version", "Config Version"
    ]
    ws_telem.append(telem_headers)
    for col_idx in range(1, len(telem_headers) + 1):
        cell = ws_telem.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = fill_brand_orange
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for r_idx, r in enumerate(results, start=2):
        s = r["site"]
        t = r["telemetry"]
        row_data = [
            s.get("no", ""), s.get("code", ""), s.get("name", ""), s.get("ring", ""), s.get("ip", ""), r["status"],
            t.get("dc_voltage", ""), t.get("dc_current", ""),
            t.get("ac_v_a", ""), t.get("ac_v_b", ""), t.get("ac_v_c", ""),
            t.get("ac_i_a", ""), t.get("ac_i_b", ""), t.get("ac_i_c", ""),
            t.get("battery_status", ""), t.get("battery_current", ""), t.get("battery_capacity", ""), t.get("battery_temp", ""), t.get("estimated_backup", ""),
            t.get("ambient_temp", ""), t.get("rectifier_count", ""), t.get("rectifier_current", ""), t.get("rectifier_used_capacity", ""),
            t.get("all_alarms_count", ""), t.get("alarms_summary", ""),
            t.get("ctrl_model", ""), t.get("ctrl_serial", ""), t.get("ctrl_hw", ""), t.get("ctrl_sw", ""), t.get("ctrl_cfg", "")
        ]
        ws_telem.append(row_data)
        for col_idx in range(1, len(telem_headers) + 1):
            cell = ws_telem.cell(row=r_idx, column=col_idx)
            cell.border = thin_border
            if col_idx in [1, 2, 4, 6, 7, 8, 15, 17, 18, 20]:
                cell.alignment = Alignment(horizontal="center")

    ws_telem.freeze_panes = "G2"
    ws_telem.auto_filter.ref = ws_telem.dimensions
    for col in ws_telem.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = max(len(str(cell.value or "")) for cell in col[:15])
        ws_telem.column_dimensions[col_letter].width = max(max_len + 3, 12)

    # =========================================================================
    # TAB 3: Battery_Test_Logs (History & Health)
    # =========================================================================
    print("[*] Generating Sheet 3: Battery_Test_Logs...")
    ws_bt = wb.create_sheet(title="Battery_Test_Logs")
    bt_headers = base_cols + [
        "Last Test Time", "Test Control Status", "Planned Tests / Year",
        "End Test Voltage (V)", "End Test Time (min)", "End Test Capacity (%)", "Test Voltage Level (V)",
        "Battery Temp (°C)", "Battery Capacity (%)", "Health Assessment"
    ]
    ws_bt.append(bt_headers)
    for col_idx in range(1, len(bt_headers) + 1):
        cell = ws_bt.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = fill_steel_blue
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for r_idx, r in enumerate(results, start=2):
        s = r["site"]
        b = r["batt_test"]
        row_data = [
            s.get("no", ""), s.get("code", ""), s.get("name", ""), s.get("ring", ""), s.get("ip", ""), r["status"],
            b.get("last_test_time", ""), b.get("test_control", ""), b.get("tests_per_year", ""),
            b.get("end_test_voltage", ""), b.get("end_test_time", ""), b.get("end_test_capacity", ""), b.get("test_voltage_level", ""),
            b.get("batt_temp", ""), b.get("batt_capacity", ""), b.get("health_assessment", "")
        ]
        ws_bt.append(row_data)
        for col_idx in range(1, len(bt_headers) + 1):
            cell = ws_bt.cell(row=r_idx, column=col_idx)
            cell.border = thin_border
            if col_idx in [1, 2, 4, 6, 7, 8, 9, 16]:
                cell.alignment = Alignment(horizontal="center")

    ws_bt.freeze_panes = "G2"
    ws_bt.auto_filter.ref = ws_bt.dimensions
    for col in ws_bt.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = max(len(str(cell.value or "")) for cell in col[:15])
        ws_bt.column_dimensions[col_letter].width = max(max_len + 3, 14)

    # =========================================================================
    # TABS 4-7: Individual Category Matrices
    # =========================================================================
    def build_matrix_sheet(sheet_title: str, category_name: str, fill_style):
        print(f"[*] Generating Sheet: {sheet_title}...")
        ws = wb.create_sheet(title=sheet_title)
        p_list = sorted_cat_params[category_name]
        headers = base_cols + p_list
        ws.append(headers)

        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = fill_style
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        for r_idx, r in enumerate(results, start=2):
            s = r["site"]
            row_data = [
                s.get("no", ""), s.get("code", ""), s.get("name", ""), s.get("ring", ""), s.get("ip", ""), r["status"]
            ]
            c_dict = r["settings"].get(category_name, {}) if r["status"] == "ONLINE" else {}
            for p in p_list:
                row_data.append(c_dict.get(p, "-"))
            ws.append(row_data)

            for col_idx in range(1, len(headers) + 1):
                cell = ws.cell(row=r_idx, column=col_idx)
                cell.border = thin_border
                if col_idx in [1, 2, 4, 6]:
                    cell.alignment = Alignment(horizontal="center")

        ws.freeze_panes = "G2"
        ws.auto_filter.ref = ws.dimensions
        for col in ws.columns:
            col_letter = get_column_letter(col[0].column)
            max_len = max(len(str(cell.value or "")) for cell in col[:15])
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    build_matrix_sheet("Battery_Charge_Settings", "Battery Charge", fill_brand_orange)
    build_matrix_sheet("Rectifier_Settings", "Rectifiers", fill_steel_blue)
    build_matrix_sheet("Temperature_Settings", "Temperature", fill_green)
    build_matrix_sheet("System_Settings", "System", fill_gray)

    # =========================================================================
    # TAB 8: Hardware_Inventory (Modules per station)
    # =========================================================================
    print("[*] Generating Sheet 8: Hardware_Inventory...")
    ws_inv = wb.create_sheet(title="Hardware_Inventory")
    inv_headers = ["No.", "Code", "Station Name", "Ring", "IP", "Equipment", "Product Model", "HW Revision", "Serial Number", "SW Revision"]
    ws_inv.append(inv_headers)
    for col_idx in range(1, len(inv_headers) + 1):
        cell = ws_inv.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = fill_navy
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for r in results:
        s = r["site"]
        if r["status"] == "ONLINE":
            for itm in r["inventory"]:
                ws_inv.append([
                    s.get("no", ""), s.get("code", ""), s.get("name", ""), s.get("ring", ""), s.get("ip", ""),
                    itm.get("equipment", ""), itm.get("model", ""), itm.get("hw_rev", ""), itm.get("serial", ""), itm.get("sw_rev", "")
                ])

    ws_inv.freeze_panes = "A2"
    ws_inv.auto_filter.ref = ws_inv.dimensions
    for col in ws_inv.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = max(len(str(cell.value or "")) for cell in col[:15])
        ws_inv.column_dimensions[col_letter].width = max(max_len + 3, 12)

    # =========================================================================
    # TAB 9: All_Parameters_List (Long Format Raw Dump)
    # =========================================================================
    print("[*] Generating Sheet 9: All_Parameters_List...")
    ws_long = wb.create_sheet(title="All_Parameters_List")
    long_headers = [
        "No.", "Code", "Station Name", "Ring", "IP",
        "Category", "Parameter Name", "Value", "Unit / Type",
        "Raw Value", "Value Type", "Equip ID", "Signal Type", "Signal ID"
    ]
    ws_long.append(long_headers)
    for col_idx in range(1, len(long_headers) + 1):
        cell = ws_long.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = fill_brand_orange
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for r in results:
        s = r["site"]
        if r["status"] == "ONLINE":
            for p in r["all_params"]:
                ws_long.append([
                    s.get("no", ""), s.get("code", ""), s.get("name", ""), s.get("ring", ""), s.get("ip", ""),
                    p.get("category", ""), p.get("name", ""), p.get("interpreted_value", ""), p.get("unit", ""),
                    p.get("raw_value", ""), p.get("val_type", ""), p.get("equip_id", ""), p.get("sig_type", ""), p.get("sig_id", "")
                ])

    ws_long.freeze_panes = "A2"
    ws_long.auto_filter.ref = ws_long.dimensions
    for col in ws_long.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = max(len(str(cell.value or "")) for cell in col[:15])
        ws_long.column_dimensions[col_letter].width = max(max_len + 3, 12)

    # =========================================================================
    # 3. Save Master Excel Report
    # =========================================================================
    ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    reports_dir = PROJECT_ROOT / "reports"
    archive_dir = reports_dir / "archive"
    reports_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)

    out_latest = reports_dir / "Rectifier_Master_Consolidated_All_Sites_Latest.xlsx"
    out_archive = archive_dir / f"Rectifier_Master_Consolidated_All_Sites_{ts_str}.xlsx"

    temp_wb_path = Path(r"C:\Users\Prajuktra\AppData\Local\Temp") / f"master_consolidated_{ts_str}.xlsx"
    print(f"[*] Saving master workbook to temporary path: {temp_wb_path}...")
    wb.save(temp_wb_path)
    wb.close()

    import shutil
    shutil.copyfile(temp_wb_path, out_latest)
    shutil.copyfile(temp_wb_path, out_archive)

    print("\n" + "=" * 80)
    print(f"[+] CONSOLIDATED MASTER REPORT SAVED SUCCESSFULLY:")
    print(f"    - Latest  : {out_latest}")
    print(f"    - Archive : {out_archive}")
    print("=" * 80)


if __name__ == "__main__":
    main()
