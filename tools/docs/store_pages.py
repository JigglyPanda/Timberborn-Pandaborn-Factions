#!/usr/bin/env python3
"""Makes the mod.io description (Markdown and HTML) from the Steam Workshop text, so the three never drift.

    python -I tools/docs/store_pages.py            # rewrite catalogue/text/store/modio.md and modio.html
    python -I tools/docs/store_pages.py --check    # exit 1 if either is out of date (writes nothing)

The source is catalogue/text/store/steam_workshop.bbcode.txt, below its line of dashes. Only the BBCode this
project uses is understood: [h1] [h2] [b] [url=] [list] [*]. Output is deterministic.
"""
import io
import os
import re
import sys

STORE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "catalogue", "text", "store"))
RULE = "-" * 70 + "\n"

MD_NOTES = """DRAFT NOTES (delete everything down to the line of dashes before publishing)
- Written by an AI (Claude). Not published anywhere.
- Made from steam_workshop.bbcode.txt by tools/docs/store_pages.py. Do not edit by hand: change the Steam text
  and run the script. modio.html is the same text as HTML, for mod.io's description field.
- The same rules apply as for the Steam text: publish only after docs/RELEASE.md is green; delete the line of any
  feature that did not ship.
- mod.io's summary field (at most 250 characters) is in summary.txt.
""" + RULE

HTML_NOTES = """<!-- DRAFT. Written by an AI (Claude). Not published. The mod.io description as HTML, made from
     steam_workshop.bbcode.txt by tools/docs/store_pages.py: do not edit by hand. Same rules as the Steam text:
     publish only after docs/RELEASE.md is green, delete the line of any feature that did not ship. Delete this
     comment before pasting. -->
"""


def to_markdown(bb):
    md = re.sub(r"\[h1\](.*?)\[/h1\]", r"# \1", bb)
    md = re.sub(r"\[h2\](.*?)\[/h2\]", r"## \1", md)
    md = re.sub(r"\[b\](.*?)\[/b\]", r"**\1**", md)
    md = re.sub(r"\[url=(.*?)\](.*?)\[/url\]", r"[\2](\1)", md)
    md = md.replace("[list]\n", "").replace("[/list]\n", "").replace("[*]", "* ")
    md = md.replace("A Workshop copy plus a manual copy", "Two copies (mod.io, Workshop or manual)")
    md = re.sub(r"(?<![(\[])(https://github\.com/\S+)", r"[\1](\1)", md)
    return md


def inline(t):
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", t)
    return re.sub(r"\[(.*?)\]\((.*?)\)", r'<a href="\2">\1</a>', t)


def to_html(md):
    out, in_list = [], False
    for line in md.split("\n"):
        if line.startswith("* "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append("<li>" + inline(line[2:]) + "</li>")
            continue
        if in_list:
            out.append("</ul>")
            in_list = False
        if line.startswith("# "):
            out.append("<h2>" + inline(line[2:]) + "</h2>")
        elif line.startswith("## "):
            out.append("<h3>" + inline(line[3:]) + "</h3>")
        elif line.strip():
            out.append("<p>" + inline(line) + "</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out) + "\n"


def main():
    check = "--check" in sys.argv[1:]
    with io.open(os.path.join(STORE, "steam_workshop.bbcode.txt"), encoding="utf-8", newline="") as f:
        bb = f.read().replace("\r\n", "\n").split(RULE, 1)[1]
    md = to_markdown(bb)
    stale = False
    for name, text in (("modio.md", MD_NOTES + md), ("modio.html", HTML_NOTES + to_html(md))):
        path = os.path.join(STORE, name)
        old = ""
        if os.path.isfile(path):
            with io.open(path, encoding="utf-8", newline="") as f:
                old = f.read().replace("\r\n", "\n")
        if old != text:
            stale = True
            if not check:
                with io.open(path, "w", encoding="utf-8", newline="\n") as f:
                    f.write(text)
    sys.stderr.write("steam text: %d characters (limit 8,000)\n" % len(bb))
    if check and stale:
        sys.stderr.write("modio.md / modio.html are out of date: run tools/docs/store_pages.py\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
