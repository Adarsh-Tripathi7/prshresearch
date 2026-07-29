import os
import glob

output_dir = r'd:\Antigravity\imobile ib dashboard'
base_url = 'https://prshcapital.netlify.app/'

# Generate robots.txt
robots_content = f'''User-agent: *
Allow: /

Sitemap: {base_url}sitemap.xml
'''
with open(os.path.join(output_dir, 'robots.txt'), 'w', encoding='utf-8') as f:
    f.write(robots_content)

# Generate sitemap.xml
html_files = glob.glob(os.path.join(output_dir, '*.html'))
sitemap_content = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']

for html_file in html_files:
    filename = os.path.basename(html_file)
    url = f'{base_url}{filename}'
    if filename == 'index.html':
        url = base_url
    
    sitemap_content.append(f'  <url>')
    sitemap_content.append(f'    <loc>{url}</loc>')
    sitemap_content.append(f'    <changefreq>daily</changefreq>')
    sitemap_content.append(f'    <priority>1.0</priority>' if filename == 'index.html' else f'    <priority>0.8</priority>')
    sitemap_content.append(f'  </url>')

sitemap_content.append('</urlset>')

with open(os.path.join(output_dir, 'sitemap.xml'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(sitemap_content))

print('Generated robots.txt and sitemap.xml')
