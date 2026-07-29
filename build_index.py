import os

OUT_DIR = r"d:\Antigravity\imobile ib dashboard"

html_files = [f for f in os.listdir(OUT_DIR) if f.endswith('.html') and f != 'index.html']
html_files.sort()

def format_title(name):
    parts = name.split('_')
    if 'step' in parts:
        if len(parts) == 3:
            return f"{parts[0]} / {parts[1]} STEP".upper()
        elif len(parts) == 2:
            return f"{parts[0]} STEP".upper()
    return name.upper()

def get_type(name):
    if '_step' in name: return 'Step'
    return 'Standard'

links_html = ""
for i, f in enumerate(html_files):
    name = f.replace('time_range_', '').replace('.html', '')
    clean_name = format_title(name)
    dash_type = get_type(name)
    
    # Staggered animation delay based on index
    delay = 0.3 + (i * 0.05)
    
    links_html += f"""
        <a href="{f}" class="nav-card animate-up" style="animation-delay: {delay}s" data-title="{clean_name.lower()}" data-category="time-range" data-type="{dash_type.lower()}">
            <div class="nav-icon-wrap">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
                </svg>
            </div>
            <div class="nav-info">
                <div class="nav-title-row">
                    <span class="nav-title">{clean_name}</span>
                    <span class="nav-badge">{dash_type}</span>
                </div>
                <div class="nav-sub">Interactive probability and extension matrix</div>
            </div>
            <div class="nav-arrow">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="5" y1="12" x2="19" y2="12"></line>
                    <polyline points="12 5 19 12 12 19"></polyline>
                </svg>
            </div>
        </a>"""

index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Prsh Capital | Research Hub</title>
<link rel="manifest" href="manifest.json">
<meta name="theme-color" content="#000000">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<link rel="apple-touch-icon" href="icon-192.png">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {{
  --bg: #000000; 
  --bg-card: #0a0a0a;
  --bg-hover: #141414;
  --border: #1f1f1f;
  --border-hover: #333333;
  --text-1: #ffffff;
  --text-2: #888888;
  --text-3: #555555;
  --accent: #6366f1;
  --accent-dim: rgba(99,102,241,0.15);
  --spring: cubic-bezier(0.25, 1, 0.5, 1);
}}
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ 
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; 
    color: var(--text-1); background: var(--bg);
    -webkit-font-smoothing: antialiased;
    min-height: 100vh; display: flex; flex-direction: column;
}}

/* ACCESSIBILITY & FOCUS */
:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 4px; }}
.search-box input:focus-visible {{ outline: none; }}
.nav-brand {{ text-decoration: none; color: inherit; transition: opacity 0.2s; }}
.nav-brand:hover {{ opacity: 0.8; }}

/* ANIMATIONS */
@keyframes fadeUp {{
    from {{ opacity: 0; transform: translateY(20px) scale(0.98); }}
    to {{ opacity: 1; transform: translateY(0) scale(1); }}
}}
@keyframes fadeIn {{
    from {{ opacity: 0; }}
    to {{ opacity: 1; }}
}}
@keyframes pulseGlow {{
    0% {{ opacity: 0.5; transform: translateX(-50%) scale(1); }}
    50% {{ opacity: 0.8; transform: translateX(-50%) scale(1.05); }}
    100% {{ opacity: 0.5; transform: translateX(-50%) scale(1); }}
}}
.animate-up {{ opacity: 0; animation: fadeUp 0.6s var(--spring) forwards; }}
.animate-fade {{ opacity: 0; animation: fadeIn 1s ease forwards; }}

/* NAVBAR */
.navbar {{
    position: sticky; top: 0; z-index: 100;
    background: rgba(0,0,0,0.7); backdrop-filter: blur(20px) saturate(1.5);
    border-bottom: 1px solid var(--border);
    padding: 12px 24px; display: flex; align-items: center; justify-content: space-between;
}}
.nav-brand {{ display: flex; align-items: center; gap: 8px; font-weight: 600; font-size: 15px; letter-spacing: -0.3px; }}
.nav-brand svg {{ width: 20px; height: 20px; color: var(--text-1); }}

.nav-actions {{ display: flex; gap: 12px; align-items: center; flex: 1; justify-content: flex-end; max-width: 500px; }}
.search-box {{
    background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px;
    display: flex; align-items: center; padding: 6px 12px; gap: 8px; flex: 1;
    transition: border 0.3s var(--spring), box-shadow 0.3s var(--spring);
}}
.search-box:focus-within {{ border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent); }}
.search-box input {{ background: transparent; border: none; color: var(--text-1); outline: none; font-size: 14px; width: 100%; }}
.search-box input::placeholder {{ color: var(--text-3); }}
.search-box svg {{ color: var(--text-2); width: 14px; height: 14px; }}
.search-kbd {{
    font-size: 10px; background: var(--border); color: var(--text-2);
    padding: 2px 6px; border-radius: 4px; font-weight: 600; border: 1px solid var(--border-hover);
}}

select.dropdown {{
    background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px;
    color: var(--text-1); padding: 8px 12px; font-size: 13px; font-family: inherit;
    outline: none; cursor: pointer; appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' fill='none' stroke='%23888888' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='3 5 6 8 9 5'/%3E%3C/svg%3E");
    background-repeat: no-repeat; background-position: right 12px center; padding-right: 32px;
}}
select.dropdown:focus {{ border-color: var(--border-hover); }}

/* HERO */
.hero {{ position: relative; padding: 80px 24px 60px; text-align: center; overflow: hidden; }}
.glow {{
    position: absolute; top: -100px; left: 50%; transform: translateX(-50%);
    width: 800px; height: 400px;
    background: radial-gradient(ellipse at center, rgba(99,102,241,0.15) 0%, rgba(0,0,0,0) 60%);
    pointer-events: none; z-index: 0;
    animation: pulseGlow 8s ease-in-out infinite;
}}
.hero-content {{ position: relative; z-index: 1; max-width: 800px; margin: 0 auto; }}
.badge {{ 
    display: inline-block; background: var(--bg-card); border: 1px solid var(--border);
    padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 500;
    color: var(--text-2); margin-bottom: 24px; letter-spacing: 0.5px;
}}
.hero h1 {{ 
    font-size: 48px; font-weight: 700; margin-bottom: 16px; letter-spacing: -2px; line-height: 1.1;
    background: linear-gradient(180deg, #FFFFFF 0%, #A1A1AA 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}}
.hero p {{ color: var(--text-2); font-size: 18px; max-width: 500px; margin: 0 auto; line-height: 1.5; }}

/* MAIN CONTENT */
.container {{ max-width: 1000px; margin: 0 auto; padding: 0 24px 80px; width: 100%; }}
.section-title {{ font-size: 18px; font-weight: 600; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 12px; }}

/* GRID */
.grid {{ display: grid; gap: 16px; grid-template-columns: 1fr; }}
@media (min-width: 768px) {{ .grid {{ grid-template-columns: repeat(2, 1fr); }} }}

/* CARDS */
.nav-card {{ 
  display: flex; align-items: flex-start; background: var(--bg-card); padding: 20px; 
  border-radius: 16px; border: 1px solid var(--border); text-decoration: none; color: inherit;
  transition: transform 0.3s var(--spring), border-color 0.3s, background 0.3s, box-shadow 0.3s;
}}
.nav-card:hover {{ 
    border-color: var(--border-hover); background: rgba(20,20,20,0.8);
    box-shadow: 0 8px 30px rgba(0,0,0,0.5), 0 0 0 1px rgba(99,102,241,0.1);
    transform: translateY(-2px);
}}
.nav-card:active {{ transform: translateY(0) scale(0.98); background: var(--bg-hover); }}
.nav-icon-wrap {{ 
    background: linear-gradient(135deg, rgba(99,102,241,0.1) 0%, rgba(168,85,247,0.1) 100%);
    width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; 
    border-radius: 10px; margin-right: 16px; border: 1px solid rgba(99,102,241,0.2);
    color: var(--accent); flex-shrink: 0;
}}
.nav-icon-wrap svg {{ width: 20px; height: 20px; }}
.nav-info {{ flex: 1; }}
.nav-title-row {{ display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }}
.nav-title {{ font-size: 15px; font-weight: 600; letter-spacing: -0.2px; }}
.nav-badge {{ background: var(--border); padding: 2px 6px; border-radius: 6px; font-size: 10px; font-weight: 600; text-transform: uppercase; color: var(--text-2); }}
.nav-sub {{ font-size: 13px; color: var(--text-2); line-height: 1.4; }}
.nav-arrow {{ color: var(--border-hover); display: flex; align-items: center; height: 40px; }}
.nav-arrow svg {{ width: 18px; height: 18px; transition: color 0.2s, transform 0.2s var(--spring); }}
.nav-card:hover .nav-arrow svg {{ color: var(--text-1); transform: translateX(4px); }}

.empty-state {{ text-align: center; padding: 40px; color: var(--text-3); font-size: 14px; display: none; grid-column: 1 / -1; }}

@media (max-width: 600px) {{
    .navbar {{ flex-direction: column; align-items: stretch; gap: 12px; padding: 16px; }}
    .nav-actions {{ max-width: none; }}
    .hero h1 {{ font-size: 36px; }}
    .hero {{ padding: 40px 16px; }}
    .search-kbd {{ display: none; }}
}}
</style>
</head>
<body>
    
    <nav class="navbar animate-fade" style="animation-delay: 0.1s">
        <a href="index.html" class="nav-brand" aria-label="Home">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
                <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
                <line x1="12" y1="22.08" x2="12" y2="12"></line>
            </svg>
            Prsh Capital
        </a>
        <div class="nav-actions">
            <select class="dropdown" id="filterCategory" aria-label="Filter category">
                <option value="all">All Research</option>
                <option value="time-range">Time Range</option>
            </select>
            <div class="search-box">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                <input type="text" id="searchInput" placeholder="Search dashboards...">
                <div class="search-kbd">/</div>
            </div>
        </div>
    </nav>

    <div class="hero">
        <div class="glow"></div>
        <div class="hero-content">
            <div class="badge animate-up" style="animation-delay: 0.1s">Research Hub</div>
            <h1 class="animate-up" style="animation-delay: 0.15s">Explore quantitative<br>insights & data.</h1>
            <p class="animate-up" style="animation-delay: 0.2s">Access interactive probability matrices, R-multiple extensions, and heatmap correlations across NQ and ES.</p>
        </div>
    </div>

    <div class="container">
        <div class="section-title animate-up" style="animation-delay: 0.25s">
            <span>Dashboards</span>
            <span id="resultCount" style="font-size:13px; color:var(--text-2); font-weight:400;">{len(html_files)} results</span>
        </div>
        <div class="grid" id="cardGrid">
            {links_html}
            <div class="empty-state" id="emptyState">No dashboards found matching your criteria.</div>
        </div>
    </div>

    <script>
        const searchInput = document.getElementById('searchInput');
        const filterCategory = document.getElementById('filterCategory');
        const cards = document.querySelectorAll('.nav-card');
        const emptyState = document.getElementById('emptyState');
        const resultCount = document.getElementById('resultCount');

        // Keyboard accessibility for search
        document.addEventListener('keydown', (e) => {{
            if (e.key === '/' && document.activeElement !== searchInput) {{
                e.preventDefault();
                searchInput.focus();
            }}
        }});

        function filterCards() {{
            const query = searchInput.value.toLowerCase().trim();
            const category = filterCategory.value;
            let visibleCount = 0;

            cards.forEach(card => {{
                const title = card.getAttribute('data-title');
                const cardCat = card.getAttribute('data-category');
                
                const matchesSearch = title.includes(query);
                const matchesCategory = category === 'all' || cardCat === category;

                if (matchesSearch && matchesCategory) {{
                    card.style.display = 'flex';
                    visibleCount++;
                }} else {{
                    card.style.display = 'none';
                }}
            }});

            if (visibleCount === 0) {{
                emptyState.style.display = 'block';
            }} else {{
                emptyState.style.display = 'none';
            }}
            resultCount.textContent = visibleCount + ' results';
        }}

        searchInput.addEventListener('input', filterCards);
        filterCategory.addEventListener('change', filterCards);
    </script>
</body>
</html>"""

with open(os.path.join(OUT_DIR, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(index_html)
print("Created animated and accessible index.html")
