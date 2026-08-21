"""_paths.py — output-path confinement, shared by every Ascend tool (stdlib only).

NOT A COMMAND. This is an importable module and it must never get a `Bash(python3 tools/_paths.py*)`
allow-list entry; the leading underscore marks it as a helper, mirroring the convention the prompts
use for non-phase files.

WHY IT EXISTS. `CLAUDE.md` and the README both tell users the agent can only write under
`workspace/**`, enforced by `Write(workspace/**)` in `.claude/settings.json`. That claim was not true
for tools. The Bash allow-list pins a tool by its *path prefix* and places no constraint on its
arguments, so an allow-listed invocation could write anywhere the process could:

    python3 tools/render_resume.py <json> --check --tex /anywhere/outside.tex   # verified, wrote

Content is escaped, so this is a clobber primitive rather than code execution. It still matters: the
agent holding that capability is the same agent that ingests attacker-influenceable job postings
(SEC-CRIT-1), and every new tool widens the surface. Confining paths in the tools is the fix that
scales, because it holds no matter how many tools get pinned later.

Usage:
    from _paths import resolve_out
    tex_path = resolve_out(a.tex, default=out_pdf.with_suffix(".tex"))
"""

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
# Where tools are allowed to write. `workspace/` is the user's own output. The repo root is allowed
# because the committed sample and CI fixtures live in-tree and the smoke suite renders them; a
# temp dir is allowed so tests and the compile path can stage files.
ALLOWED_ROOTS = [REPO / "workspace", REPO / "examples", REPO / "tests"]


class PathOutsideWorkspace(ValueError):
    """Raised when an output path would land outside every allowed root."""


def _tmp_roots():
    roots = []
    for var in ("TMPDIR", "TEMP", "TMP"):
        v = os.environ.get(var)
        if v:
            try:
                roots.append(Path(v).resolve())
            except OSError:
                pass
    roots.append(Path("/tmp").resolve())
    return roots


def is_allowed(p) -> bool:
    """True when `p` resolves inside an allowed root. Resolves first, so `..` cannot escape."""
    try:
        rp = Path(p).expanduser().resolve()
    except (OSError, RuntimeError):
        return False
    for root in ALLOWED_ROOTS + _tmp_roots():
        try:
            if rp == root or rp.is_relative_to(root):
                return True
        except (OSError, ValueError):
            continue
    return False


def resolve_out(candidate, default=None) -> Path:
    """Return a confined output path, or raise PathOutsideWorkspace.

    Resolution happens BEFORE the containment test, so `workspace/../../etc/x` is rejected rather
    than accepted on its literal prefix.
    """
    p = Path(candidate) if candidate else Path(default)
    if not is_allowed(p):
        raise PathOutsideWorkspace(
            f"refusing to write outside the workspace: {p}\n"
            f"  Allowed: {', '.join(str(r.relative_to(REPO)) + '/' for r in ALLOWED_ROOTS)} "
            f"(under {REPO}), or a temp dir.\n"
            "  This boundary is what makes CLAUDE.md's 'writes only under workspace/' claim true for "
            "tools as well as for the Write tool."
        )
    return Path(p).expanduser().resolve()


def guard(candidate, default=None) -> Path:
    """resolve_out(), but exits 2 with a clean message instead of raising. For CLI main()s."""
    try:
        return resolve_out(candidate, default)
    except PathOutsideWorkspace as e:
        print(f"render: {e}", file=sys.stderr)
        raise SystemExit(2)
