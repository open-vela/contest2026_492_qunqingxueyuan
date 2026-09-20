"""Package only final report and user-recorded video, never source or logs."""
import argparse
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--video', type=Path, default=ROOT / 'submission/final/FlyReflex_演示视频.mp4')
    a = p.parse_args()
    folder = ROOT / 'submission/final'
    reports = [folder / ('FlyReflex_技术报告' + ext) for ext in ('.docx', '.pdf')]
    for path in reports + [a.video]:
        if not path.is_file() or path.stat().st_size == 0:
            p.error(f'Missing final deliverable: {path}')
    if a.video.name != 'FlyReflex_演示视频.mp4':
        p.error('Final video must be named FlyReflex_演示视频.mp4; old browser footage is not a final video')
    ffprobe = shutil.which('ffprobe')
    if ffprobe:
        data = json.loads(subprocess.check_output([ffprobe, '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', str(a.video)]))
        seconds = float(data['format']['duration'])
        if not 0 < seconds <= 300:
            p.error(f'Video duration {seconds:.2f}s is outside (0, 300]')
        print(f'Video duration: {seconds:.2f}s')
    else:
        print('ffprobe unavailable: duration not automatically verified; final video must be <= 5 minutes.')
    target = ROOT / 'submission/群青学院-FlyReflex-contest2026_492_qunqingxueyuan.zip'
    temp = target.with_suffix('.zip.tmp')
    with zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED) as z:
        for path in reports + [a.video]:
            z.write(path, path.name)
    temp.replace(target)
    print(target)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
