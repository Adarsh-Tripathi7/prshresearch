import os
import json
import msgpack
import glob

# Path to the data directory
data_dir = r"d:\Antigravity\prshcapital\data"

# Find all JSON files in the data directory
json_files = glob.glob(os.path.join(data_dir, "*.json"))

for json_path in json_files:
    if os.path.basename(json_path) == "manifest.json":
        continue # skip manifest
        
    # Generate msgpack path
    msgpack_path = json_path.replace('.json', '.msgpack')
    
    print(f"Converting {os.path.basename(json_path)} to MessagePack...")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    with open(msgpack_path, 'wb') as f:
        packed = msgpack.packb(data, use_single_float=True)
        f.write(packed)

print("Conversion to MessagePack completed!")
