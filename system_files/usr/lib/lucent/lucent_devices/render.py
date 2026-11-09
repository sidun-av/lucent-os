"""Plain-text report for people (and for pasting into a help request)."""
from __future__ import annotations

from .inventory import GROUPS
from .strings import t


def summary_line(report, lang) -> str:
    s = report["summary"]
    n, k = s["total"], s["needs_driver"] + s["problem"]
    if k == 0:
        return t(lang, "summary_ok_1") if n == 1 else t(lang, "summary_ok", n=n)
    return t(lang, "summary_attention_1", n=n) if k == 1 else t(lang, "summary_attention", k=k, n=n)


def explain(dev, lang) -> list[tuple[str, str]]:
    """(what is wrong, what to do) pairs for one device."""
    out = []
    for p in dev["problems"]:
        code = p["code"]
        if code == "no_driver" and dev.get("hint"):
            code = dev["hint"]
        fields = {k: ("?" if v is None else v) for k, v in p.items() if k != "code"}
        out.append((t(lang, f"problem.{code}", **fields), t(lang, f"do.{code}")))
    return out


def _line(dev, lang) -> str:
    who = dev["name"] + (f" ({dev['vendor']})" if dev["vendor"] else "")
    drv = t(lang, "driver", driver=dev["driver"]) if dev["driver"] else t(lang, "no_driver_bound")
    notes = "".join(f" · {t(lang, 'note.' + n)}" for n in dev["notes"])
    return f"  {who}\n    {t(lang, 'status.' + dev['status'])} · {drv}{notes}"


def text(report, lang="en", show_all=False) -> str:
    lines = [summary_line(report, lang)]
    if not report["kernel_log"]["readable"]:
        lines.append(t(lang, "no_log"))
    devs = report["devices"]
    attention = [d for d in devs if d["status"] in ("problem", "needs_driver")]
    for d in attention:
        lines += ["", f"{t(lang, 'group.' + d['group'])}", _line(d, lang)]
        for what, todo in explain(d, lang):
            lines += [f"    {what}", f"    {todo}"]
    rest = [d for d in devs if d not in attention and (show_all or not d["system"])]
    for g in GROUPS:
        members = [d for d in rest if d["group"] == g]
        if not members:
            continue
        lines += ["", t(lang, "group." + g)]
        for d in members:
            lines.append(_line(d, lang))
            if d["status"] == "unused" and not d["system"]:
                lines.append(f"    {t(lang, 'unused.hint')}")
    hidden = sum(1 for d in devs if d["system"] and d not in attention)
    if hidden and not show_all:
        lines += ["", t(lang, "hidden", n=hidden)]
    return "\n".join(lines) + "\n"
