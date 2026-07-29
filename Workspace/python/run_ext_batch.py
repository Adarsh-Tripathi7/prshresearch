import os
import subprocess
import glob

scripts = glob.glob("ib_extension_test*.py")

for script in scripts:
    print(f"Running {script}...")
    subprocess.run(["python", script], check=True)
    
dash_scripts = glob.glob("ib_interactive_dashboard_*.py")
# Filter out experiment script just in case
dash_scripts = [s for s in dash_scripts if "experiment" not in s]

for script in dash_scripts:
    print(f"Running {script}...")
    subprocess.run(["python", script], check=True)

print("Running build_mobile_dashboard.py...")
subprocess.run(["python", "build_mobile_dashboard.py"], check=True)
print("Done!")
