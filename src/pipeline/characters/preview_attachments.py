"""Offline check of the hat and basket on both peoples: Inkpaw adult and Ringtail adult, each wearing the hat or the
basket on its node, in a few animations; front 3/4, back 3/4 and side.

usage: python -I preview_attachments.py <preview dir from make_attachments.py> <out dir> [--anims idle,walk,...]
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FACTION = r'E:\PandabornDev\build\PandabornFactions'
OUT = r'E:\PandabornDev\build\characters\out'
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('preview'); ap.add_argument('out')
    ap.add_argument('--anims', default='idle,walk,BeaverAdult_walk_box,BeaverAdult_planting,BeaverAdult_sitting')
    ap.add_argument('--name', default='attach')
    a = ap.parse_args()
    idx = json.load(open(os.path.join(a.preview, 'preview_index.json')))
    ink = dict(model=os.path.join(FACTION, r'Characters\Pandaborn\InkpawAdult.Model.timbermesh'),
               texture=os.path.join(FACTION, r'Materials\Pandaborn\Inkpaws\Adult\InkpawAdult1.png'))
    rt = dict(model=os.path.join(OUT, 'RingtailAdult.Model.timbermesh'),
              texture=os.path.join(REPO, r'mod\PandabornFactions\Materials\Pandaborn\Ringtails\Adult\RingtailAdultCoat1.png'))
    anims = [x for x in a.anims.split(',') if x]
    items = []
    x = -(len(anims) * 2 - 1) * 0.35
    for an in anims:
        for who, att, node in ((ink, 'ConicalHat', '#Head'), (rt, 'BackBasket', '#Backpack'), (ink, 'BackBasket', '#Backpack')):
            items.append(dict(model=who['model'], texture=who['texture'], anim=an, frame='0.4', offset=[x, 0]))
            pk = len(items) - 1
            for mat, (mesh, tex) in idx[att].items():
                items.append(dict(parent=pk, node=node, model=mesh, texture=tex))
            x += 0.47
    W = x + 0.5
    cams = []
    for view, az, el in (('front', 25, 12), ('back', 200, 18), ('side', 90, 8)):
        cams.append(dict(out=os.path.join(a.out, f'{a.name}_{view}.png'), target=[0, 0.3, 0], az=az, el=el, dist=W * 1.25, lens=50))
    sc = dict(out_npz=os.path.join(a.out, a.name + '.npz'), items=items, cameras=cams, size=[1800, 640], samples=32)
    os.makedirs(a.out, exist_ok=True)
    p = os.path.join(a.out, a.name + '.json')
    json.dump(sc, open(p, 'w'), indent=1)
    subprocess.run([sys.executable, '-I', os.path.join(HERE, 'preview.py'), p], check=True)


if __name__ == '__main__':
    main()
