import os

OUT_DIR = r'd:\Antigravity\imobile ib dashboard'
for f in os.listdir(OUT_DIR):
    if not f.endswith('.html'): continue
    path = os.path.join(OUT_DIR, f)
    html = open(path, 'r', encoding='utf-8').read()
    if 'window.onerror' not in html:
        err_script = """<script>window.onerror = function(msg, url, line, col, error) { document.body.innerHTML = '<div style="color:red; background:white; position:fixed; top:0; left:0; right:0; z-index:99999; padding:20px; font-size:16px; word-break:break-all;"><b>JS Error:</b> ' + msg + '<br>Line: ' + line + '<br>Col: ' + col + '</div>' + document.body.innerHTML; };</script>"""
        html = html.replace('<head>', '<head>' + err_script)
        open(path, 'w', encoding='utf-8').write(html)
print('Injected window.onerror')
