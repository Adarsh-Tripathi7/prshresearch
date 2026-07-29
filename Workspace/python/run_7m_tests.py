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

window_add = 6
step = 7
num_windows = len(range(60, 1261, step))
suffix = "_7m"

print(f"==================== GENERATING 7m IB / 7m STEP TESTS ====================")
for script in scripts_to_convert:
    with open(script, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Window logic modifications
    content = content.replace("start_time + 59", f"start_time + {window_add}")
    content = content.replace("start_time += 30", f"start_time += {step}")
    
    # Text modifications
    content = content.replace("60-Minute Window", "7-Minute Window")
    content = content.replace("60-minute Initial Balance", "7-minute Initial Balance")
    content = content.replace("60-Minute IB Window", "7-Minute IB Window")
    content = content.replace("60-minute windows", "7-minute windows")
    content = content.replace("60m rolling", "7m rolling")
    
    # Output file modifications
    content = content.replace(".csv", f"{suffix}.csv")
    content = content.replace(".png", f"{suffix}.png")
    content = content.replace(".md", f"{suffix}.md")
    content = content.replace(".txt", f"{suffix}.txt")

    new_script_name = script.replace(".py", f"{suffix}.py")
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
dash_content = dash_content.replace('ib_interactive_dashboard_60m.html', f'ib_interactive_dashboard{suffix}.html')

# Change input files
dash_content = dash_content.replace('"db_probability_by_rth_close.csv"', f'"db_probability_by_rth_close{suffix}.csv"')
dash_content = dash_content.replace('"db_probability_by_first_break.csv"', f'"db_probability_by_first_break{suffix}.csv"')
dash_content = dash_content.replace('"ib_correlation_directional.csv"', f'"ib_correlation_directional{suffix}.csv"')
dash_content = dash_content.replace('_percentiles.csv"', f'_percentiles{suffix}.csv"')

# Update Title and texts
dash_content = dash_content.replace('IB Research Terminal — NQ & ES', 'IB Research Terminal (7m) — NQ & ES')
dash_content = dash_content.replace('60m rolling · 30m step', f'7m rolling · {step}m step')

# Replace window count
dash_content = dash_content.replace('>42<', f'>{num_windows}<')
dash_content = dash_content.replace(' 42<', f' {num_windows}<')
dash_content = dash_content.replace('>42 ', f'>{num_windows} ')

new_dash_script = f"ib_interactive_dashboard{suffix}.py"
with open(new_dash_script, "w", encoding="utf-8") as f:
    f.write(dash_content)

print(f"Created {new_dash_script}. Running it now...")
subprocess.run(["python", new_dash_script])
print(f"7m tests and dashboard generation completed successfully!\n")
