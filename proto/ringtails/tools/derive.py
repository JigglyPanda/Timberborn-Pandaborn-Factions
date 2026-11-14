"""Derive the Ringtails test data (dev mod proto/ringtails) that rides on the generated Inkpaws build.

This is the data the catalogue lane will own (docs/tech/two-peoples.md, "For the catalogue lane"); until then it lives in
the dev mod. Writes into proto/ringtails/mod:
  * Characters/Pandaborn/RingtailAdult|RingtailChild.Inkpaws   hidden Ringtail templates (in no template collection),
    real red panda body (ringtail-body lane), coats and avatars from the faction build, PandabornRingtailSpec
  * Characters/Pandaborn/InkpawAdult|InkpawChild.Inkpaws       merges: PandabornRingtailsSpec (adult), the save alias
  * Buildings/Pandaborn/.../PandabornNight*Post.Inkpaws         merges: PandabornNightPostSpec (+ a science cost)
  * Buildings/Pandaborn/Housing/PandabornMoonLoft.Inkpaws        merge: PandabornMoonLoftSpec, no ProcreationHouseSpec
  * WorkerTypes/Pandaborn/WorkerType.PandabornRingtail           the worker type (must stay in data forever: saves name it)
  * WorkerOutfits/Pandaborn/WorkerOutfit.<Id>.PandabornRingtail.Inkpaws
Usage: python proto/ringtails/tools/derive.py [--blueprints E:\\PandabornDev\\reference\\Blueprints]
"""
import argparse
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", "mod"))
WORKER_TYPE = "PandabornRingtail"
ANIMATION_FACTOR = 1.25    # the ringtail-body lane: suits the shorter legs
LIFTING = 14               # DESIGN: Inkpaws lift 18, Ringtails 14

COATS_ADULT = ["Materials/Pandaborn/Ringtails/Adult/RingtailAdultCoat%d" % i for i in range(1, 6)]
COATS_CHILD = ["Materials/Pandaborn/Ringtails/Child/RingtailChildCoat%d" % i for i in range(1, 4)]
AVATARS = {True: ("Sprites/Pandaborn/Avatars/RingtailAdult", "Sprites/Pandaborn/Avatars/RingtailContaminatedAdult"),
           False: ("Sprites/Pandaborn/Avatars/RingtailChild", "Sprites/Pandaborn/Avatars/RingtailContaminatedChild")}

POSTS = {
    "Buildings/Pandaborn/DistrictManagement/PandabornNightBuildersPost/PandabornNightBuildersPost.Inkpaws.blueprint.json": 50,
    "Buildings/Pandaborn/DistrictManagement/PandabornNightCourierPost/PandabornNightCourierPost.Inkpaws.blueprint.json": None,
    "Buildings/Pandaborn/Food/PandabornNightForagersPost/PandabornNightForagersPost.Inkpaws.blueprint.json": None,
}
LOFT = "Buildings/Pandaborn/Housing/PandabornMoonLoft/PandabornMoonLoft.Inkpaws.blueprint.json"
OUTFITS = ("Builder", "Hauler", "Gatherer")


def load(path):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def save(rel, data):
    path = os.path.join(MOD, *rel.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print("wrote", rel)


def derive_character(bp, src, dst, template, model, adult):
    data = load(os.path.join(bp, src))
    data["TemplateSpec"]["TemplateName"] = template
    data["TemplateSpec"]["BackwardCompatibleTemplateNames"] = []
    child = data["Children"]["Model_Preserved"]
    child["TimbermeshSpec"]["Model"] = model      # the red panda body; its 0.82 size is baked in (no TransformSpec)
    child.pop("TransformSpec", None)
    walker = data["WalkerSpeedManagerSpec"]
    walker["BaseSlowedSpeed"] = walker["BaseWalkingSpeed"]   # loads never slow a Ringtail (DESIGN.md Pillar 4)
    data["MovementAnimatorSpec"]["AnimationSpeedScale"] = round(data["MovementAnimatorSpec"].get("AnimationSpeedScale", 1.0) * ANIMATION_FACTOR, 3)
    assert data["SimpleLabeledEntitySpec"]["EntityNameLocKey"] in ("Beaver.Adult.TemplateName", "Beaver.Child.TemplateName")
    if adult:
        data["WorkerSpec"]["WorkerType"] = WORKER_TYPE
        data["GoodCarrierSpec"]["BaseLiftingCapacity"] = LIFTING
    avatar, contaminated = AVATARS[adult]
    data["PandabornRingtailSpec"] = {
        "Kind": "Ringtail",
        "Textures": COATS_ADULT if adult else COATS_CHILD,
        "Avatar": avatar,
        "ContaminatedAvatar": contaminated,
        "RestStartHours": 0.0,
        "RestEndHours": 8.0,
        "RestEndsAtBell": True,
        "RestMinEndHours": 4.0,
        "RestMaxEndHours": 16.0,
        "SleepBelow": 0.55,
    }
    save(dst, data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blueprints", default=r"E:\PandabornDev\reference\Blueprints")
    bp = ap.parse_args().blueprints
    # start clean: everything under mod/ except the manifest and the hand-written loc is generated here
    for sub in ("Characters", "Buildings", "WorkerTypes", "WorkerOutfits"):
        shutil.rmtree(os.path.join(MOD, sub), ignore_errors=True)
    derive_character(bp, "Characters/Beaver/BeaverAdult.blueprint.json", "Characters/Pandaborn/RingtailAdult.Inkpaws.blueprint.json",
                     "RingtailAdult.Inkpaws", "Characters/Pandaborn/RingtailAdult.Model", True)
    derive_character(bp, "Characters/Beaver/BeaverChild.blueprint.json", "Characters/Pandaborn/RingtailChild.Inkpaws.blueprint.json",
                     "RingtailChild.Inkpaws", "Characters/Pandaborn/RingtailChild.Model", False)
    save("Characters/Pandaborn/InkpawAdult.Inkpaws.blueprint.json", {
        "TemplateSpec": {"BackwardCompatibleTemplateNames#append": ["RingtailAdult.Inkpaws"]},
        "PandabornRingtailsSpec": {
            "AdultBlueprint": "Characters/Pandaborn/RingtailAdult.Inkpaws.blueprint",
            "ChildBlueprint": "Characters/Pandaborn/RingtailChild.Inkpaws.blueprint",
            "WorkerType": WORKER_TYPE, "ArrivalAdults": 2, "ArrivalKits": 1},
        # test only: the Bell's stage-0 numbers, so the Ringtails' shift start can be checked against Bell's locked day
        # (the generated build does not carry PandabornBellSpec yet; the Bell lane owns it)
        "PandabornBellSpec": {"WorkingSpeedCurve": [{"Hours": 12, "Bonus": 0.33}, {"Hours": 16, "Bonus": 0.0}],
                              "MovementSpeedCurve": [{"Hours": 12, "Bonus": 0.33}, {"Hours": 16, "Bonus": 0.0}],
                              "SuggestionDay": 4, "SuggestionLocKey": "Pandaborn.Bell.Suggestion"}})
    save("Characters/Pandaborn/InkpawChild.Inkpaws.blueprint.json", {
        "TemplateSpec": {"BackwardCompatibleTemplateNames#append": ["RingtailChild.Inkpaws"]}})
    for path, science in POSTS.items():
        merge = {"PandabornNightPostSpec": {}}
        if science is not None:
            merge["BuildingSpec"] = {"ScienceCost": science}   # locked until the Ringtails arrive (they unlock it for free)
        save(path, merge)
    save(LOFT, {"PandabornMoonLoftSpec": {"KitsPerDay": 1}, "ProcreationHouseSpec#delete": {}})
    save("WorkerTypes/Pandaborn/WorkerType.PandabornRingtail.blueprint.json", {"WorkerTypeSpec": {
        "Id": WORKER_TYPE, "BackwardCompatibleIds": [], "IgnoresWorkingHours": True,
        "DisplayNameLocKey": "Pandaborn.Ringtails.PluralDisplayName", "WorkerOnlyTextLocKey": "Pandaborn.Ringtails.WorkerOnly"}})
    for outfit_id in OUTFITS:
        data = load(os.path.join(bp, "WorkerOutfits", "WorkerOutfit.%s.Beaver.Folktails.blueprint.json" % outfit_id))
        data["WorkerOutfitSpec"]["FactionId"] = "Inkpaws"
        data["WorkerOutfitSpec"]["WorkerType"] = WORKER_TYPE
        save("WorkerOutfits/Pandaborn/WorkerOutfit.%s.%s.Inkpaws.blueprint.json" % (outfit_id, WORKER_TYPE), data)


if __name__ == "__main__":
    main()
