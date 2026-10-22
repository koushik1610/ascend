#!/usr/bin/env python3
"""autoapply.py: automatic apply for Greenhouse, Ashby and Lever jobs (Ascend 2.0).

  python3 tools/autoapply.py run    WS [--dry-run] [--limit N] [--posting ID]
  python3 tools/autoapply.py status WS
  python3 tools/autoapply.py pause  WS [--reason TEXT]

Turning automatic apply on, resuming it and changing its limits happen only in the hub, where the user
types "apply for me". There is no command for them. The hub's server signs data/auto.json with a key kept
outside the workspace (~/.config/ascend/auto.key), so a file changed any other way reads as off.

A run takes the queue's best-fit jobs that pass every gate (apply.ready, then apply.pack), opens each
job's application page rebuilt from its board, fills it from the user's own answers with
autoapply_forms.py (Playwright), and submits. A job is applied only when the ATS's confirmation page was
seen. Anything else goes to Needs you with the reason: a CAPTCHA, a login, a question the user's answers
do not cover, an upload that failed, no confirmation. --dry-run fills and screenshots without submitting,
works while automatic apply is off, and changes no state.

Limits: the day's cap (5 a day for the first 7 days, then the user's setting, default 25), 2 applications
per company per 30 days, a pause after 3 unclear results in a day, and a pause once 50 applications are
sent if fewer than 5% of the last 50 drew any reply.
"""

import hashlib
import hmac
import json
import os
import secrets
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import _v2data as d  # noqa: E402
import apply  # noqa: E402
import jobqueue  # noqa: E402

PHRASE = "apply for me"
DEFAULTS = {"enabled": False, "enabled_at": None, "daily_cap": 25, "fit_threshold": 75, "company_cap": 2,
            "paused": False, "paused_reason": None}
FIRST_WEEK_CAP, FIRST_WEEK_DAYS = 5, 7
CAP_RANGE, FIT_RANGE = (1, 50), (50, 100)
STALE_ATTEMPT = timedelta(hours=1)
PAUSE_AFTER, MIN_REPLY, MAX_UNCLEAR = 50, 0.05, 3
REPLY_CATEGORIES = {"info-request", "assessment", "interview-invite", "rejection"}
INSTALL = "auto-apply needs Playwright: pip install playwright && playwright install chromium"
UNCLEAR_NOTE = "It may have been sent: check your email and the company's site before applying again."


# --- auto.json: written only through the hub's server --------------------------------------------------

def _key_path():
    return Path(os.environ.get("ASCEND_AUTO_KEY") or Path.home() / ".config" / "ascend" / "auto.key")


def _key(create=False):
    p = _key_path()
    if not p.is_file():
        if not create:
            return None
        p.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            os.write(fd, secrets.token_bytes(32))
            os.close(fd)
        except FileExistsError:
            pass
    return p.read_bytes()


def _sig(key, ws, cfg):
    msg = str(Path(ws).resolve()) + "\n" + json.dumps(cfg, sort_keys=True)
    return hmac.new(key, msg.encode(), hashlib.sha256).hexdigest()


def _path(ws):
    return Path(ws) / "data" / "auto.json"


def load_config(ws):
    """The settings, or the defaults (off) when the file is missing or was not written by the hub's server."""
    raw = d.read_json(_path(ws), None)
    if raw is None:
        return dict(DEFAULTS, tampered=False)
    key = _key()
    cfg = raw.get("config") if isinstance(raw, dict) else None
    if not (key and isinstance(cfg, dict) and isinstance(raw.get("sig"), str)
            and hmac.compare_digest(raw["sig"], _sig(key, ws, cfg))):
        return dict(DEFAULTS, tampered=True)
    return dict(DEFAULTS, **{k: v for k, v in cfg.items() if k in DEFAULTS}, tampered=False)


def _change(ws, fn):
    with d.locked(_path(ws)):
        cfg = load_config(ws)
        cfg.pop("tampered", None)
        fn(cfg)
        clean = {k: cfg[k] for k in DEFAULTS}
        d.write_json_atomic(_path(ws), {"config": clean, "sig": _sig(_key(create=True), ws, clean)})
    return load_config(ws)


def enable(ws, phrase):
    if not isinstance(phrase, str) or " ".join(phrase.lower().split()) != PHRASE:
        raise ValueError(f'type "{PHRASE}" to turn on automatic apply')

    def on(cfg):
        if not cfg["enabled"]:
            cfg["enabled_at"] = date.today().isoformat()
        cfg.update(enabled=True, paused=False, paused_reason=None)
    return _change(ws, on)


def disable(ws):
    return _change(ws, lambda cfg: cfg.update(enabled=False))


def pause(ws, reason=None):
    return _change(ws, lambda cfg: cfg.update(paused=True, paused_reason=str(reason or "paused by you")[:300]))


def resume(ws):
    return _change(ws, lambda cfg: cfg.update(paused=False, paused_reason=None))


def settings(ws, daily_cap=None, fit_threshold=None):
    def bounded(v, lo_hi, what):
        if isinstance(v, bool) or not isinstance(v, int) or not lo_hi[0] <= v <= lo_hi[1]:
            raise ValueError(f"{what} must be a whole number from {lo_hi[0]} to {lo_hi[1]}")
        return v
    upd = {}
    if daily_cap is not None:
        upd["daily_cap"] = bounded(daily_cap, CAP_RANGE, "the daily cap")
    if fit_threshold is not None:
        upd["fit_threshold"] = bounded(fit_threshold, FIT_RANGE, "the fit threshold")
    return _change(ws, lambda cfg: cfg.update(upd))


def cap_today(cfg, today=None):
    today = today or date.today()
    try:
        since = date.fromisoformat(cfg.get("enabled_at") or "")
    except ValueError:
        since = None
    first_week = since is not None and (today - since).days < FIRST_WEEK_DAYS
    return min(FIRST_WEEK_CAP, cfg["daily_cap"]) if first_week else cfg["daily_cap"]


# --- the run --------------------------------------------------------------------------------------------

def _log(ws):
    return d.read_jsonl(Path(ws) / "data" / "apply-log.jsonl")


def _attempts_today(ws, today):
    return sum(1 for r in _log(ws) if r.get("mode") == "auto" and not r.get("dry_run")
               and r.get("result") in ("submitted", "unclear") and str(r.get("at", "")).startswith(today.isoformat()))


def pause_reason(ws, today=None):
    """Why automatic apply should stop now, or None."""
    today = today or date.today()
    log = _log(ws)
    unclear = sum(1 for r in log if r.get("mode") == "auto" and r.get("result") == "unclear" and not r.get("dry_run")
                  and str(r.get("at", "")).startswith(today.isoformat()))
    if unclear >= MAX_UNCLEAR:
        return f"{unclear} unclear results today: check them in Needs you, then resume in the hub"
    sent = []
    for r in sorted(log, key=lambda r: r.get("at") or ""):
        if r.get("result") == "submitted" and not r.get("dry_run") and r.get("posting_id") not in sent:
            sent.append(r.get("posting_id"))
    if len(sent) < PAUSE_AFTER:
        return None
    last = sent[-PAUSE_AFTER:]
    nn = {j.get("posting_id"): j.get("nn") for j in jobqueue._queue(ws).get("jobs", []) if j.get("nn")}
    from classify import latest_events
    matched = {e.get("match") for e in latest_events(d.read_jsonl(Path(ws) / "data" / "events.jsonl"))
               if e.get("category") in REPLY_CATEGORIES}
    replied = sum(1 for p in last if p in matched or (nn.get(p) and nn[p] in matched))
    if replied / PAUSE_AFTER < MIN_REPLY:
        return (f"{replied} of the last {PAUSE_AFTER} applications got any reply ({replied * 100 // PAUSE_AFTER}%), "
                f"below {int(MIN_REPLY * 100)}%. Look at fit and the résumés before resuming")
    return None


def _recover(ws, now):
    """An attempt that never finished (the Mac slept, the run was killed) goes to the user, never retried:
    it may have been sent."""
    for j in jobqueue._queue(ws).get("jobs", []):
        if j.get("state") != "applying":
            continue
        try:
            started = datetime.fromisoformat(j.get("attempt_at") or "")
        except ValueError:
            started = None
        if started is None or now - started > STALE_ATTEMPT:
            jobqueue.set_state(ws, j["posting_id"], "needs-you", via_runner=True,
                               stop_reason=f"the last attempt was interrupted. {UNCLEAR_NOTE}")


def _record(ws, entry, result, reason, res, dry_run):
    d.append_jsonl(Path(ws) / "data" / "apply-log.jsonl", {
        "posting_id": entry["posting_id"], "company": entry.get("company"), "title": entry.get("title"),
        "mode": "auto", "result": result, "reason": reason, "dry_run": dry_run,
        "unfilled": list(res.get("unfilled") or [])[:30], "screenshots": list(res.get("shots") or [])[:5],
        "at": datetime.now().isoformat(timespec="seconds")})


def _filler():
    try:
        from autoapply_forms import fill
    except ImportError:
        return None
    return fill


def run(ws, dry_run=False, limit=None, filler=None, posting=None, today=None):
    ws, today, now = Path(ws), today or date.today(), datetime.now()
    out = {"submitted": 0, "unclear": 0, "stopped": 0, "filled": 0, "waiting": [], "skipped": None, "error": None}
    with d.locked(ws / "data" / "autoapply.run"):          # one runner at a time
        _recover(ws, now)
        cfg = load_config(ws)
        if dry_run:
            room = limit or 3
        else:
            if not cfg["enabled"]:
                out["skipped"] = "auto-apply is off" + (" (auto.json was changed outside the hub)" if cfg["tampered"] else "")
                return out
            if cfg["paused"]:
                out["skipped"] = f"paused: {cfg['paused_reason']}"
                return out
            why = pause_reason(ws, today)
            if why:
                pause(ws, why)
                out["skipped"] = f"paused: {why}"
                return out
            room = cap_today(cfg, today) - _attempts_today(ws, today)
            if limit is not None:
                room = min(room, limit)
            if room <= 0:
                out["skipped"] = "today's cap is reached"
                return out
        fill = filler or _filler()
        if fill is None:
            out["error"] = INSTALL
            return out
        jobs = sorted(jobqueue._queue(ws).get("jobs", []), key=lambda j: -(j.get("fit") or 0))
        for entry in jobs:
            if room <= 0:
                break
            pid = entry.get("posting_id")
            if posting and pid != posting:
                continue
            if apply.ready(ws, entry, cfg, today):
                continue
            try:
                job, pdf = apply.pack(ws, entry)
            except apply.NotYet as e:
                out["waiting"].append(f"{entry.get('company')}: waiting for a tailored résumé ({e})")
                continue
            except apply.Refused as e:
                out["stopped"] += 1
                _record(ws, entry, "stopped", str(e), {}, dry_run)
                if not dry_run:
                    jobqueue.set_state(ws, pid, "needs-you", via_runner=True, stop_reason=str(e))
                continue
            url = apply.apply_url_for(ws, pid)
            if not apply.allowed(url):          # ready() checked this; a second look costs nothing
                continue
            room -= 1
            if not dry_run:
                jobqueue.set_state(ws, pid, "applying", via_runner=True, approved_by="auto",
                                   attempt_at=now.isoformat(timespec="seconds"))
            shots = job / "apply"
            shots.mkdir(exist_ok=True)
            try:
                res = fill(url, apply.answers(ws), str(pdf), not dry_run, str(shots)) or {}
            except Exception as e:      # after a click on submit nothing is certain
                res = {"result": "stopped" if dry_run else "unclear", "reason": f"the runner failed ({type(e).__name__}: {e})"}
            result = res.get("result")
            if dry_run:
                result = "filled" if result in ("filled", "submitted") else "stopped"
            elif result not in ("submitted", "unclear", "stopped"):
                result = "unclear"
            reason = res.get("reason") or ("" if result in ("submitted", "filled") else "no reason given")
            _record(ws, entry, result, reason, res, dry_run)
            out[result] += 1
            if dry_run:
                continue
            if result == "submitted":
                jobqueue.set_state(ws, pid, "applied", via_runner=True)
            else:
                jobqueue.set_state(ws, pid, "needs-you", via_runner=True,
                                   stop_reason=f"{reason}. {UNCLEAR_NOTE}" if result == "unclear" else reason)
    return out


def status(ws, today=None):
    today = today or date.today()
    cfg = load_config(ws)
    return {"enabled": cfg["enabled"], "paused": cfg["paused"], "paused_reason": cfg["paused_reason"],
            "tampered": cfg["tampered"], "cap_today": cap_today(cfg, today), "sent_today": _attempts_today(ws, today),
            "fit_threshold": cfg["fit_threshold"], "daily_cap": cfg["daily_cap"], "enabled_at": cfg["enabled_at"],
            "playwright": _filler() is not None}


def _opt(args, name, default=None):
    return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else default


def main(argv):
    if len(argv) >= 2 and argv[1] in ("enable", "resume", "settings", "disable"):
        print(f"autoapply: {argv[1]} happens in the hub, where you type \"{PHRASE}\"; there is no command for it",
              file=sys.stderr)
        return 2
    if len(argv) < 3 or argv[1] not in ("run", "status", "pause"):
        print(__doc__, file=sys.stderr)
        return 2
    cmd, ws, args = argv[1], argv[2], argv[3:]
    if cmd == "pause":
        print(json.dumps(pause(ws, _opt(args, "--reason"))))
        return 0
    if cmd == "status":
        print(json.dumps(status(ws), indent=2))
        return 0
    lim = _opt(args, "--limit")
    out = run(ws, dry_run="--dry-run" in args, limit=int(lim) if lim else None, posting=_opt(args, "--posting"))
    print(json.dumps(out, indent=2))
    return 1 if out["error"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
