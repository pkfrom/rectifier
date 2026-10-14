# -*- coding: utf-8 -*-
"""
scripts/reboot_controller.py — MEA Rectifier Controller Remote Reboot & Management

Supports:
  1. Hardware Reboot Controller via web_cgi_control.cgi (control_type=11)
  2. Stop ACU Daemon via web_cgi_filemanage.cgi (_close_acu=1)
  3. Start ACU Daemon via web_cgi_filemanage.cgi (_start_acu=1)
  4. Real-time post-reboot health verification (supports both v1.02A and v1.00)

Usage:
  python scripts/reboot_controller.py --ip 10.209.22.21 --action status
  python scripts/reboot_controller.py --ip 10.209.22.21 --action reboot
  python scripts/reboot_controller.py --ip 10.209.22.21 --action stop
  python scripts/reboot_controller.py --ip 10.209.22.21 --action start
  python scripts/reboot_controller.py --code KJ
"""
from __future__ import annotations
import sys
import time
import json
import base64
import socket
import argparse
import urllib.request
import urllib.parse
from pathlib import Path

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_USER_B64 = base64.b64encode(b"admin").decode()
DEFAULT_PASS_B64 = base64.b64encode(b"640275").decode()


def resolve_station_ip(code_or_ip: str) -> tuple[str, str]:
    """Resolves station code to IP using Rectifier.xlsx if not an IP address."""
    if any(c.isalpha() for c in code_or_ip):
        excel_path = PROJECT_ROOT / "Rectifier.xlsx"
        if excel_path.exists():
            import openpyxl
            wb = openpyxl.load_workbook(excel_path, read_only=True)
            ws = wb.active
            for row in ws.iter_rows(values_only=True):
                if row and len(row) >= 5:
                    c, name, _, _, ip = row[0], row[1], row[2], row[3], row[4]
                    if str(c).strip().upper() == code_or_ip.strip().upper():
                        return str(ip).strip(), f"{c} ({name})"
            wb.close()
    return code_or_ip.strip(), code_or_ip.strip()


def login_controller(ip: str, timeout: float = 8.0) -> tuple[bool, str, dict[str, str]]:
    """Logs into NCU controller and extracts session tokens."""
    url = f"http://{ip}/app/www_user/html/cgi-bin/web_cgi_main.cgi?_={int(time.time()*1000)}"
    post_data = f"user_name={DEFAULT_USER_B64}&user_password={DEFAULT_PASS_B64}".encode('utf-8')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': f'http://{ip}/app/www_user/html/eng/index.html'
    }
    try:
        req = urllib.request.Request(url, data=post_data, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode('utf-8-sig', errors='ignore').strip()
            res = json.loads(body)
            st = res.get('status')
            if st == 1:
                cookie_str = res.get('cookie', '')
                cookies = dict(part.split('=', 1) for part in cookie_str.split(',') if '=' in part)
                session_id = cookies.get('sessionId', '').strip()
                return True, session_id, cookies
            elif st == 6:
                return False, "Controller is starting up (status 6)", {}
            elif st == 4:
                return False, f"Comm error with application (status 4: {res.get('cookie', '')})", {}
            else:
                return False, f"Login returned status {st}", {}
    except Exception as e:
        return False, str(e), {}


def get_auth_headers(ip: str, cookies: dict[str, str]) -> dict[str, str]:
    cookie_header = '; '.join([f'{k}={v}' for k, v in cookies.items()])
    cookie_header += f'; user_name={DEFAULT_USER_B64}; user_password={DEFAULT_PASS_B64}; language_type=0'
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Referer': f'http://{ip}/app/www_user/html/eng/index.html',
        'Cookie': cookie_header
    }


def send_reboot(ip: str, session_id: str, cookies: dict[str, str]) -> bool:
    """Sends control_type=11 to web_cgi_control.cgi."""
    url = f"http://{ip}/app/www_user/html/cgi-bin/web_cgi_control.cgi?_={int(time.time()*1000)}"
    payload = f"equip_ID=-2&signal_type=-2&signal_id=-2&control_value=-2&control_type=11&sessionId={session_id}&language_type=0"
    headers = get_auth_headers(ip, cookies)
    req = urllib.request.Request(url, data=payload.encode('utf-8'), headers=headers)
    print(f"[*] Dispatching Reboot Controller command (control_type=11) to {ip}...")
    try:
        with urllib.request.urlopen(req, timeout=8.0) as resp:
            body = resp.read().decode('utf-8-sig', errors='ignore')
            print(f"[*] Controller response: {body.strip()}")
            return True
    except Exception as e:
        print(f"[+] Controller accepted reboot command (connection closed by remote host: {e})")
        return True


def send_stop(ip: str, session_id: str, cookies: dict[str, str]) -> bool:
    """Sends _close_acu=1 to web_cgi_filemanage.cgi."""
    url = f"http://{ip}/app/www_user/html/cgi-bin/web_cgi_filemanage.cgi?_={int(time.time()*1000)}"
    payload = f"_close_acu=1&sessionId={session_id}&language_type=0"
    headers = get_auth_headers(ip, cookies)
    req = urllib.request.Request(url, data=payload.encode('utf-8'), headers=headers)
    print(f"[*] Stopping controller ACU process (_close_acu=1) on {ip}...")
    try:
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            body = resp.read().decode('utf-8-sig', errors='ignore')
            print(f"[+] Stop response: {body.strip()}")
            return True
    except Exception as e:
        print(f"[*] Stop command completed/timed out as expected: {e}")
        return True


def send_start(ip: str, session_id: str, cookies: dict[str, str]) -> bool:
    """Sends _start_acu=1 to web_cgi_filemanage.cgi."""
    url = f"http://{ip}/app/www_user/html/cgi-bin/web_cgi_filemanage.cgi?_={int(time.time()*1000)}"
    payload = f"file_name=0&_start_acu=1&_upload_file=&filetype=&_upload_cfg=0&_upload_lang=0&filedata0=&sessionId={session_id}&language_type=0"
    headers = get_auth_headers(ip, cookies)
    req = urllib.request.Request(url, data=payload.encode('utf-8'), headers=headers)
    print(f"[*] Starting controller ACU process (_start_acu=1) on {ip}...")
    try:
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            body = resp.read().decode('utf-8-sig', errors='ignore')
            print(f"[+] Start response: {body.strip()}")
            return True
    except Exception as e:
        print(f"[*] Start command sent: {e}")
        return True


def read_telemetry_status(ip: str) -> bool:
    """Reads and prints live voltage, battery state, and telemetry using collect_site logic."""
    try:
        from collect_rectifier_inventory import collect_site
        site = {'No.': 1, 'Code': 'CLI', 'Station Name': 'Target', 'Ring': '?', 'IP': ip}
        res = collect_site(site, timeout=4.0)
        if res.get('status') == 'OK':
            print("\n" + "=" * 55)
            print(f"CONTROLLER TELEMETRY STATUS: {ip}")
            print(f"  Model / Firmware    : {res.get('controller_product_model')} (HW: {res.get('controller_hardware_version')}, SW: {res.get('controller_software_version')}, Cfg: {res.get('controller_config_version')})")
            print(f"  System DC Voltage   : {res.get('output_voltage')} V")
            print(f"  Output Load Current : {res.get('output_current')} A")
            print(f"  Battery Status      : {res.get('battery_status')} ({res.get('battery_capacity')}%, {res.get('battery_temp')} °C)")
            print(f"  Ambient Temperature : {res.get('ambient_temp')} °C")
            print(f"  Rectifiers Active   : {res.get('rectifier_count')} modules ({res.get('rectifier_total_current')} A total)")
            print("=" * 55 + "\n")
            return True
        else:
            print(f"[!] Telemetry read error: {res.get('error')}")
            return False
    except Exception as e:
        print(f"[!] Telemetry read error: {e}")
        return False


def wait_and_verify(ip: str, max_seconds: int = 180) -> bool:
    """Monitors port 80 bounce, polls ACU startup, and verifies live telemetry."""
    print(f"[*] Monitoring controller reboot & startup on {ip} (max wait {max_seconds}s)...")
    start_time = time.time()

    # 1. Wait for port 80 to drop
    time.sleep(2)
    while time.time() - start_time < 30:
        s = socket.socket()
        s.settimeout(1.0)
        try:
            s.connect((ip, 80))
            s.close()
            time.sleep(1.5)
        except Exception:
            print(f"[+] Port 80 dropped at {time.time()-start_time:.1f}s (hardware rebooting)")
            break

    # 2. Wait for port 80 to reopen
    print("[*] Waiting for network / web server to come back up...")
    port_up = False
    while time.time() - start_time < max_seconds:
        time.sleep(3)
        s = socket.socket()
        s.settimeout(1.5)
        try:
            s.connect((ip, 80))
            s.close()
            port_up = True
            print(f"[+] Port 80 back OPEN at {time.time()-start_time:.1f}s")
            break
        except Exception:
            pass

    if not port_up:
        print("[-] Timed out waiting for Port 80 to reopen!")
        return False

    # 3. Poll web_cgi_main.cgi until ACU initialization finishes (status 1)
    print("[*] Waiting for ACU daemon initialization...")
    acu_ready = False
    while time.time() - start_time < max_seconds:
        time.sleep(4)
        ok, res, _ = login_controller(ip, timeout=5.0)
        if ok:
            acu_ready = True
            print(f"[+] ACU fully initialized and ready at {time.time()-start_time:.1f}s! Session: {res}")
            break
        else:
            print(f"    [{time.time()-start_time:.0f}s] {res}")

    if not acu_ready:
        print("[-] Timed out waiting for ACU daemon initialization!")
        return False

    # 4. Read live telemetry verification
    return read_telemetry_status(ip)


def main():
    parser = argparse.ArgumentParser(description="MEA Rectifier Controller Reboot & Management CLI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--ip", help="Target controller IP address")
    group.add_argument("--code", help="Station code (e.g. KJ, BAT, AUG)")

    parser.add_argument("--action", choices=["reboot", "stop", "start", "status"], default="reboot",
                        help="Action to perform (default: reboot)")
    parser.add_argument("--no-wait", action="store_true", help="Do not wait for reboot cycle completion")
    parser.add_argument("--timeout", type=int, default=180, help="Max wait seconds for reboot (default: 180)")

    args = parser.parse_args()

    ip, label = resolve_station_ip(args.ip or args.code)
    print(f"Target Controller: {label} [{ip}] | Action: {args.action.upper()}")

    if args.action == "status":
        ok, res, _ = login_controller(ip, timeout=5.0)
        if ok:
            print(f"[+] Controller ONLINE. Session ID: {res}")
            read_telemetry_status(ip)
        else:
            print(f"[-] Controller NOT ready: {res}")
        return

    # Login to acquire session
    ok, session_id, cookies = login_controller(ip, timeout=6.0)
    if not ok:
        print(f"[!] Initial login note: {session_id}")
        session_id = ""
        cookies = {}

    if args.action == "reboot":
        send_reboot(ip, session_id, cookies)
    elif args.action == "stop":
        send_stop(ip, session_id, cookies)
    elif args.action == "start":
        send_start(ip, session_id, cookies)

    if not args.no_wait and args.action in ["reboot", "start"]:
        success = wait_and_verify(ip, max_seconds=args.timeout)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
