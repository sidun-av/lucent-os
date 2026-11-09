"""Running system tools.

Every backend talks to the system through a `Runner`, so tests can swap in
a fake that records the exact argv and replays output captured on a real
Lucent OS machine (tests/fixtures/). Nothing here ever runs a shell.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class Result:
    code: int
    out: str = ""
    err: str = ""

    @property
    def ok(self) -> bool:
        return self.code == 0

    @property
    def message(self) -> str:
        """The tool's own explanation, for an error line in the UI: its first
        line (later ones tend to be summaries like "not all devices ...")."""
        text = (self.err or self.out).strip()
        return text.splitlines()[0].strip() if text else ""


class Runner:
    def run(self, argv: list[str], *, timeout: float = 30, stdin: str | None = None) -> Result:
        try:
            p = subprocess.run(argv, input=stdin, capture_output=True, text=True, timeout=timeout,
                               env=_env())
        except FileNotFoundError:
            return Result(127, "", f"{argv[0]}: not installed")
        except subprocess.TimeoutExpired:
            return Result(124, "", f"{argv[0]}: timed out")
        return Result(p.returncode, p.stdout, p.stderr)

    def spawn(self, argv: list[str]) -> bool:
        """Start a program and don't wait for it (file manager, System Settings)."""
        try:
            subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, start_new_session=True, env=_env())
        except OSError:
            return False
        return True


def _env() -> dict[str, str]:
    # Tools answer in the C locale so their output parses the same everywhere;
    # what the user reads comes from our own catalog.
    env = dict(os.environ)
    env["LC_ALL"] = "C.UTF-8"
    env.pop("LANGUAGE", None)
    return env
