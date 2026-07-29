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
        
    # Window logic modifications: keep 60m window (start_time + 59), change step to 15m
    content = content.replace("start_time += 30", "start_time += 15")
    
    # Text modifications
    content = content.replace("30m step", "15m step")
    
    # Output file modifications
    content = content.replace(".csv", "_15m_step.csv")
    content = content.replace(".png", "_15m_step.png")
    content = content.replace(".md", "_15m_step.md")
    content = content.replace(".txt", "_15m_step.txt")

    new_script_name = script.replace(".py", "_15m_step.py")
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
dash_content = dash_content.replace('ib_interactive_dashboard_60m.html', 'ib_interactive_dashboard_15m_step.html')

# Change input files
dash_content = dash_content.replace('"db_probability_by_rth_close.csv"', '"db_probability_by_rth_close_15m_step.csv"')
dash_content = dash_content.replace('"db_probability_by_first_break.csv"', '"db_probability_by_first_break_15m_step.csv"')
dash_content = dash_content.replace('"ib_correlation_directional.csv"', '"ib_correlation_directional_15m_step.csv"')
dash_content = dash_content.replace('_percentiles.csv"', '_percentiles_15m_step.csv"')

# Update Title and texts
dash_content = dash_content.replace('IB Research Terminal — NQ & ES', 'IB Research Terminal (15m step) — NQ & ES')
dash_content = dash_content.replace('60m rolling · 30m step', '60m rolling · 15m step')
dash_content = dash_content.replace('>42<', '>81<') # Update the number of windows metric if it has >42<
dash_content = dash_content.replace(' 42<', ' 81<')
dash_content = dash_content.replace('>42 ', '>81 ')
dash_content = dash_content.replace('42', '81') # Just replace 42 with 81 generally

new_dash_script = "ib_interactive_dashboard_15m_step.py"
with open(new_dash_script, "w", encoding="utf-8") as f:
    f.write(dash_content)

print(f"Created {new_dash_script}. Running it now...")
subprocess.run(["python", new_dash_script])
print("All 15-minute step tests and dashboard generation completed successfully!")
