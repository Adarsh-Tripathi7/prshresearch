import os
import re

main_js = r"d:\Antigravity\banknifty_dashboard\main.js"

with open(main_js, 'r', encoding='utf-8') as f:
    js = f.read()

# Fix Extension Heatmap data loading
js = js.replace("EXT[globalAsset === 'es' ? 'es' : 'nq']", "EXT['bnf']")
js = js.replace("EXT['nq']", "EXT['bnf']")
js = js.replace("EXT['es']", "EXT['bnf']")

# Fix Probability Heatmap sorting
js = js.replace("hmSortCol.includes('NQ') ? a.NQ_DB_Prob : (hmSortCol.includes('ES') ? a.ES_DB_Prob : 0)", "a.BNF_DB_Prob")
js = js.replace("hmSortCol.includes('NQ') ? b.NQ_DB_Prob : (hmSortCol.includes('ES') ? b.ES_DB_Prob : 0)", "b.BNF_DB_Prob")

# Just in case there are lingering a.NQ_DB_Prob etc
js = js.replace(".NQ_DB_Prob", ".BNF_DB_Prob")
js = js.replace(".ES_DB_Prob", ".BNF_DB_Prob")
js = js.replace("['NQ', 'ES']", "['BNF']")
js = js.replace("['NQ','ES']", "['BNF']")

# Also, the sorting logic looks for 'NQ' and 'ES' in labels.
# const allLabels = [...extLabels, 'ES Lead +`', ... 'NQ', 'ES'];
js = re.sub(r"const allLabels = \[.*?\];", "const allLabels = [...extLabels, 'BNF Lead +`', 'BNF Lead +\"', 'Combined Avg', 'BNF'];", js)

with open(main_js, 'w', encoding='utf-8') as f:
    f.write(js)
print("Heatmap logic fixed!")
