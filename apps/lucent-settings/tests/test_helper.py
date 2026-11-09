"""data/settings-helper (run by pkexec) edits rpm-ostreed.conf and the timer."""

import os
import subprocess
import sys
from pathlib import Path

HELPER = Path(__file__).parents[1] / "data" / "settings-helper"


def run(tmp_path, *args, conf_text=None):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    log = tmp_path / "calls"
    for tool in ("rpm-ostree", "systemctl"):
        stub = bin_dir / tool
        stub.write_text(f'#!/bin/sh\necho "{tool} $*" >> "{log}"\n')
        stub.chmod(0o755)
    conf = tmp_path / "rpm-ostreed.conf"
    if conf_text is not None:
        conf.write_text(conf_text)
    env = dict(os.environ, PATH=f"{bin_dir}:{os.environ['PATH']}", LUCENT_RPM_OSTREED_CONF=str(conf))
    p = subprocess.run([sys.executable, str(HELPER), *args], env=env, capture_output=True, text=True)
    calls = log.read_text().splitlines() if log.exists() else []
    return p, conf, calls


def test_turn_on_with_fedora_default_file(tmp_path):
    p, conf, calls = run(tmp_path, "auto-updates", "on",
                         conf_text="[Daemon]\n#AutomaticUpdatePolicy=none\n#IdleExitTimeout=60\n")
    assert p.returncode == 0, p.stderr
    assert "AutomaticUpdatePolicy=stage" in conf.read_text().splitlines()
    assert calls == ["rpm-ostree reload", "systemctl enable --now rpm-ostreed-automatic.timer"]


def test_turn_off_replaces_the_setting(tmp_path):
    p, conf, calls = run(tmp_path, "auto-updates", "off", conf_text="[Daemon]\nAutomaticUpdatePolicy=stage\n")
    assert p.returncode == 0
    assert conf.read_text().count("AutomaticUpdatePolicy") == 1
    assert "AutomaticUpdatePolicy=none" in conf.read_text()
    assert calls[-1] == "systemctl disable --now rpm-ostreed-automatic.timer"


def test_refuses_anything_else(tmp_path):
    for args in ([], ["auto-updates"], ["auto-updates", "maybe"], ["rm", "-rf"]):
        p, _conf, calls = run(tmp_path, *args, conf_text="[Daemon]\n")
        assert p.returncode == 2 and calls == []
