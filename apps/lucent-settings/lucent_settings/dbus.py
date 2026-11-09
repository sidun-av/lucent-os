"""D-Bus calls through `busctl` (systemd), with JSON output.

busctl takes the signature and arguments on the command line and prints
typed JSON, so a call is a plain argv that tests can assert on, and the
answer parses without a binding library. Only non-secret arguments go
through here: argv is visible to other local processes.
"""

from __future__ import annotations

import json
from typing import Any

SYSTEM = "system"
SESSION = "user"


def _arg(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def call(bus: str, service: str, path: str, iface: str, method: str,
         signature: str = "", *args: Any, timeout: int | None = None) -> list[str]:
    argv = ["busctl", f"--{bus}", "--json=short"]
    if timeout is not None:
        argv.append(f"--timeout={timeout}")
    argv += ["call", service, path, iface, method]
    if signature:
        argv += [signature, *map(_arg, args)]
    return argv


def get_property(bus: str, service: str, path: str, iface: str, *props: str) -> list[str]:
    return ["busctl", f"--{bus}", "--json=short", "get-property", service, path, iface, *props]


def set_property(bus: str, service: str, path: str, iface: str, prop: str,
                 signature: str, value: Any) -> list[str]:
    return ["busctl", f"--{bus}", "set-property", service, path, iface, prop, signature, _arg(value)]


def emit(bus: str, path: str, iface: str, signal: str, signature: str = "", *args: Any) -> list[str]:
    argv = ["busctl", f"--{bus}", "emit", path, iface, signal]
    if signature:
        argv += [signature, *map(_arg, args)]
    return argv


def values(out: str) -> list[Any]:
    """busctl --json=short prints one {"type", "data"} object per line:
    for `call` data is the list of return values, for `get-property` one
    line per property. Returns the plain values, in order."""
    found: list[Any] = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        found.append(json.loads(line)["data"])
    return found


def plain(variant: Any) -> Any:
    """Unwrap busctl's {"type": ..., "data": ...} variants, recursively."""
    if isinstance(variant, dict):
        if set(variant) == {"type", "data"}:
            return plain(variant["data"])
        return {k: plain(v) for k, v in variant.items()}
    if isinstance(variant, list):
        return [plain(v) for v in variant]
    return variant
