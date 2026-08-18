from pathlib import Path
import re

path = Path('app/main.py')
text = path.read_text(encoding='utf-8')

if 'from app.demo_template import render_demo_html' in text:
    print('Demo generator already upgraded; nothing to do.')
    raise SystemExit(0)

pattern = re.compile(r"def demo_html\(data\):.*?\n(?=def slugify\(value\):)", re.S)
replacement = '''def demo_html(data):
    from app.demo_template import render_demo_html
    return render_demo_html(data)

'''
new_text, count = pattern.subn(replacement, text, count=1)
if count != 1:
    raise SystemExit('Could not locate the existing demo_html function; stopping without changes.')

path.write_text(new_text, encoding='utf-8')
print('Replaced the old demo generator with the advanced template.')
