import openpyxl
from pathlib import Path
from collect_rectifier_inventory import get_json, extract_settings_dict
from datetime import datetime

base_dir = Path(__file__).resolve().parent.parent
reports_dir = base_dir / "reports"
wb_path = (reports_dir / "Rectifier_Abnormal_Report_Latest.xlsx") if (reports_dir / "Rectifier_Abnormal_Report_Latest.xlsx").exists() else (reports_dir / "Rectifier_Abnormal_Report.xlsx")
wb = openpyxl.load_workbook(wb_path)

stations_to_update = {
    "AUG": "10.209.30.21",
    "KP": "10.209.8.21",
    "RTR": "10.209.51.21",
    "SYI": "10.209.186.21"
}

# Update Settings sheet in Rectifier_Abnormal_Report_Latest.xlsx
ws_settings = wb["Settings Audit"]

# Find column index for "Equalize Charge Voltage (V)"
col_eq = None
for col in range(1, ws_settings.max_column + 1):
    header = ws_settings.cell(row=1, column=col).value
    if header and "Equalize Charge Voltage" in str(header):
        col_eq = col
        break

print("Equalize col index:", col_eq)

if col_eq:
    for row in range(2, ws_settings.max_row + 1):
        code = str(ws_settings.cell(row=row, column=2).value or "").strip()
        if code in stations_to_update:
            old_v = ws_settings.cell(row=row, column=col_eq).value
            ws_settings.cell(row=row, column=col_eq, value=53.6)
            # Remove highlight fill if abnormal
            ws_settings.cell(row=row, column=col_eq).fill = openpyxl.styles.PatternFill(fill_type=None)
            print(f"Updated {code} row {row}: {old_v} -> 53.6")

# Check Executive Summary sheet in workbook
if "Executive Summary" in wb.sheetnames:
    ws_summary = wb["Executive Summary"]
    # Update note or abnormal count if present
    print("Executive Summary present")

wb.save(str(wb_path))
print(f"Saved {wb_path} successfully")

# Also update Rectifier_Inventory_188_Sites.xlsx
inv_path = reports_dir / "Rectifier_Inventory_188_Sites.xlsx"
wb_inv = openpyxl.load_workbook(str(inv_path))
if "Settings" in wb_inv.sheetnames:
    ws_inv_set = wb_inv["Settings"]
    inv_col_eq = None
    for col in range(1, ws_inv_set.max_column + 1):
        header = ws_inv_set.cell(row=1, column=col).value
        if header and "Equalize Charge Voltage" in str(header):
            inv_col_eq = col
            break
    if inv_col_eq:
        for row in range(2, ws_inv_set.max_row + 1):
            code = str(ws_inv_set.cell(row=row, column=2).value or "").strip()
            if code in stations_to_update:
                ws_inv_set.cell(row=row, column=inv_col_eq, value=53.6)
                ws_inv_set.cell(row=row, column=inv_col_eq).fill = openpyxl.styles.PatternFill(fill_type=None)
                print(f"Updated Inventory {code} row {row}: -> 53.6")
    wb_inv.save(str(inv_path))
    print(f"Saved {inv_path} successfully")
