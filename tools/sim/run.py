"""Colony model for the Inkpaws faction. Usage:

    python tools/sim/run.py all            # every scenario, written to tools/sim/out/
    python tools/sim/run.py calibrate      # or: q1 q1drought q2 q3 q4 q5 q6 q7 q8 sheet

Standard library and numpy only; no game needed.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from pandasim import scenarios as SC  # noqa: E402
from pandasim import sheet  # noqa: E402

COMMANDS = {
    "calibrate": SC.calibrate, "q1": SC.q1_opening, "q1drought": SC.q1_drought, "q2": SC.q2_bell,
    "q3": SC.q3_food, "q4": SC.q4_water, "q5": SC.q5_ringtails, "q6": SC.q6_population, "q7": SC.q7_flowering,
    "q8": SC.q8_late, "sheet": sheet.markdown,
}


def main(argv):
    names = argv[1:] or ["all"]
    if names == ["all"]:
        names = list(COMMANDS)
    out_dir = os.path.join(HERE, "out")
    os.makedirs(out_dir, exist_ok=True)
    for n in names:
        text = COMMANDS[n]()
        print(text, "\n")
        with open(os.path.join(out_dir, f"{n}.md"), "w", encoding="utf-8") as f:
            f.write(text + "\n")
    if "sheet" in names:
        with open(os.path.join(out_dir, "statsheet.json"), "w", encoding="utf-8") as f:
            json.dump(sheet.as_json(), f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main(sys.argv)
