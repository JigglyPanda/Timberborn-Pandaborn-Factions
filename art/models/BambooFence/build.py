"""Bamboo Fence (decoration): a modular 1x1 fence on the vanilla Wood Fence's MergeableObjectModel. The game picks one
of six variant models by which neighbours are fences (code letters down/left/up/right = -z/-x/+z/+x, rotated as
needed): 0000 alone, 0001 one side, 1010 straight, 0011 corner, 0111 tee, 1111 cross.

Each piece: a stout bamboo post in the middle on a river stone, and for each connected side a half-section of two
lashed horizontal culms with thin upright canes between them, gold and green culms mixed, a little uneven.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import json  # noqa: E402
import numpy as np  # noqa: E402
from building import Model, block  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

VARIANTS = {"0000": "", "0001": "L", "1010": "LR", "0011": "UR", "0111": "LUR", "1111": "DLUR"}
DIRS = {"D": (0, -1), "L": (-1, 0), "U": (0, 1), "R": (1, 0)}
C = np.array([0.5, 0.0, 0.5])


def piece(g, sides):
    K.stones(g, 0.42, 0.42, 0.58, 0.58, y=-0.01, size=0.16, h=0.06, ring=False, skip=0.0)
    K.pole(g, (0.5, 0.0, 0.5), (0.5, 0.78, 0.5), r=0.045, material=BAMBOO_GOLD, sides=6, bend=0.005)
    sides = sides or "L"    # a lone post still gets a stub so it reads as fence
    for s in sides:
        dx, dz = DIRS[s]
        d = np.array([dx, 0.0, dz])
        end = C + d * 0.5
        for y in (0.3, 0.6):
            K.pole(g, C + d * 0.04 + [0, y + g.jitter(0.02), 0], end + [0, y + g.jitter(0.02), 0], r=0.022,
                   material=BAMBOO_GOLD, sides=4, bend=0.0, caps=False)
        K.lashing(g, C + d * 0.05 + [0, 0.6, 0], (0, 1, 0), r=0.05)
        for k in range(3):
            p = C + d * (0.14 + 0.13 * k)
            K.pole(g, p + [0, 0.02, 0], p + [0, 0.66 + g.jitter(0.04), 0], r=0.013,
                   material=BAMBOO_GREEN if (k + len(sides)) % 2 else BAMBOO_GOLD, sides=3, bend=0.0, caps=False)


models = {}
for code, sides in VARIANTS.items():
    m = Model("BambooFence" + code, size=(1, 1, 1), seed=233 + int(code, 2), stand_in="WoodFence.Folktails")
    m.out = os.path.join(os.path.dirname(m.out), "BambooFence")
    piece(m.geo, sides)
    rep = m.build(write_json=False)
    models[code] = rep["triangles"]
    # the shared construction stage is the 0000 piece's
    if code != "0000":
        os.remove(os.path.join(m.out, f"BambooFence{code}.ConstructionStage0.Model.timbermesh"))
os.replace(os.path.join(m.out, "BambooFence0000.ConstructionStage0.Model.timbermesh"),
           os.path.join(m.out, "BambooFence.ConstructionStage0.Model.timbermesh"))
doc = {"id": "BambooFence", "standIn": "WoodFence.Folktails",
       "generatedBy": "art/models/BambooFence/build.py (src/pipeline/kit); AI-generated, code-made",
       "models": {"finished": None, "constructionStage0": "BambooFence.ConstructionStage0.Model",
                  "mergeableVariants": {code: f"BambooFence{code}.Model" for code in VARIANTS}},
       "mergeableObjectModel": {"ModelNamePrefix": "BambooFence",
                                "children": {f"BambooFence{c}": f"BambooFence{c}.Model" for c in VARIANTS}},
       "size": {"X": 1, "Y": 1, "Z": 1}, "blocks": None, "entrance": None, "slots": [], "animatedNodes": [],
       "colliders": [], "attachments": [],
       "triangles": {"finished": max(models.values()), "constructionStage0": None, "vanillaMedianForFootprint": 300,
                     "perVariant": models},
       "notes": ["Replace the vanilla Wood Fence's six #Finished children WoodFence<code> with BambooFence<code> "
                 "(same codes) and set MergeableObjectModelSpec.ModelNamePrefix to 'BambooFence'."]}
json.dump(doc, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "model.json"), "w"), indent=1)
print(models)
