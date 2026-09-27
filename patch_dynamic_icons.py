from pathlib import Path

p = Path("/opt/muka/index.html")
data = p.read_bytes()

replacements = [
    (
        b'''c.innerHTML='<div class="icon">?</div><h3>'+esc(n.trim())+'</h3>''',
        b'''c.innerHTML='<div class="icon">&#128295;</div><h3>'+esc(n.trim())+'</h3>'''
    ),
    (
        b'''c.innerHTML='<div class="icon">?</div><h3>'+esc(n.trim())+'</h3><p>Meeting created''',
        b'''c.innerHTML='<div class="icon">&#128197;</div><h3>'+esc(n.trim())+'</h3><p>Meeting created'''
    ),
]

changed = 0
for old, new in replacements:
    if old in data:
        data = data.replace(old, new)
        changed += 1

p.write_bytes(data)
print(f"DYNAMIC_ICON_PATCH_OK replacements={changed}")
