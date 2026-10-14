import sys
from pathlib import Path
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

excel_path = Path("reports/Rectifier_Inventory_188_Sites.xlsx")
df = pd.read_excel(excel_path, sheet_name='Sheet1')

print(f"Total Rows: {len(df)}")
cols = [
    'Output Voltage (V)', 'System Load (A)', 'System Power (kW)',
    'AC Phase A Voltage (V)', 'Battery Current (A)', 'Battery Temp (°C)', 'Ambient Temp (°C)'
]

for col in cols:
    s = pd.to_numeric(df[col], errors='coerce').dropna()
    print(f"{col}: count={len(s)}, min={s.min():.2f}, max={s.max():.2f}, mean={s.mean():.2f}, std={s.std():.2f}")

print("\n--- Firmware Distribution ---")
print(df['Controller Software Version'].value_counts(dropna=False))

print("\n--- Collection Status ---")
print(df['สถานะเก็บข้อมูล'].value_counts(dropna=False))

print("\n--- Abnormal Battery Current (> 1.0 A) ---")
high_ib = df[pd.to_numeric(df['Battery Current (A)'], errors='coerce') > 1.0]
for idx, r in high_ib.iterrows():
    print(f"{r['ชื่อย่อ']} ({r['สถานีไฟฟ้า']}) IP={r['IP']}: {r['Battery Current (A)']} A, Status={r['Battery Status']}")

print("\n--- High Temperature Sites (Battery >= 35°C or Ambient >= 37°C) ---")
high_temp = df[(pd.to_numeric(df['Battery Temp (°C)'], errors='coerce') >= 35) | (pd.to_numeric(df['Ambient Temp (°C)'], errors='coerce') >= 37)]
for idx, r in high_temp.iterrows():
    print(f"{r['ชื่อย่อ']} ({r['สถานีไฟฟ้า']}) IP={r['IP']}: Batt={r['Battery Temp (°C)']}°C, Amb={r['Ambient Temp (°C)']}°C")

print("\n--- No IP Sites ---")
no_ip = df[df['IP'].isna() | (df['IP'].astype(str).str.strip() == '')]
for idx, r in no_ip.iterrows():
    print(f"{r['ชื่อย่อ']} ({r['สถานีไฟฟ้า']})")

# Check Settings in Rectifier_Inventory_188_Sites.xlsx
df_set = pd.read_excel(excel_path, sheet_name='Settings')
print("\nSettings Columns:", list(df_set.columns)[:15])
for c in ['Float Charge Voltage (V)', 'Equalize Charge Voltage (V)', 'LVD Disconnect Voltage (V)', 'LVD Reconnect Voltage (V)', 'End Test Time (min)']:
    if c in df_set.columns:
        print(f"\n{c} value counts:")
        print(df_set[c].value_counts(dropna=False))

