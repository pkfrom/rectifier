import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

# Check font
font_path = "C:/Windows/Fonts/THSarabunNew.ttf"
bold_font_path = "C:/Windows/Fonts/THSarabunNew Bold.ttf"

if Path(font_path).exists():
    fm.fontManager.addfont(font_path)
    fm.fontManager.addfont(bold_font_path)
    prop = fm.FontProperties(fname=font_path)
    prop_bold = fm.FontProperties(fname=bold_font_path)
    plt.rcParams['font.family'] = prop.get_name()
else:
    print("Warning: TH Sarabun New not found, using default sans-serif")
    prop = fm.FontProperties()
    prop_bold = fm.FontProperties()

reports_dir = Path("reports")
charts_dir = reports_dir / "charts"
charts_dir.mkdir(parents=True, exist_ok=True)

df_inv = pd.read_excel(reports_dir / "Rectifier_Inventory_188_Sites.xlsx", sheet_name='Sheet1')
df_set = pd.read_excel(reports_dir / "Rectifier_Inventory_188_Sites.xlsx", sheet_name='Settings')

# Chart 1: DC Voltage Distribution
fig, ax = plt.subplots(figsize=(8, 4.2), dpi=300)
v_data = pd.to_numeric(df_inv['Output Voltage (V)'], errors='coerce').dropna()
n, bins, patches = ax.hist(v_data, bins=15, color='#1F4E79', edgecolor='white', alpha=0.85)

ax.axvline(53.5, color='#C00000', linestyle='--', linewidth=1.5, label='Target Float Voltage (53.5 V)')
ax.axvline(v_data.mean(), color='#2CA02C', linestyle='-', linewidth=1.5, label=f'Mean Observed ({v_data.mean():.2f} V)')

ax.set_title('การกระจายตัวของแรงดันไฟฟ้ากระแสตรง (DC Bus Voltage Distribution)', fontsize=14, fontweight='bold', fontproperties=prop_bold, pad=12)
ax.set_xlabel('แรงดันไฟตรง (V)', fontsize=12, fontproperties=prop)
ax.set_ylabel('จำนวนสถานี (แห่ง)', fontsize=12, fontproperties=prop)
ax.legend(prop=prop, frameon=True, facecolor='#F8F9FA')
ax.grid(axis='y', linestyle=':', alpha=0.6)
ax.set_axisbelow(True)
plt.tight_layout()
c1_path = charts_dir / "chart1_dc_voltage_dist.png"
plt.savefig(c1_path)
plt.close()
print(f"Saved {c1_path}")

# Chart 2: System Load Current Distribution
fig, ax = plt.subplots(figsize=(8, 4.2), dpi=300)
load_data = pd.to_numeric(df_inv['System Load (A)'], errors='coerce').dropna()
ax.hist(load_data, bins=16, color='#2F5597', edgecolor='white', alpha=0.85)
ax.axvline(load_data.mean(), color='#C00000', linestyle='--', linewidth=1.5, label=f'Mean Load ({load_data.mean():.2f} A)')
ax.axvline(69.0, color='#7F7F7F', linestyle=':', linewidth=1.5, label='Rated Capacity 2x Rectifiers (69.0 A)')

ax.set_title('การกระจายตัวของกระแสโหลดสถานี (Substation DC Load Current)', fontsize=14, fontweight='bold', fontproperties=prop_bold, pad=12)
ax.set_xlabel('กระแสโหลด (A)', fontsize=12, fontproperties=prop)
ax.set_ylabel('จำนวนสถานี (แห่ง)', fontsize=12, fontproperties=prop)
ax.legend(prop=prop, frameon=True, facecolor='#F8F9FA')
ax.grid(axis='y', linestyle=':', alpha=0.6)
ax.set_axisbelow(True)
plt.tight_layout()
c2_path = charts_dir / "chart2_load_current_dist.png"
plt.savefig(c2_path)
plt.close()
print(f"Saved {c2_path}")

# Chart 3: Temperature Correlation & Hotspots
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=300)
amb_data = pd.to_numeric(df_inv['Ambient Temp (°C)'], errors='coerce')
bat_data = pd.to_numeric(df_inv['Battery Temp (°C)'], errors='coerce')

valid = ~(amb_data.isna() | bat_data.isna())
x = amb_data[valid]
y = bat_data[valid]

ax.scatter(x, y, color='#2E75B6', alpha=0.7, edgecolors='none', s=45, label='สถานีปกติ (186 แห่ง)')

# Threshold lines
ax.axhline(35, color='#ED7D31', linestyle='--', linewidth=1, label='เกณฑ์เตือนอุณหภูมิแบตเตอรี่ (35°C)')
ax.axvline(38, color='#C00000', linestyle='--', linewidth=1, label='เกณฑ์เตือนอุณหภูมิห้อง (38°C)')

# Annotate outliers
outliers = [
    ('BYD (เขตบางใหญ่)', 40.0, 39.0),
    ('BU (บางปู)', 36.0, 38.0),
    ('SB (สนามบินน้ำ)', 38.0, 35.0)
]
for name, amb, bat in outliers:
    ax.scatter([amb], [bat], color='#C00000', s=90, zorder=5)
    ax.annotate(name, (amb, bat), textcoords="offset points", xytext=(-20, 8),
                fontproperties=prop_bold, fontsize=11, color='#C00000',
                bbox=dict(boxstyle="round,pad=0.2", fc="#FFEEEE", ec="#C00000", lw=0.8))

ax.set_title('ความสัมพันธ์ระหว่างอุณหภูมิห้องและอุณหภูมิแบตเตอรี่ (Thermal Matrix)', fontsize=14, fontweight='bold', fontproperties=prop_bold, pad=12)
ax.set_xlabel('อุณหภูมิห้องควบคุม Ambient Temp (°C)', fontsize=12, fontproperties=prop)
ax.set_ylabel('อุณหภูมิแบตเตอรี่ Battery Temp (°C)', fontsize=12, fontproperties=prop)
ax.legend(prop=prop, frameon=True, facecolor='#F8F9FA', loc='upper left')
ax.grid(True, linestyle=':', alpha=0.6)
ax.set_axisbelow(True)
plt.tight_layout()
c3_path = charts_dir / "chart3_thermal_matrix.png"
plt.savefig(c3_path)
plt.close()
print(f"Saved {c3_path}")

# Chart 4: Configuration & Firmware Breakdown
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.5, 4.2), dpi=300)

# End Test Time
tt_counts = df_set['Batt End Test Time (min)'].value_counts()
labels1 = [f'{int(k)} นาที' for k in tt_counts.index]
colors1 = ['#1F4E79', '#2F5597', '#5B9BD5', '#ED7D31', '#C00000']
bars1 = ax1.bar(labels1, tt_counts.values, color=colors1[:len(tt_counts)], width=0.55)
ax1.set_title('ระยะเวลาทดสอบแบตเตอรี่ (End Test Time)', fontsize=13, fontweight='bold', fontproperties=prop_bold)
ax1.set_ylabel('จำนวนสถานี (แห่ง)', fontsize=11, fontproperties=prop)
ax1.grid(axis='y', linestyle=':', alpha=0.6)
for bar in bars1:
    h = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., h + 1, f'{int(h)}', ha='center', va='bottom', fontproperties=prop, fontsize=11)

# Firmware versions
fw_counts = df_inv['Controller Software Version'].value_counts()
labels2 = [str(k) for k in fw_counts.index]
colors2 = ['#1F4E79', '#41719C', '#5B9BD5', '#8FAADC']
bars2 = ax2.bar(labels2, fw_counts.values, color=colors2[:len(fw_counts)], width=0.5)
ax2.set_title('เวอร์ชันเฟิร์มแวร์คอนโทรลเลอร์ (Firmware)', fontsize=13, fontweight='bold', fontproperties=prop_bold)
ax2.set_ylabel('จำนวนสถานี (แห่ง)', fontsize=11, fontproperties=prop)
ax2.grid(axis='y', linestyle=':', alpha=0.6)
for bar in bars2:
    h = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., h + 1, f'{int(h)}', ha='center', va='bottom', fontproperties=prop, fontsize=11)

plt.tight_layout()
c4_path = charts_dir / "chart4_config_fw_breakdown.png"
plt.savefig(c4_path)
plt.close()
print(f"Saved {c4_path}")
