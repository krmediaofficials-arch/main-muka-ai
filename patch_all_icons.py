from pathlib import Path

p = Path("/opt/muka/index.html")
data = p.read_bytes()

replacements = [
    # Sidebar
    (b'<span class="ico">?</span>MUKA AI Chat', b'<span class="ico">&#128172;</span>MUKA AI Chat'),
    (b'<span class="ico">?</span>Recent Chats', b'<span class="ico">&#128196;</span>Recent Chats'),
    (b'<span class="ico">?</span>Client AIs', b'<span class="ico">&#128101;</span>Client AIs'),
    (b'<span class="ico">?</span>Client Management', b'<span class="ico">&#9881;</span>Client Management'),
    (b'<span class="ico">??</span>Trash Bin', b'<span class="ico">&#128465;</span>Trash Bin'),
    (b'<span class="ico">?</span>Meetings', b'<span class="ico">&#128197;</span>Meetings'),
    (b'<span class="ico">?</span>Project Schedule', b'<span class="ico">&#128198;</span>Project Schedule'),
    (b'<span class="ico">?</span>Team & Employees', b'<span class="ico">&#128101;</span>Team & Employees'),
    (b'<span class="ico">?</span>Demo & Training', b'<span class="ico">&#127891;</span>Demo & Training'),
    (b'<span class="ico">?</span>Mail Box', b'<span class="ico">&#9993;</span>Mail Box'),
    (b'<span class="ico">?</span>App Connections', b'<span class="ico">&#128279;</span>App Connections'),
    (b'<span class="ico">?</span>Creative Studio', b'<span class="ico">&#127912;</span>Creative Studio'),
    (b'<span class="ico">?</span>Tools Hub', b'<span class="ico">&#128295;</span>Tools Hub'),
    (b'<span class="ico">?</span>Google Maps Manager', b'<span class="ico">&#128205;</span>Google Maps Manager'),

    # Header
    (b'<button class="logout" id="logout" title="Logout">?</button>', b'<button class="logout" id="logout" title="Logout">&#10162;</button>'),
    (b'<div class="header-left"><button class="btn" id="menu">?</button>', b'<div class="header-left"><button class="btn" id="menu">&#9776;</button>'),
    (b'<div class="status">? Online', b'<div class="status">&#9679; Online'),
    (b'<div class="search">? <input', b'<div class="search">&#128269; <input'),

    # Dashboard module cards
    (b'<div class="card module" data-page="connections"><div class="icon">?</div><h3>App Connections</h3>',
     b'<div class="card module" data-page="connections"><div class="icon">&#128279;</div><h3>App Connections</h3>'),
    (b'<div class="card module" data-page="studio"><div class="icon">?</div><h3>Creative Studio</h3>',
     b'<div class="card module" data-page="studio"><div class="icon">&#127912;</div><h3>Creative Studio</h3>'),
    (b'<div class="card module" data-page="tools"><div class="icon">?</div><h3>Tools Hub</h3>',
     b'<div class="card module" data-page="tools"><div class="icon">&#128295;</div><h3>Tools Hub</h3>'),
    (b'<div class="card module" data-page="recent"><div class="icon">?</div><h3>Recent Chats</h3>',
     b'<div class="card module" data-page="recent"><div class="icon">&#128196;</div><h3>Recent Chats</h3>'),
    (b'<div class="card module"><div class="icon">?</div><h3>Workspace Search</h3>',
     b'<div class="card module"><div class="icon">&#128269;</div><h3>Workspace Search</h3>'),

    # Chat buttons
    (b'id="mukaVoiceBtn" type="button">? Voice', b'id="mukaVoiceBtn" type="button">&#127908; Voice'),
    (b'id="mukaSendBtn" type="button">? Send', b'id="mukaSendBtn" type="button">&#10148; Send'),

    # Client AI card
    (b'<div class="card"><div class="icon">?</div><h3>Roots & Leaves Collection</h3>',
     b'<div class="card"><div class="icon">&#127807;</div><h3>Roots & Leaves Collection</h3>'),
    (b'<div class="card"><div class="icon">R</div><h3>Roots & Leaves Collection</h3>',
     b'<div class="card"><div class="icon">&#127807;</div><h3>Roots & Leaves Collection</h3>'),

    # Refresh
    (b'<button type="button" class="btn" onclick="loadClientTrash()">? Refresh</button>',
     b'<button type="button" class="btn" onclick="loadClientTrash()">&#8635; Refresh</button>'),

    # Training
    (b'<div class="card"><div class="icon">?</div><h3>MUKA AI Demo</h3>',
     b'<div class="card"><div class="icon">&#9654;</div><h3>MUKA AI Demo</h3>'),
    (b'<div class="card"><div class="icon">?</div><h3>Team Training</h3>',
     b'<div class="card"><div class="icon">&#127891;</div><h3>Team Training</h3>'),
    (b'<div class="card"><div class="icon">?</div><h3>Training Progress</h3>',
     b'<div class="card"><div class="icon">&#128202;</div><h3>Training Progress</h3>'),

    # Business Email
    (b'<div class="card"><div class="icon">?</div><h3>Business Email</h3>',
     b'<div class="card"><div class="icon">&#9993;</div><h3>Business Email</h3>'),

    # Studio
    (b'<div class="card"><div class="icon">?</div><h3>Image Upload</h3>',
     b'<div class="card"><div class="icon">&#128228;</div><h3>Image Upload</h3>'),
    (b'<div class="card"><div class="icon">?</div><h3>Image Generate</h3>',
     b'<div class="card"><div class="icon">&#10024;</div><h3>Image Generate</h3>'),
    (b'<div class="card"><div class="icon">??</div><h3>Image Editing</h3>',
     b'<div class="card"><div class="icon">&#9998;</div><h3>Image Editing</h3>'),
    (b'<div class="card"><div class="icon">?</div><h3>Video Editing</h3>',
     b'<div class="card"><div class="icon">&#127909;</div><h3>Video Editing</h3>'),

    # Tools
    (b'<div class="card"><div class="icon">?</div><h3>Web Research</h3>',
     b'<div class="card"><div class="icon">&#128269;</div><h3>Web Research</h3>'),
    (b'<div class="card"><div class="icon">?</div><h3>Instagram Studio</h3>',
     b'<div class="card"><div class="icon">&#128247;</div><h3>Instagram Studio</h3>'),
    (b'<div class="card"><div class="icon">?</div><h3>Report Builder</h3>',
     b'<div class="card"><div class="icon">&#128196;</div><h3>Report Builder</h3>'),
    (b'<div class="card"><div class="icon">??</div><h3>Image Edit</h3>',
     b'<div class="card"><div class="icon">&#9998;</div><h3>Image Edit</h3>'),

    # Google Maps workspace
    (b'<div style="font-size:50px;color:#a993ff">?</div><h3>Google Maps Workspace</h3>',
     b'<div style="font-size:50px;color:#a993ff">&#128205;</div><h3>Google Maps Workspace</h3>'),

    # Dynamic Recent Chats / Client Trash
    (b'<div class="icon">?</div>\'+',
     b'<div class="icon">&#128172;</div>\'+'),
    (b'<div class="icon">??</div>\'+',
     b'<div class="icon">&#128465;</div>\'+'),
]

changed = 0

for old, new in replacements:
    if old in data:
        data = data.replace(old, new)
        changed += 1

p.write_bytes(data)

print(f"ICON_PATCH_OK replacements={changed}")
