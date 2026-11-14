"""Rebuild everything of the Ringtail body, deterministically: meshes, QA, AO, coats, portraits.

usage: python -I make_ringtails.py [--steps meshes,qa,coats,portraits] [--out E:/PandabornDev/build/characters/out]

  meshes     build_ringtail.py ADULT/CHILD -> <out>/RingtailAdult|RingtailChild.Model.timbermesh (+ .paint.npz)
  qa         qa_ringtail.py on both (format checks fail the run; motion metrics -> <out>/qa_adult|child.json)
  coats      AO bake + paint_ringtail.py -> mod/PandabornFactions/Materials/Pandaborn/Ringtails/{Adult,Child}/*.png
  portraits  make_portraits.py -> mod/PandabornFactions/Sprites/Pandaborn/Avatars/Ringtail*.png (+ .meta.json)

Inputs (never committed): the vanilla beaver meshes and textures dumped from the owner's own install into
E:/PandabornDev/reference/vanilla-characters (see art/characters/Ringtail/README.md).
The meshes stay on E: (about 108 MB and 64 MB); the build copies them into the mod (see docs/tech/ringtail-body.md).
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
PY = sys.executable
PANDA = r'E:\PandabornDev\assets\Pandaborn-Reskin-release\Characters\Beaver'


def run(*args):
    print('>', ' '.join(os.path.basename(a) if i == 1 else a for i, a in enumerate(args)))
    subprocess.run([PY, '-I'] + list(args), check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--steps', default='meshes,qa,coats,portraits')
    ap.add_argument('--out', default=r'E:\PandabornDev\build\characters\out')
    a = ap.parse_args()
    steps = a.steps.split(',')
    os.makedirs(a.out, exist_ok=True)
    mesh = {k: os.path.join(a.out, f'Ringtail{k.capitalize()}.Model.timbermesh') for k in ('adult', 'child')}
    if 'meshes' in steps:
        for k in ('adult', 'child'):
            run(os.path.join(HERE, 'build_ringtail.py'), k.upper(), mesh[k])
    if 'qa' in steps:
        for k, panda in (('adult', 'BeaverAdult'), ('child', 'BeaverChild')):
            run(os.path.join(HERE, 'qa_ringtail.py'), k.upper(), mesh[k], '--json', os.path.join(a.out, f'qa_{k}.json'),
                '--compare', os.path.join(PANDA, panda + '.Model.timbermesh'))
    coats = os.path.join(REPO, 'mod', 'PandabornFactions', 'Materials', 'Pandaborn', 'Ringtails')
    if 'coats' in steps:
        for k in ('adult', 'child'):
            dst = os.path.join(coats, k.capitalize())
            run(os.path.join(HERE, 'paint_ringtail.py'), k.upper(), mesh[k].replace('.timbermesh', '') + '.paint.npz', dst, '--rebake')
    if 'portraits' in steps:
        av = os.path.join(REPO, 'mod', 'PandabornFactions', 'Sprites', 'Pandaborn', 'Avatars')
        run(os.path.join(HERE, 'make_portraits.py'), av)
        for f in os.listdir(av):
            if f.startswith('Ringtail') and f.endswith('.png') and not os.path.exists(os.path.join(av, f + '.meta.json')):
                with open(os.path.join(av, f + '.meta.json'), 'w', encoding='utf-8') as fh:
                    fh.write('{"isSprite": true}')


if __name__ == '__main__':
    main()
