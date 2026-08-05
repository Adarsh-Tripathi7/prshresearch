import re
with open(r'd:\Antigravity\banknifty_dashboard\index.html', 'r', encoding='utf-8') as f:
    content = f.read()

new_link = '''        <a href="dashboard.html?tf=time_range_10m_1m_step&bust=1" class="nav-card animate-up" style="animation-delay: 0.95s" data-title="10m / 1m step" data-category="time-range" data-type="step">
            <div class="nav-icon-wrap">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
            </div>
            <div class="nav-info">
                <div class="nav-title-row">
                    <div class="nav-title">10m / 1m step</div>
                    <div class="nav-badge">Step</div>
                </div>
                <div class="nav-sub">Rolling analysis</div>
            </div>
            <div class="nav-arrow"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg></div>
        </a>'''

content = content.replace('</div>\n    </div>\n    <div class="empty-state" id="emptyState">', new_link + '\n    </div>\n    </div>\n    <div class="empty-state" id="emptyState">')
with open(r'd:\Antigravity\banknifty_dashboard\index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done")
