"""iso/oci-vs-registry.py: how much of the ISO's system image an installed
system can reuse when it first updates from the registry (ostree-container
keys layers by their compressed digest)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "iso" / "oci-vs-registry.py"


def layout(root: Path, layers: list[tuple[str, int]]) -> dict:
    (root / "blobs" / "sha256").mkdir(parents=True)
    manifest = {"schemaVersion": 2, "config": {"digest": "sha256:" + "c" * 64, "size": 1},
                "layers": [{"mediaType": "application/vnd.oci.image.layer.v1.tar+gzip", "digest": d, "size": s}
                           for d, s in layers]}
    raw = json.dumps(manifest).encode()
    import hashlib
    md = "sha256:" + hashlib.sha256(raw).hexdigest()
    (root / "blobs" / "sha256" / md.split(":")[1]).write_bytes(raw)
    (root / "index.json").write_text(json.dumps({"schemaVersion": 2, "manifests": [{"digest": md, "size": len(raw)}]}))
    return manifest


def test_counts_layers_and_bytes_the_registry_has_too(tmp_path):
    a, b, c = ("sha256:" + x * 64 for x in "abd")
    layout(tmp_path / "oci", [(a, 100), (b, 200), (c, 300)])
    reg = tmp_path / "reg.json"
    reg.write_text(json.dumps({"layers": [{"digest": a, "size": 100}, {"digest": c, "size": 300},
                                          {"digest": "sha256:" + "e" * 64, "size": 50}]}))
    p = subprocess.run([sys.executable, str(SCRIPT), str(tmp_path / "oci"), str(reg)],
                       capture_output=True, text=True, check=True)
    out = json.loads(p.stdout)
    assert out == {"layers": 3, "same_layers": 2, "bytes": 600, "same_bytes": 400,
                   "first_update_download_bytes": 50}
