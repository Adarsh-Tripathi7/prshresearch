import glob
import re

def update_colors(text):
    # We only want to update colors inside the light mode definitions
    # So we can search for the :root[data-theme='light'] block and replace within it
    
    # Replace in index.html specifically:
    text = text.replace("--bg: #fdfbf7;", "--bg: #f5f0e6;")
    text = text.replace("--bg-card: #ffffff;", "--bg-card: #fcfbf8;")
    text = text.replace("--bg-surface: #f4f1ea;", "--bg-surface: #ebe3d5;")
    text = text.replace("--bg-hover: #f4f1ea;", "--bg-hover: #ebe3d5;")
    text = text.replace("--bg-hover: #e8e4dc;", "--bg-hover: #dcd2c2;") # in styles.css it was --bg-hover: #e8e4dc
    text = text.replace("--border: #e8e4dc;", "--border: #dcd2c2;")
    text = text.replace("--border-hover: #d6d1c6;", "--border-hover: #c6bba8;")
    
    text = text.replace("rgba(248,250,252,0.95)", "rgba(245,240,230,0.95)")
    text = text.replace("rgba(253,251,247,0.95)", "rgba(245,240,230,0.95)")
    
    # Update navbar / app-bar bg
    text = text.replace("rgba(255,255,255,0.85)", "rgba(252,251,248,0.85)")
    
    # Update hover card in index.html
    text = text.replace("background: #fdfbf7;", "background: #f5f0e6;")
    
    # Update modals and kbd in index.html
    text = text.replace("background: #e8e4dc;", "background: #dcd2c2;") # search-kbd
    text = text.replace("border-color: #d6d1c6;", "border-color: #c6bba8;") # search-kbd border
    
    text = text.replace(".vault-modal { background: #ffffff; border-color: #e8e4dc; }", ".vault-modal { background: #fcfbf8; border-color: #dcd2c2; }")
    text = text.replace(".admin-modal { background: #ffffff; border-color: #e8e4dc; }", ".admin-modal { background: #fcfbf8; border-color: #dcd2c2; }")
    
    # Update td first child in styles.css
    text = text.replace("td:first-child { background: #ffffff;", "td:first-child { background: #fcfbf8;")
    text = text.replace("th { background: rgba(248,250,252,0.95); }", "th { background: rgba(245,240,230,0.95); }")
    text = text.replace("th:first-child { background: #f1f5f9; }", "th:first-child { background: #ebe3d5; }")
    text = text.replace("tr:hover td:first-child { background: #f8fafc; }", "tr:hover td:first-child { background: #f5f0e6; }")
    
    # Update segments active
    text = text.replace(".segments button.active { background: #ffffff;", ".segments button.active { background: #fcfbf8;")
    
    return text

# 1. Update styles.css
with open("styles.css", "r", encoding="utf-8") as f:
    css_content = f.read()

css_content = update_colors(css_content)

with open("styles.css", "w", encoding="utf-8") as f:
    f.write(css_content)

# 2. Update all HTML files (specifically index.html has inline CSS)
html_files = glob.glob("*.html")
for f_name in html_files:
    with open(f_name, "r", encoding="utf-8") as f:
        content = f.read()
    
    content = update_colors(content)
    
    with open(f_name, "w", encoding="utf-8") as f:
        f.write(content)

print("Colors updated to warm beige.")
