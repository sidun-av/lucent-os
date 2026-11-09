"""iso/make-config.py: the bootc-image-builder config with Lucent's kickstart."""
from __future__ import annotations

import os
import subprocess
import sys
import tomllib
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "iso" / "make-config.py"


def make(tmp_path: Path, ref: str | None, *extra: str) -> str:
    env = {k: v for k, v in os.environ.items() if k != "LUCENT_IMAGE_REF"}
    if ref is not None:
        env["LUCENT_IMAGE_REF"] = ref
    out = tmp_path / "config.toml"
    subprocess.run([sys.executable, str(SCRIPT), str(out), *extra], check=True, env=env)
    return tomllib.loads(out.read_text())["customizations"]["installer"]["kickstart"]["contents"]


def test_apps_and_signed_updates_sections_with_the_image_reference(tmp_path):
    ks = make(tmp_path, "ghcr.io/sidun-av/lucent-os:stable")
    assert "lucent-apps: start" in ks
    assert "ref='ghcr.io/sidun-av/lucent-os:stable'" in ks
    assert "--enforce-container-sigpolicy" in ks
    assert "@IMAGE_REF@" not in ks
    # Ours run after bootc-image-builder's %post (which %includes come first).
    assert ks.index("lucent-apps: start") < ks.index("lucent-updates")


def test_without_a_reference_the_updates_section_does_nothing(tmp_path):
    ks = make(tmp_path, None)
    assert "ref=''" in ks
    assert "no image reference given" in ks


def test_extra_kickstart_comes_first(tmp_path):
    extra = tmp_path / "extra.ks"
    extra.write_text("text --non-interactive\n")
    ks = make(tmp_path, "x", str(extra))
    assert ks.startswith("text --non-interactive")


def test_a_reference_with_quotes_is_refused(tmp_path):
    env = dict(os.environ, LUCENT_IMAGE_REF="x'; rm -rf /; '")
    p = subprocess.run([sys.executable, str(SCRIPT), str(tmp_path / "c.toml")], env=env,
                       capture_output=True, text=True)
    assert p.returncode != 0
