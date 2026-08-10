import subprocess
import json
import re

def run_script(script_name):
    print(f"Running {script_name}...")
    res = subprocess.run(['python', script_name], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error running {script_name}:\n{res.stderr}")
        return None
    # Output might have warning logs, so let's find the JSON block
    lines = res.stdout.strip().split('\n')
    for line in reversed(lines):
        if line.startswith('{'):
            return json.loads(line)
    return None

def inject_json(html_path, json_data, key_name):
    print(f"Injecting into {html_path}...")
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Find `const _D = { ... };`
    match = re.search(r'const _D = (\{.*?\});\n', content, flags=re.DOTALL)
    if not match:
        print(f"Could not find const _D in {html_path}")
        return
        
    d_str = match.group(1)
    try:
        d_obj = json.loads(d_str)
    except json.JSONDecodeError as e:
        print(f"Error parsing _D in {html_path}: {e}")
        return
        
    # Add the retracement data
    # In pdr_analysis.html, PAGE_TYPE is "pdr". So it accesses _D["pdr"]
    # So we should inject into _D[key_name]["retrace"]
    if key_name not in d_obj:
        d_obj[key_name] = {}
        
    d_obj[key_name]['retrace'] = json_data
    
    new_d_str = json.dumps(d_obj)
    
    new_content = content[:match.start(1)] + new_d_str + content[match.end(1):]
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Successfully updated {html_path}")

def main():
    pdr_data = run_script('pdr_retracement_cdf.py')
    if pdr_data:
        inject_json(r'd:\Antigravity\prshcapital\pdr_analysis.html', pdr_data, 'pdr')
        
    pwr_data = run_script('pwr_retracement_cdf.py')
    if pwr_data:
        inject_json(r'd:\Antigravity\prshcapital\pwr_analysis.html', pwr_data, 'pwr')

if __name__ == '__main__':
    main()
