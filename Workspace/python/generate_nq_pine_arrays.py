import pandas as pd
import math

df = pd.read_csv(r'd:\Antigravity\Results\nq_all_breaks_combined_percentiles.csv')
p_cols = ['5%', '10%', '15%', '20%', '25%', '30%', '35%', '40%', '45%', '50%', '55%', '60%', '65%', '70%', '75%', '80%', '85%', '90%', '95%']

values = []
for index, row in df.iterrows():
    for p in p_cols:
        val = row[p]
        if pd.isna(val) or math.isnan(val):
            val = 0.0
        values.append(round(float(val), 2))

# Generate array.concat lines
pine_code = "var float[] NQ_EXT = array.new<float>(0)\nif barstate.isfirst\n"
chunk_size = 50
for i in range(0, len(values), chunk_size):
    chunk = values[i:i+chunk_size]
    chunk_str = ", ".join([str(x) for x in chunk])
    pine_code += f"    array.concat(NQ_EXT, array.from({chunk_str}))\n"

with open(r'd:\Antigravity\Workspace\python\nq_pine_arrays.txt', 'w') as f:
    f.write(pine_code)

print("Pine code generated successfully.")
