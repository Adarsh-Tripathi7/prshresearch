import re

with open(r'd:\Antigravity\imobile ib dashboard\main.js', 'r', encoding='utf-8') as f:
    code = f.read()

# Remove all `.clear();` lines
code = re.sub(r'\s*if \(charts\[.*?\]\) charts\[.*?\].clear\(\);', '', code)

# Change setOption(..., true) to setOption(..., {replaceMerge: ['series']})
code = re.sub(r'\}, true\);', r'}, {replaceMerge: ["series"]});', code)

with open(r'd:\Antigravity\imobile ib dashboard\main.js', 'w', encoding='utf-8') as f:
    f.write(code)
