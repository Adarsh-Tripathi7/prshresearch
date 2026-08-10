import re

with open(r'd:\Antigravity\prshcapital\index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Remove LIGHT THEME SUPPORT CSS
html = re.sub(r'/\*\s*LIGHT THEME SUPPORT\s*\*/.*?</style>', '</style>', html, flags=re.DOTALL)

# 2. Remove theme <script> in head
html = re.sub(r'<script>\s*\(function\(\)\{\s*var theme = localStorage\.getItem\("theme"\);\s*if\(theme === "light"\) document\.documentElement\.setAttribute\("data-theme", "light"\);\s*\}\)\(\);\s*</script>', '', html, flags=re.DOTALL)

# 3. Remove themeToggleBtn button
html = re.sub(r'<button id="themeToggleBtn".*?</button>', '', html, flags=re.DOTALL)

# 4. Remove Theme toggler JS logic at bottom
html = re.sub(r'// Theme toggler\s*document\.addEventListener\("DOMContentLoaded", function\(\) \{.*?\}\);\s*</script>', '</script>', html, flags=re.DOTALL)

with open(r'd:\Antigravity\prshcapital\index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Light mode removed successfully.')
