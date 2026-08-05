import re
with open(r'd:\Antigravity\banknifty_dashboard\index.html', 'r', encoding='utf-8') as f:
    content = f.read()
content = re.sub(r'<a href="dashboard\.html\?tf=time_range_(120m|15m_step|30m_15m_step|45m|7m)&bust=1".*?</a>', '', content, flags=re.DOTALL)
with open(r'd:\Antigravity\banknifty_dashboard\index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done")
