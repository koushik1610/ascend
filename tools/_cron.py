"""_cron.py: install, replace and remove one tagged crontab line, safely (stdlib only).

NOT A COMMAND. Shared by the daily brief (ui/server.py) and the Ascend 2.0 sync (tools/schedule.py).

Moved here from ui/server.py so both schedulers keep its hard-won rule (2026-08-20 council): `crontab -l`
exits non-zero both for "no crontab yet" (fine) and for a real failure such as macOS denying Full Disk
Access (not fine, and stdout is also empty). Treating the second as the first replaced a user's whole
crontab. So: read, refuse when the read genuinely failed, back up what was there, replace only our own
tagged line.

ASCEND_CRONTAB_FILE points this at a plain file instead of the crontab command. Tests use it so they
never touch the real crontab.
"""

import os
import subprocess
from pathlib import Path


def _file():
    p = os.environ.get("ASCEND_CRONTAB_FILE")
    return Path(p) if p else None


def read():
    """(ok, text, error). ok is False only when the existing crontab could not be read."""
    f = _file()
    if f:
        try:
            return True, (f.read_text(encoding="utf-8") if f.exists() else ""), ""
        except OSError as e:
            return False, "", str(e)
    cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    err = (cur.stderr or "").lower()
    if cur.returncode != 0 and not ("no crontab" in err or not err.strip()):
        return False, "", (cur.stderr or "").strip()
    return True, cur.stdout if cur.returncode == 0 else "", ""


def _write(text):
    f = _file()
    if f:
        f.write_text(text, encoding="utf-8")
    else:
        subprocess.run(["crontab", "-"], input=text, text=True, check=True)


def install(tag, line, backup_dir):
    tagged = line if line.rstrip().endswith(f"# {tag}") else f"{line} # {tag}"
    ok, text, err = read()
    if not ok:
        return {"ok": False, "manual": True, "error": err,
                "note": "Could not read your existing crontab, so nothing was changed (refusing to risk "
                        "overwriting it). Add this line via `crontab -e`:\n" + tagged}
    existing = text.splitlines()
    if existing:
        Path(backup_dir).mkdir(parents=True, exist_ok=True)
        (Path(backup_dir) / "crontab.bak").write_text(text, encoding="utf-8")
    kept = [l for l in existing if tag not in l]
    try:
        _write("\n".join(kept + [tagged]) + "\n")
    except (OSError, subprocess.CalledProcessError) as e:
        return {"ok": False, "manual": True, "error": str(e),
                "note": f"Could not set cron automatically. Add this line via `crontab -e`:\n{tagged}"}
    return {"ok": True, "preserved": len(kept), "line": tagged}


def remove(tag):
    ok, text, err = read()
    if not ok:
        return {"ok": False, "error": err}
    kept = [l for l in text.splitlines() if tag not in l]
    _write("\n".join(kept) + ("\n" if kept else ""))
    return {"ok": True, "removed": len(text.splitlines()) - len(kept)}
