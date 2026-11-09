"""build_files/container-policy.py: the containers-policy.json that makes an
installed Lucent OS refuse an update that isn't signed with Lucent's key,
while every other image (toolbox, podman pulls) behaves as before."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / "container-policy.py"
SCOPE = "ghcr.io/sidun-av/lucent-os"
KEY = "/etc/pki/containers/lucent-os.pub"

# Fedora's containers-common policy.json, as in the base image.
FEDORA = {
    "default": [{"type": "insecureAcceptAnything"}],
    "transports": {
        "docker": {
            "registry.access.redhat.com": [{"type": "signedBy", "keyType": "GPGKeys",
                                            "keyPaths": ["/etc/pki/rpm-gpg/RPM-GPG-KEY-redhat-release"]}],
            "registry.redhat.io": [{"type": "signedBy", "keyType": "GPGKeys",
                                    "keyPaths": ["/etc/pki/rpm-gpg/RPM-GPG-KEY-redhat-release"]}],
        },
        "docker-daemon": {"": [{"type": "insecureAcceptAnything"}]},
    },
}


def load():
    import importlib.util
    spec = importlib.util.spec_from_file_location("container_policy", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def effective(policy: dict, transport: str, scope: str):
    """What containers/image applies: the most specific scope, else the transport's "", else default."""
    scopes = policy.get("transports", {}).get(transport, {})
    parts = scope.split("/")
    for n in range(len(parts), 0, -1):
        if "/".join(parts[:n]) in scopes:
            return scopes["/".join(parts[:n])]
    return scopes.get("", policy["default"])


def test_default_rejects_so_bootc_accepts_the_policy_for_signed_updates():
    # ostree-ext refuses ostree-image-signed: with a default of insecureAcceptAnything.
    p = load().lucent_policy(FEDORA, SCOPE, KEY)
    assert p["default"] == [{"type": "reject"}]


def test_lucent_updates_need_a_signature_from_the_key():
    p = load().lucent_policy(FEDORA, SCOPE, KEY)
    assert p["transports"]["docker"][SCOPE] == [{
        "type": "sigstoreSigned", "keyPath": KEY,
        # cosign/sigstore signatures only name the repository.
        "signedIdentity": {"type": "matchRepository"}}]
    assert effective(p, "docker", f"{SCOPE}") == p["transports"]["docker"][SCOPE]


def test_everything_else_behaves_as_before():
    p = load().lucent_policy(FEDORA, SCOPE, KEY)
    for transport, scope in [("docker", "docker.io/library/fedora"), ("docker", "quay.io/toolbx/ubuntu-toolbox"),
                             ("docker", "ghcr.io/sidun-av/other"), ("docker", "registry.access.redhat.com/ubi9"),
                             ("docker-daemon", "x"), ("containers-storage", "localhost/x"), ("dir", "/tmp/x"),
                             ("oci", "/tmp/x"), ("oci-archive", "/tmp/x.tar"), ("docker-archive", "/tmp/x.tar")]:
        assert effective(p, transport, scope) == effective(FEDORA, transport, scope), (transport, scope)


def test_base_is_not_modified_and_rerunning_changes_nothing():
    base = copy.deepcopy(FEDORA)
    mod = load()
    once = mod.lucent_policy(base, SCOPE, KEY)
    assert base == FEDORA
    assert mod.lucent_policy(once, SCOPE, KEY) == once


def test_a_base_that_already_rejects_by_default_keeps_rejecting():
    base = {"default": [{"type": "reject"}], "transports": {}}
    p = load().lucent_policy(base, SCOPE, KEY)
    assert effective(p, "docker", "docker.io/x") == [{"type": "reject"}]


def test_cli_writes_valid_json(tmp_path):
    (tmp_path / "base.json").write_text(json.dumps(FEDORA))
    out = tmp_path / "policy.json"
    subprocess.run([sys.executable, str(SCRIPT), str(tmp_path / "base.json"), "--key", KEY,
                    "--scope", SCOPE, "--out", str(out)], check=True)
    assert json.loads(out.read_text()) == load().lucent_policy(FEDORA, SCOPE, KEY)
