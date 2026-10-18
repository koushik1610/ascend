"""_v2data.py: the Ascend 2.0 data contract's file I/O (stdlib only).

NOT A COMMAND. Importable helper; it must never get a `Bash(python3 tools/_v2data.py*)` allow-list
entry (the leading underscore marks it, as with `_paths.py`).

Every v2 stage reads and writes files under workspace/<name>/data/ (spec §5). JSON Lines files are
append-only, so a crashed run can only leave a partial last line, which readers skip. JSON files are
written through a temp file and os.replace, so a reader never sees half a file. Every write goes
through `_paths.resolve_out`, so these helpers inherit the same output confinement as every tool.
"""

import fcntl
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

from _paths import resolve_out


def data_dir(ws):
    """workspace/<name>/data, created if missing."""
    p = resolve_out(str(Path(ws) / "data"))
    p.mkdir(parents=True, exist_ok=True)
    return p


def append_jsonl(path, rec):
    with locked(path) as p:                 # so a retention rewrite never drops a concurrent append
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")


def rewrite_jsonl(path, fn):
    """Replace a JSON Lines file with fn(rows), under its lock. The only sanctioned non-append write."""
    with locked(path) as p:
        rows = fn(read_jsonl(p))
        fd, tmp = tempfile.mkstemp(dir=p.parent, prefix=p.name + ".", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.writelines(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, p)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise


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
    fd, tmp = tempfile.mkstemp(dir=p.parent, prefix=p.name + ".", suffix=".tmp")   # one temp file per writer
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, p)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


@contextmanager
def locked(path):
    """An exclusive lock on <path>.lock for one read-modify-write. Not re-entrant: never take the same file's
    lock twice. The one nesting allowed is apply-log.jsonl, then queue.json (apply.record); never take them
    in the other order."""
    p = resolve_out(str(path))
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p.with_name(p.name + ".lock"), "a") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        try:
            yield p
        finally:
            fcntl.flock(lk, fcntl.LOCK_UN)


def update_json(path, default, fn):
    """Read, change and write a JSON file under its lock, so concurrent writers (the cron sync, the hub
    server, a Claude session) never lose each other's update. fn changes the object in place; its return
    value is returned."""
    with locked(path) as p:
        obj = read_json(p, default)
        out = fn(obj)
        write_json_atomic(p, obj)
        return out


def read_json(path, default):
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default
