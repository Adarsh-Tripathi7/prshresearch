import os
import subprocess

original = "ib_interactive_dashboard_experiment.py"

with open(original, "r", encoding="utf-8") as f:
    content = f.read()

# Change DATA_DIR and OUT_PATH
content = content.replace(r'DATA_DIR = r"d:\Antigravity\Results\IB Analysis"', r'DATA_DIR = r"d:\Antigravity\Results"')
content = content.replace('ib_interactive_dashboard_60m.html', 'ib_interactive_dashboard_30m.html')

# Change input files
content = content.replace('"db_probability_by_rth_close.csv"', '"db_probability_by_rth_close_30m.csv"')
content = content.replace('"db_probability_by_first_break.csv"', '"db_probability_by_first_break_30m.csv"')
content = content.replace('"ib_correlation_directional.csv"', '"ib_correlation_directional_30m.csv"')
content = content.replace('_percentiles.csv"', '_percentiles_30m.csv"')

# Update Title
content = content.replace('IB Research Terminal — NQ & ES', 'IB Research Terminal (30m) — NQ & ES')
content = content.replace('60m rolling · 30m step', '30m rolling · 30m step')

new_script = "ib_interactive_dashboard_30m.py"
with open(new_script, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Created {new_script}. Running it now...")
subprocess.run(["python", new_script])
print("Done!")
