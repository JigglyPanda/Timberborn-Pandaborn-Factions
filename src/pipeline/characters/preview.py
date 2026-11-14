"""Render a preview scene: pose_export.py (venv) then bl_render.py (headless Blender).

usage: python -I preview.py scene.json
Environment: BLENDER (default: the portable Blender 4.5 on E:).
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER = os.environ.get('BLENDER', r'E:\PandabornDev\tools\blender-4.5-lts\blender-4.5.16-windows-x64\blender.exe')
ENV = dict(os.environ, BLENDER_USER_RESOURCES=r'E:\PandabornDev\tools\blender-userdata',
           TEMP=r'E:\PandabornDev\tools\tmp', TMP=r'E:\PandabornDev\tools\tmp', PYTHONDONTWRITEBYTECODE='1')


def run(scene_path):
    sc = json.load(open(scene_path, encoding='utf-8'))
    subprocess.run([sys.executable, '-I', os.path.join(HERE, 'pose_export.py'), scene_path], check=True, env=ENV)
    r = subprocess.run([BLENDER, '-b', '--factory-startup', '--python', os.path.join(HERE, 'bl_render.py'), '--',
                        sc['out_npz']], env=ENV, capture_output=True, text=True)
    lines = [l for l in r.stdout.splitlines() if l.startswith('rendered') or 'Error' in l or 'Traceback' in l]
    print('\n'.join(lines))
    if r.returncode != 0 or not any(l.startswith('rendered') for l in lines):
        print(r.stdout[-3000:], r.stderr[-3000:])
        raise SystemExit('blender failed')


if __name__ == '__main__':
    run(sys.argv[1])
