import re

replacements = [
    ('\u2611', '[x]'),
    ('\u2610', '[ ]'),
    ('\u2699\ufe0f', ''),
    ('\u2699', ''),
]

files = [
    'src/welcome/dispatch_view.py',
    'src/welcome/vehicle_view.py',
]

for path in files:
    with open(path, encoding='utf-8') as f:
        text = f.read()
    orig = text
    for old, new in replacements:
        text = text.replace(old, new)
    if text != orig:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f'Cleaned {path}')
    else:
        print(f'No changes: {path}')
