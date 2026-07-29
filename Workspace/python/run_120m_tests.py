import os
import subprocess

scripts_to_convert = [
    "ib_double_break_probability_rth.py",
    "ib_double_break_duration_test.py",
    "ib_double_break_test.py",
    "ib_db_by_first_break.py",
    "ib_extension_test.py",
    "ib_correlation_test_fast.py"
]

for script in scripts_to_convert:
    with open(script, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Window logic modifications
    content = content.replace("start_time + 59", "start_time + 119")
    content = content.replace("start_time += 30", "start_time += 60")
    
    # Text modifications
    content = content.replace("60-Minute Window", "120-Minute Window")
    content = content.replace("60-minute Initial Balance", "120-minute Initial Balance")
    content = content.replace("60-Minute IB Window", "120-Minute IB Window")
    content = content.replace("60-minute windows", "120-minute windows")
    content = content.replace("60m rolling", "120m rolling")
    
    # Output file modifications
    content = content.replace(".csv", "_120m.csv")
    content = content.replace(".png", "_120m.png")
    content = content.replace(".md", "_120m.md")
    content = content.replace(".txt", "_120m.txt")

    new_script_name = script.replace(".py", "_120m.py")
    with open(new_script_name, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"Created {new_script_name}. Running it now...")
    subprocess.run(["python", new_script_name])
    print(f"Finished running {new_script_name}\n")

# Now generate the dashboard script
dashboard_script = "ib_interactive_dashboard_experiment.py"
with open(dashboard_script, "r", encoding="utf-8") as f:
    dash_content = f.read()

# Change DATA_DIR and OUT_PATH
dash_content = dash_content.replace(r'DATA_DIR = r"d:\Antigravity\Results\IB Analysis"', r'DATA_DIR = r"d:\Antigravity\Results"')
dash_content = dash_content.replace('ib_interactive_dashboard_60m.html', 'ib_interactive_dashboard_120m.html')

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
print("All 120-minute tests and dashboard generation completed successfully!")
