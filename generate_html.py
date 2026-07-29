import pandas as pd

df = pd.read_csv(r'd:\Antigravity\Results\7m_double_break_with_time.csv')

html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>7m Double Break Data</title>
<style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #0a0a0a; color: #fff; padding: 20px; }
    table { border-collapse: collapse; width: 100%; text-align: right; font-variant-numeric: tabular-nums; }
    th { cursor: pointer; background: #1a1a1a; padding: 12px 10px; border-bottom: 2px solid #333; position: sticky; top: 0; user-select: none; font-size: 0.9em; }
    th:hover { background: #333; }
    td { padding: 10px; border-bottom: 1px solid #222; font-size: 0.95em; }
    tr:hover { background: #1f1f1f; }
    .window-col { text-align: left; font-weight: bold; color: #6366f1; }
    .nq-col { color: #38bdf8; }
    .es-col { color: #fbbf24; }
</style>
</head>
<body>
    <h2>7m Double Break - Sortable Data</h2>
    <p style="color: #888; font-size: 0.9em;">Click on any column header to sort.</p>
    <table id="dbTable">
        <thead>
            <tr>
                <th onclick="sortTable(0, 'str')">Window</th>
                <th onclick="sortTable(1, 'num')" class="nq-col">NQ Total</th>
                <th onclick="sortTable(2, 'num')" class="nq-col">NQ DB Prob (%)</th>
                <th onclick="sortTable(3, 'num')" class="nq-col">NQ P10 (m)</th>
                <th onclick="sortTable(4, 'num')" class="nq-col">NQ P25 (m)</th>
                <th onclick="sortTable(5, 'num')" class="nq-col">NQ P50 (m)</th>
                <th onclick="sortTable(6, 'num')" class="nq-col">NQ P75 (m)</th>
                <th onclick="sortTable(7, 'num')" class="nq-col">NQ P90 (m)</th>
                <th onclick="sortTable(8, 'num')" class="es-col">ES Total</th>
                <th onclick="sortTable(9, 'num')" class="es-col">ES DB Prob (%)</th>
                <th onclick="sortTable(10, 'num')" class="es-col">ES P10 (m)</th>
                <th onclick="sortTable(11, 'num')" class="es-col">ES P25 (m)</th>
                <th onclick="sortTable(12, 'num')" class="es-col">ES P50 (m)</th>
                <th onclick="sortTable(13, 'num')" class="es-col">ES P75 (m)</th>
                <th onclick="sortTable(14, 'num')" class="es-col">ES P90 (m)</th>
            </tr>
        </thead>
        <tbody>
'''

for idx, row in df.iterrows():
    html_content += f'''
            <tr>
                <td class="window-col">{row['Window']}</td>
                <td class="nq-col">{row['NQ_Total']}</td>
                <td class="nq-col">{row['NQ_DB_Prob']}%</td>
                <td class="nq-col">{row['NQ_P10_min']}</td>
                <td class="nq-col">{row['NQ_P25_min']}</td>
                <td class="nq-col">{row['NQ_P50_min']}</td>
                <td class="nq-col">{row['NQ_P75_min']}</td>
                <td class="nq-col">{row['NQ_P90_min']}</td>
                <td class="es-col">{row['ES_Total']}</td>
                <td class="es-col">{row['ES_DB_Prob']}%</td>
                <td class="es-col">{row['ES_P10_min']}</td>
                <td class="es-col">{row['ES_P25_min']}</td>
                <td class="es-col">{row['ES_P50_min']}</td>
                <td class="es-col">{row['ES_P75_min']}</td>
                <td class="es-col">{row['ES_P90_min']}</td>
            </tr>'''

html_content += '''
        </tbody>
    </table>

    <script>
    let sortOrders = {};
    function sortTable(n, type) {
        const table = document.getElementById("dbTable");
        let rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
        switching = true;
        
        dir = sortOrders[n] === "asc" ? "desc" : "asc";
        sortOrders[n] = dir;
        
        while (switching) {
            switching = false;
            rows = table.rows;
            for (i = 1; i < (rows.length - 1); i++) {
                shouldSwitch = false;
                x = rows[i].getElementsByTagName("TD")[n];
                y = rows[i + 1].getElementsByTagName("TD")[n];
                
                let valX = x.innerHTML.trim().replace('%', '');
                let valY = y.innerHTML.trim().replace('%', '');
                
                if (type === 'num') {
                    valX = valX === 'NaN' || valX === 'None' || valX === '' ? -1 : parseFloat(valX);
                    valY = valY === 'NaN' || valY === 'None' || valY === '' ? -1 : parseFloat(valY);
                } else {
                    valX = valX.toLowerCase();
                    valY = valY.toLowerCase();
                }

                if (dir == "asc") {
                    if (valX > valY) {
                        shouldSwitch = true;
                        break;
                    }
                } else if (dir == "desc") {
                    if (valX < valY) {
                        shouldSwitch = true;
                        break;
                    }
                }
            }
            if (shouldSwitch) {
                rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                switching = true;
                switchcount++;
            }
        }
    }
    </script>
</body>
</html>
'''

with open(r'd:\Antigravity\Results\7m_db_sortable.html', 'w', encoding='utf-8') as f:
    f.write(html_content)
print('Generated HTML!')
