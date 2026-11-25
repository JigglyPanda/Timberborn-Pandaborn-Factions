"""Run the balance questions: `python -I tools/balance/run.py all` or `... q2 q4`. Output: tools/balance/out/*.md."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from balance import questions  # noqa: E402


def main(argv):
    names = list(questions.ALL) if not argv or argv == ["all"] else argv
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    for name in names:
        text = "\n".join(questions.ALL[name]())
        with open(os.path.join(HERE, "out", name + ".md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(text + "\n")
        sys.stdout.buffer.write((text + "\n").encode("utf-8"))


if __name__ == "__main__":
    main(sys.argv[1:])
