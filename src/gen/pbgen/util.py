"""Shared helpers: JSON in and out (deterministic), hashing, asset keys. Standard library only."""
import hashlib
import json
import os

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DEFAULT_BLUEPRINTS = r"E:\PandabornDev\reference\Blueprints"
DEFAULT_LOCALIZATIONS = r"E:\PandabornDev\reference\Localizations"
DEFAULT_GAME = r"C:\Program Files (x86)\Steam\steamapps\common\Timberborn"
DEFAULT_BUILD = r"E:\PandabornDev\build"


class GenError(Exception):
    """A catalogue problem the generator refuses to guess about. The message says what to change."""


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def load_json(path):
    raw = read_bytes(path)
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    return json.loads(raw.decode("utf-8"))


def dumps(obj):
    """The one output format: 2-space indent, UTF-8, LF, trailing newline. Key order is the insertion order, which the
    generator keeps deterministic (vanilla order for copied specs, a fixed order for built ones). Floats use Python's
    shortest round-trip repr, so a value read from a vanilla file is written back with the same digits."""
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    return sha256_bytes(read_bytes(path))


def asset_key(rel_path):
    """The game's AssetPathHelper: forward slashes, lowercase, last extension stripped."""
    p = rel_path.replace("\\", "/").lstrip("/")
    root, ext = os.path.splitext(p)
    return (root if ext else p).lower()


def ref_key(value):
    return value.replace("\\", "/").lstrip("/").lower()


def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
