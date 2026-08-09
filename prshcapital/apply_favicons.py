import glob
import re

html_files = glob.glob("*.html")
for f_name in html_files:
    with open(f_name, "r", encoding="utf-8") as f:
        content = f.read()

    # If it already has the svg icon link, update it to v=4
    if 'type="image/svg+xml"' in content:
        content = re.sub(
            r'<link rel="icon" type="image/svg\+xml" href="[^"]*">',
            '<link rel="icon" type="image/svg+xml" href="icon.svg?v=4">',
            content
        )
    else:
        # Otherwise, insert it after the png or ico link
        if '<link rel="icon" type="image/x-icon"' in content:
            content = content.replace(
                '<link rel="icon" type="image/x-icon" href="favicon.ico">',
                '<link rel="icon" type="image/x-icon" href="favicon.ico">\n<link rel="icon" type="image/svg+xml" href="icon.svg?v=4">'
            )
        elif '<head>' in content:
            content = content.replace(
                '<head>',
                '<head>\n<link rel="icon" type="image/svg+xml" href="icon.svg?v=4">'
            )
            
    with open(f_name, "w", encoding="utf-8") as f:
        f.write(content)

print("Updated SVG favicons in all HTML files.")
