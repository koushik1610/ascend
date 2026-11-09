"""_cli.py: the one argv helper the tools share (stdlib only).

NOT A COMMAND. Importable helper; it must never get a `Bash(python3 tools/_cli.py*)` allow-list entry.
"""


def opt(args, name, default=None):
    """The value after `--name` in args, or default when the flag or its value is missing."""
    if name in args:
        i = args.index(name)
        if i + 1 < len(args):
            return args[i + 1]
    return default
