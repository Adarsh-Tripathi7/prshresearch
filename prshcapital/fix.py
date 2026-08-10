import glob, re

for f in glob.glob('*.html'):
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    content = re.sub(r'style="min-width:\s*600px;?"', 'style=""', content)
    content = re.sub(r'<script src="main.js[^"]*"', '<script src="main.js?v=4"', content)
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)
print("done")
