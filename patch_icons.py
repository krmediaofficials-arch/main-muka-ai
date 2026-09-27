from pathlib import Path

p = Path("/opt/muka/index.html")
data = p.read_bytes()

replacements = [
    (b'<div class="icon">?</div><h3>Client AIs</h3>', b'<div class="icon">R</div><h3>Client AIs</h3>'),
    (b'<div class="icon">?</div><h3>Mail Box</h3>', b'<div class="icon">M</div><h3>Mail Box</h3>'),
    (b'<div class="icon">?</div><h3>Meetings</h3>', b'<div class="icon">C</div><h3>Meetings</h3>'),
    (b'<div class="icon">?</div><h3>Project Schedule</h3>', b'<div class="icon">P</div><h3>Project Schedule</h3>'),
    (b'<div class="icon">?</div><h3>Team & Employees</h3>', b'<div class="icon">T</div><h3>Team & Employees</h3>'),
    (b'<div class="icon">?</div><h3>Demo & Training</h3>', b'<div class="icon">D</div><h3>Demo & Training</h3>'),
    (b'<div class="icon">?</div><h3>Google Maps Manager</h3>', b'<div class="icon">G</div><h3>Google Maps Manager</h3>'),
]

changed = 0
for old, new in replacements:
    if old in data:
        data = data.replace(old, new)
        changed += 1

p.write_bytes(data)
print(f"ICON_PATCH_OK replacements={changed}")
