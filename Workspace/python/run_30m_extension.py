import os
import subprocess

script = "ib_extension_test.py"
with open(script, 'r', encoding='utf-8') as f:
    content = f.read()
    
# Window logic modifications
content = content.replace("start_time + 59", "start_time + 29")

# Text modifications
content = content.replace("60-Minute Window", "30-Minute Window")
content = content.replace("60-minute Initial Balance", "30-minute Initial Balance")
content = content.replace("60-Minute IB Window", "30-Minute IB Window")

# Output file modifications
content = content.replace(".csv", "_30m.csv")
content = content.replace(".png", "_30m.png")
content = content.replace(".md", "_30m.md")
content = content.replace(".txt", "_30m.txt")

# Titles
content = content.replace("Rolling IB Double Break Correlation", "Rolling 30m IB Double Break Correlation")
content = content.replace("Probability of Double Break Based", "Probability of 30m Double Break Based")

new_script_name = script.replace(".py", "_30m.py")
with open(new_script_name, 'w', encoding='utf-8') as f:
    f.write(content)
    
print(f"Created {new_script_name}. Running it now...")
subprocess.run(["python", new_script_name])
print(f"Finished running {new_script_name}\n")
