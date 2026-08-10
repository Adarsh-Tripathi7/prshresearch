import os
import json
import glob

data_dir = r"d:\Antigravity\prshcapital\data"
json_files = glob.glob(os.path.join(data_dir, "*.json"))

for jf in json_files:
    try:
        with open(jf, "r") as f:
            data = json.load(f)
            if "prob" in data and len(data["prob"]) > 1:
                w1 = data['prob'][0].get('Window', 'N/A')
                w2 = data['prob'][1].get('Window', 'N/A')
                print(f"{os.path.basename(jf):<30} : {w1} -> {w2}")
            else:
                print(f"{os.path.basename(jf):<30} : No enough prob data")
    except Exception as e:
        print(f"Error reading {jf}: {e}")
