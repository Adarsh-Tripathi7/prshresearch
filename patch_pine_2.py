import sys

with open('data.txt', 'r') as f:
    lines = f.readlines()
nq_str = lines[0].split('=')[1].strip()
es_str = lines[1].split('=')[1].strip()

with open(r'd:\Antigravity\Indicators\ib_hourly_levels.pine', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''// ═══════════════════════════════════════════════════════════════════════════════
// DATA — DB PROBABILITY  (41 windows, rounded to 1 decimal)
// Index: 0 = 18:00, 1 = 18:30 … 30 = 09:00, 31 = 09:30 … 40 = 14:00
// ═══════════════════════════════════════════════════════════════════════════════'''

replacement = f'''// ═══════════════════════════════════════════════════════════════════════════════
// DATA ARRAYS
// ═══════════════════════════════════════════════════════════════════════════════
var int[] WSTARTS = array.from(1080, 1110, 1140, 1170, 1200, 1230, 1260, 1290, 1320, 1350, 1380, 1410, 0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 360, 390, 420, 450, 480, 510, 540, 570, 600, 630, 660, 690, 720, 750, 780, 810, 840)

var string[] WNAMES = array.from("18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00", "21:30", "22:00", "22:30", "23:00", "23:30", "00:00", "00:30", "01:00", "01:30", "02:00", "02:30", "03:00", "03:30", "04:00", "04:30", "05:00", "05:30", "06:00", "06:30", "07:00", "07:30", "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30", "13:00", "13:30", "14:00")

var ACT_PCT = array.new<int>(0)
var RLABELS = array.new<string>(0)
var float[] NQ_EXT = array.new<float>(0)
var float[] ES_EXT = array.new<float>(0)

if barstate.isfirst
    if i_r95
        array.push(ACT_PCT, 0)
        array.push(RLABELS, "95%")
    if i_r90
        array.push(ACT_PCT, 1)
        array.push(RLABELS, "90%")
    if i_r75
        array.push(ACT_PCT, 4)
        array.push(RLABELS, "75%")
    if i_r50
        array.push(ACT_PCT, 9)
        array.push(RLABELS, "50%")
    if i_r25
        array.push(ACT_PCT, 14)
        array.push(RLABELS, "25%")
    if i_r10
        array.push(ACT_PCT, 17)
        array.push(RLABELS, "10%")
    if i_r05
        array.push(ACT_PCT, 18)
        array.push(RLABELS, "5%")
        
    string nq_str = "{nq_str}"
    string[] nq_strs = str.split(nq_str, ",")
    for s in nq_strs
        array.push(NQ_EXT, str.tonumber(s))

    string es_str = "{es_str}"
    string[] es_strs = str.split(es_str, ",")
    for s in es_strs
        array.push(ES_EXT, str.tonumber(s))
'''

if target in content:
    content = content.replace(target, replacement)
    with open(r'd:\Antigravity\Indicators\ib_hourly_levels.pine', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Patched successfully!')
else:
    print('Target not found in content!')
