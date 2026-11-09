#!/usr/bin/python3
"""Compare the system image on the ISO (an OCI layout) with the registry's.

Usage: oci-vs-registry.py OCI_DIR REGISTRY_MANIFEST.json

ostree-container (bootc, rpm-ostree) stores image layers under their
compressed digest, so after an install from the ISO the first update from
the registry downloads every registry layer the ISO didn't carry with the
same digest. Prints JSON: layers and bytes on the ISO, how many of them the
registry has with the same digest, and what that first update would
download.
"""
import json
import sys
from pathlib import Path


def main(oci: Path, reg_manifest: Path) -> int:
    index = json.loads((oci / "index.json").read_text())
    digest = index["manifests"][0]["digest"]
    manifest = json.loads((oci / "blobs" / "sha256" / digest.split(":")[1]).read_bytes())
    ours = {layer["digest"]: layer["size"] for layer in manifest["layers"]}
    theirs = {layer["digest"]: layer["size"] for layer in json.loads(reg_manifest.read_text())["layers"]}
    same = set(ours) & set(theirs)
    print(json.dumps({
        "layers": len(ours),
        "same_layers": len(same),
        "bytes": sum(ours.values()),
        "same_bytes": sum(ours[d] for d in same),
        "first_update_download_bytes": sum(s for d, s in theirs.items() if d not in ours),
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]), Path(sys.argv[2])))
