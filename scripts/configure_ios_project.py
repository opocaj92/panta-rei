"""Configure pygame-ios generated Xcode project without changing game code."""
import json
import plistlib
import shutil
from pathlib import Path

root = Path.cwd()
projects = [p for p in root.rglob('*.xcodeproj') if '.buildozer' not in p.parts]
if len(projects) != 1:
    raise SystemExit(f'Expected one generated Xcode project; found: {projects}')
project_dir = projects[0].parent
icon = root / 'assets/icons/panta_rei_1024.png'
if not icon.is_file():
    raise SystemExit(f'Missing icon: {icon}')

icon_sets = list(project_dir.rglob('AppIcon.appiconset'))
if not icon_sets:
    raise SystemExit('No AppIcon.appiconset in generated Xcode template; cannot set icon safely')
for icon_set in icon_sets:
    shutil.copy2(icon, icon_set / 'PantaRei-1024.png')
    # Universal 1024-point icon is supported by modern Xcode asset catalogs.
    (icon_set / 'Contents.json').write_text(json.dumps({
        'images': [{'filename': 'PantaRei-1024.png', 'idiom': 'universal',
                    'platform': 'ios', 'size': '1024x1024'}],
        'info': {'author': 'xcode', 'version': 1}
    }, indent=2) + '\n')

# Explicit landscape orientation in existing plist files (when supplied by template).
plists = [p for p in project_dir.rglob('Info.plist') if 'Build' not in p.parts]
for plist in plists:
    try:
        with plist.open('rb') as f:
            data = plistlib.load(f)
    except (ValueError, OSError, plistlib.InvalidFileException):
        continue
    if not isinstance(data, dict):
        continue
    orientations = ['UIInterfaceOrientationLandscapeLeft', 'UIInterfaceOrientationLandscapeRight']
    data['UISupportedInterfaceOrientations'] = orientations
    data['UISupportedInterfaceOrientations~ipad'] = orientations
    with plist.open('wb') as f:
        plistlib.dump(data, f)

# Also set orientation for projects with Xcode-generated Info.plist settings.
pbx = projects[0] / 'project.pbxproj'
if pbx.is_file():
    content = pbx.read_text()
    import re
    for key in ('INFOPLIST_KEY_UISupportedInterfaceOrientations',
                'INFOPLIST_KEY_UISupportedInterfaceOrientations~ipad'):
        # Only replace existing keys: don't guess Xcode project structure.
        content = re.sub(r'(?m)^(\s*)' + re.escape(key) + r'\s*=\s*[^;]*;',
                         lambda m: m.group(1) + key + ' = "UIInterfaceOrientationLandscapeLeft UIInterfaceOrientationLandscapeRight";', content)
    pbx.write_text(content)
print(f'Configured {len(icon_sets)} app icon set(s) and {len(plists)} Info.plist candidate(s) in {project_dir}')
