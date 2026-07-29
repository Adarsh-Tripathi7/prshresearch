import subprocess

dashboard_script = "ib_interactive_dashboard_experiment.py"
with open(dashboard_script, "r", encoding="utf-8") as f:
    dash_content = f.read()

# Change DATA_DIR and OUT_PATH
dash_content = dash_content.replace(r'DATA_DIR = r"d:\Antigravity\Results\IB Analysis"', r'DATA_DIR = r"d:\Antigravity\Results"')
dash_content = dash_content.replace(r'OUT_PATH = r"d:\Antigravity\Dashboard\ib_interactive_dashboard_60m.html"', r'OUT_PATH = r"d:\Antigravity\Dashboard\ib_interactive_dashboard_120m.html"')

# Change input files
dash_content = dash_content.replace('"db_probability_by_rth_close.csv"', '"db_probability_by_rth_close_120m.csv"')
dash_content = dash_content.replace('"db_probability_by_first_break.csv"', '"db_probability_by_first_break_120m.csv"')
dash_content = dash_content.replace('"ib_correlation_directional.csv"', '"ib_correlation_directional_120m.csv"')
dash_content = dash_content.replace('_percentiles.csv"', '_percentiles_120m.csv"')

# Update Title
dash_content = dash_content.replace('IB Research Terminal — NQ & ES', 'IB Research Terminal (120m) — NQ & ES')
dash_content = dash_content.replace('60m rolling · 30m step', '120m rolling · 60m step')
dash_content = dash_content.replace('42', '21') # Because step is 60m, there are exactly half the windows! (1260-60)/60 + 1 = 21.

new_dash_script = "ib_interactive_dashboard_120m.py"
with open(new_dash_script, "w", encoding="utf-8") as f:
    f.write(dash_content)

print(f"Created {new_dash_script}. Running it now...")
subprocess.run(["python", new_dash_script])
