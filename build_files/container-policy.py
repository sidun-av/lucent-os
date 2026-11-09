#!/usr/bin/python3
"""Write the containers-policy.json that makes Lucent OS verify its updates.

Usage: container-policy.py BASE_POLICY --key PUBKEY --scope REPO [--out FILE]

Installed systems pull updates with bootc/rpm-ostree from REPO
(ghcr.io/sidun-av/lucent-os). With this policy, and the system's origin set
to `ostree-image-signed:` (`bootc switch --enforce-container-sigpolicy`),
an update that isn't signed with PUBKEY is refused. Signatures are sigstore
signatures stored next to the image (registries.d: use-sigstore-attachments).

- REPO requires a sigstore signature from PUBKEY (`signedIdentity`
  matchRepository: cosign-style signatures name only the repository).
- The default becomes `reject`: ostree-ext refuses `ostree-image-signed:`
  when the default is insecureAcceptAnything. To keep everything else as it
  was, each transport gets a "" scope with the base policy's old default,
  unless it already had one; existing scopes (registry.redhat.io...) stay.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import sys
from pathlib import Path

# The transports containers/image has; each keeps the old default via "".
TRANSPORTS = ("docker", "docker-daemon", "docker-archive", "containers-storage", "dir", "oci", "oci-archive")


def lucent_policy(base: dict, scope: str, key_path: str) -> dict:
    policy = copy.deepcopy(base)
    old_default = policy.get("default") or [{"type": "insecureAcceptAnything"}]
    transports = policy.setdefault("transports", {})
    for t in TRANSPORTS:
        scopes = transports.setdefault(t, {})
        if "" not in scopes:
            scopes[""] = copy.deepcopy(old_default)
    policy["default"] = [{"type": "reject"}]
    transports["docker"][scope] = [{
        "type": "sigstoreSigned",
        "keyPath": key_path,
        "signedIdentity": {"type": "matchRepository"},
    }]
    return policy


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("base", type=Path)
    ap.add_argument("--key", required=True)
    ap.add_argument("--scope", required=True)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)
    policy = lucent_policy(json.loads(a.base.read_text()), a.scope, a.key)
    text = json.dumps(policy, indent=4) + "\n"
    if a.out:
        tmp = a.out.with_name(a.out.name + ".tmp")
        tmp.write_text(text)
        os.replace(tmp, a.out)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
