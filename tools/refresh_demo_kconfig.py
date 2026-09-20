"""Refresh only a generated demo Kconfig index after adding manifest linkfiles."""
from pathlib import Path
workspace = Path.cwd()
output = workspace / 'cmake_out/vela_goldfish-arm64-v8a-ap/apps'
candidates = list(output.glob('*_packages_demos_Kconfig'))
apps = workspace / 'apps/packages/demos'
if not (apps / 'CMakeLists.txt').is_file():
    raise SystemExit('Missing packages/demos checkout; sync that public repository first')
if len(candidates) > 1:
    raise SystemExit('Ambiguous generated demos Kconfig indexes')
if candidates:
    index = candidates[0]
else:
    # A workspace configured before repo sync may have only the Packages index.
    # Repair generated build metadata, never a public source Kconfig.
    parents = list(output.glob('*_packages_Kconfig'))
    if len(parents) != 1:
        raise SystemExit('Expected one generated Packages Kconfig index')
    index = output / (str(apps / 'Kconfig').replace('/', '_') )
    index.write_text('menu "Demos"\nendmenu # Demos\n')
    parent = parents[0]
    parent_text = parent.read_text()
    include = f'source "{index}"'
    if include not in parent_text:
        parent.write_text(parent_text.replace('endmenu', include + '\nendmenu', 1))
text = index.read_text()
for directory in sorted(apps.iterdir()):
    kconfig = directory / 'Kconfig'
    if not kconfig.is_file():
        continue
    line = f'source "{kconfig}"'
    if line not in text:
        text = text.replace('endmenu', line + '\nendmenu', 1)
index.write_text(text)
print('Refreshed generated demo Kconfig index')
