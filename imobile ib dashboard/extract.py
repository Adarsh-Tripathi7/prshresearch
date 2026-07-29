import glob, re, json, os
os.makedirs('data', exist_ok=True)
for f in glob.glob('*.html'):
  content = open(f, encoding='utf-8').read()
  match = re.search(r'const _D = (\{.*?\});', content, re.DOTALL)
  if match:
    open('data/' + f.replace('.html', '.json'), 'w', encoding='utf-8').write(match.group(1))
    print(f'Extracted {f}')
