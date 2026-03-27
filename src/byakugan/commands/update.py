"""byakugan update — refresh templates from master, preserve project context."""
from __future__ import annotations

from byakugan.commands.init import run as init_run


def run() -> None:
    init_run(update=True)
