"""Refresh only a generated demo Kconfig index after adding manifest linkfiles."""
from pathlib import Path
workspace = Path.cwd()
output = workspace / 'cmake_out/vela_goldfish-arm64-v8a-ap/apps'
candidates = list(output.glob('*_packages_demos_Kconfig'))
if len(candidates) != 1:
    raise SystemExit('Expected one generated demos Kconfig index')
index = candidates[0]
text = index.read_text()
apps = workspace / 'apps/packages/demos'
for directory in sorted(apps.iterdir()):
    kconfig = directory / 'Kconfig'
    if not kconfig.is_file():
        continue
    line = f'source "{kconfig}"'
    if line not in text:
        text = text.replace('endmenu', line + '\nendmenu', 1)
index.write_text(text)
print('Refreshed generated demo Kconfig index')
