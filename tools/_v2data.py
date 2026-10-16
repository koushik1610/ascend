"""_v2data.py: the Ascend 2.0 data contract's file I/O (stdlib only).

NOT A COMMAND. Importable helper; it must never get a `Bash(python3 tools/_v2data.py*)` allow-list
entry (the leading underscore marks it, as with `_paths.py`).

Every v2 stage reads and writes files under workspace/<name>/data/ (spec §5). JSON Lines files are
append-only, so a crashed run can only leave a partial last line, which readers skip. JSON files are
written through a temp file and os.replace, so a reader never sees half a file. Every write goes
through `_paths.resolve_out`, so these helpers inherit the same output confinement as every tool.
"""

import json
import os
from pathlib import Path

from _paths import resolve_out


def data_dir(ws):
    """workspace/<name>/data, created if missing."""
    p = resolve_out(str(Path(ws) / "data"))
    p.mkdir(parents=True, exist_ok=True)
    return p


def append_jsonl(path, rec):
    p = resolve_out(str(path))
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")


def read_jsonl(path):
    """Every well-formed object in the file. Missing file → []. Blank and corrupt lines are skipped."""
    p = Path(path)
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(rec, dict):
            out.append(rec)
    return out


def write_json_atomic(path, obj):
    p = resolve_out(str(path))
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, p)


def read_json(path, default):
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default
