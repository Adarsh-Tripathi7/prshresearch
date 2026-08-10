import re

with open(r'd:\Antigravity\prshcapital\index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Remove glare from VanillaTilt
html = re.sub(r' data-tilt-glare data-tilt-max-glare="[0-9.]+"', '', html)

# 2. Optimize Navbar blur
html = html.replace('backdrop-filter: blur(24px) saturate(1.5);', '')
html = html.replace('-webkit-backdrop-filter: blur(24px) saturate(1.5);', '')
html = html.replace('background: rgba(3, 3, 5, 0.6);', 'background: rgba(3, 3, 5, 0.98);')

# 3. Optimize Hero Grid (Remove mask and continuous animation)
html = html.replace('animation: gridMove 15s linear infinite;', '/* animation removed */')
html = html.replace('-webkit-mask-image: linear-gradient(to top, rgba(0,0,0,1) 10%, rgba(0,0,0,0) 80%);', '/* mask removed */')

with open(r'd:\Antigravity\prshcapital\index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Optimizations applied successfully.')
