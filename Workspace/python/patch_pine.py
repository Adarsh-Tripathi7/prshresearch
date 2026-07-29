import re

with open('data.txt', 'r') as f:
    lines = f.readlines()
nq_str = lines[0].split('=')[1].strip()
es_str = lines[1].split('=')[1].strip()

with open(r'd:\Antigravity\Indicators\ib_hourly_levels.pine', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove i_breakType
content = re.sub(r'i_breakType\s*=\s*input\.string\(.*?\)\n', '', content)

# 2. Replace the data block
start_idx = content.find('var _da = array.from(')
end_idx = content.find('// ─── Assemble arrays')

if start_idx != -1 and end_idx != -1:
    end_assemble = content.find('// ─── Time Windows', end_idx)
    if end_assemble != -1:
        replacement = f'''// Data stored as strings to bypass Pine Script array limits
var string NQ_EXT_STR = "{nq_str}"
var string ES_EXT_STR = "{es_str}"

var float[] NQ_EXT = array.new<float>(0)
var float[] ES_EXT = array.new<float>(0)

if barstate.isfirst
    string[] nq_strs = str.split(NQ_EXT_STR, ",")
    for s in nq_strs
        array.push(NQ_EXT, str.tonumber(s))
    string[] es_strs = str.split(ES_EXT_STR, ",")
    for s in es_strs
        array.push(ES_EXT, str.tonumber(s))

'''
        content = content[:start_idx] + replacement + content[end_assemble:]

# 3. Modify getExt
content = re.sub(
    r'float\[\] src = i_breakType == "Double Break" \? NQ_DB_EXT : NQ_SB_EXT',
    r'float[] src = i_asset == "NQ" ? NQ_EXT : ES_EXT',
    content
)

# 4. Remove Probability Data
prob_start = content.find('var NQ_PROB = array.from(')
if prob_start != -1:
    prob_end = content.find('// Get R-extension', prob_start)
    if prob_end != -1:
        content = content[:prob_start] + content[prob_end:]

# 5. Remove Table drawing
new_lines = []
for line in content.splitlines():
    if 'probArr =' in line or 'dbPct =' in line or 'table.cell(' in line or 'table.new(' in line or 'var table tb =' in line or 'table.clear' in line:
        continue
    new_lines.append(line)
content = '\n'.join(new_lines) + '\n'

with open(r'd:\Antigravity\Indicators\ib_hourly_levels.pine', 'w', encoding='utf-8') as f:
    f.write(content)
print('Patched successfully!')
