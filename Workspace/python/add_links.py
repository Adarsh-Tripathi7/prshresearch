import re
with open(r'd:\Antigravity\banknifty_dashboard\index.html', 'r', encoding='utf-8') as f:
    content = f.read()

new_links = '''        <a href="dashboard.html?tf=time_range_60m_15m_step&bust=1" class="nav-card animate-up" style="animation-delay: 0.8s" data-title="60m / 15m step" data-category="time-range" data-type="step">
            <div class="nav-icon-wrap">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
            </div>
            <div class="nav-info">
                <div class="nav-title-row">
                    <div class="nav-title">60m / 15m step</div>
                    <div class="nav-badge">Step</div>
                </div>
                <div class="nav-sub">Rolling analysis</div>
            </div>
            <div class="nav-arrow"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg></div>
        </a>
        <a href="dashboard.html?tf=time_range_30m_15m_step&bust=1" class="nav-card animate-up" style="animation-delay: 0.85s" data-title="30m / 15m step" data-category="time-range" data-type="step">
            <div class="nav-icon-wrap">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
            </div>
            <div class="nav-info">
                <div class="nav-title-row">
                    <div class="nav-title">30m / 15m step</div>
                    <div class="nav-badge">Step</div>
                </div>
                <div class="nav-sub">Rolling analysis</div>
            </div>
            <div class="nav-arrow"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg></div>
        </a>
        <a href="dashboard.html?tf=time_range_20m_7m_step&bust=1" class="nav-card animate-up" style="animation-delay: 0.9s" data-title="20m / 7m step" data-category="time-range" data-type="step">
            <div class="nav-icon-wrap">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
            </div>
            <div class="nav-info">
                <div class="nav-title-row">
                    <div class="nav-title">20m / 7m step</div>
                    <div class="nav-badge">Step</div>
                </div>
                <div class="nav-sub">Rolling analysis</div>
            </div>
            <div class="nav-arrow"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg></div>
        </a>'''

content = content.replace('</div>\n    </div>\n    <div class="empty-state" id="emptyState">', new_links + '\n    </div>\n    </div>\n    <div class="empty-state" id="emptyState">')
with open(r'd:\Antigravity\banknifty_dashboard\index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done")
