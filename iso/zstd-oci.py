#!/usr/bin/python3
"""Recompress an OCI image layout's layers from gzip to zstd, in place.

Usage: zstd-oci.py OCI_DIR [--level N] [--long N]

bootc-image-builder puts the system image on the installer ISO as an OCI
layout (/container) with gzip layers. zstd at a high level is markedly
smaller, and the installer (ostree-container via containers-image-proxy)
reads zstd layers as well as gzip ones.

Only the compression changes: each layer is decompressed, its content is
checked against the image config's diff_id for that layer, and it is
compressed again. The config (diff_ids, labels) and every annotation stay as
they are; the manifest and index.json get the new layer digests and sizes.
Nothing is modified unless every layer checks out. Uncompressed layers are
compressed too; zstd layers are left alone. Docker media types are refused
(zstd isn't valid in a Docker schema 2 manifest).

The --long window stays at 2^27 by default: that is the largest window a
zstd decoder accepts without being told otherwise.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

GZIP = "application/vnd.oci.image.layer.v1.tar+gzip"
ZSTD = "application/vnd.oci.image.layer.v1.tar+zstd"
TAR = "application/vnd.oci.image.layer.v1.tar"
CHUNK = 4 << 20


def blob_path(root: Path, digest: str) -> Path:
    algo, hexd = digest.split(":", 1)
    return root / "blobs" / algo / hexd


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(CHUNK):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def write_blob(root: Path, data: bytes) -> dict:
    digest = "sha256:" + hashlib.sha256(data).hexdigest()
    path = blob_path(root, digest)
    if not path.exists():
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_bytes(data)
        os.replace(tmp, path)
    return {"digest": digest, "size": len(data)}


def recompress(root: Path, layer: dict, diff_id: str, level: int, long: int, n: int) -> tuple[dict, Path]:
    """Write layer number n as zstd next to the old blob; return (new descriptor fields, path)."""
    src = blob_path(root, layer["digest"])
    if layer["mediaType"] == GZIP:
        unpack = [shutil.which("pigz") or "gzip", "-dc"]
    else:
        unpack = ["cat"]
    tmp = root / "blobs" / "sha256" / f".zstd-oci-{os.getpid()}-{n}"
    level_args = ["--ultra"] if level > 19 else []
    with open(src, "rb") as fin, open(tmp, "wb") as fout:
        dec = subprocess.Popen(unpack, stdin=fin, stdout=subprocess.PIPE)
        enc = subprocess.Popen(["zstd", "-q", "-c", "-T0", *level_args, f"-{level}", f"--long={long}"],
                               stdin=subprocess.PIPE, stdout=fout)
        h = hashlib.sha256()
        err: list[BaseException] = []

        def pump():
            try:
                while chunk := dec.stdout.read(CHUNK):
                    h.update(chunk)
                    enc.stdin.write(chunk)
            except BaseException as e:  # noqa: BLE001 - reported below
                err.append(e)
            finally:
                enc.stdin.close()

        t = threading.Thread(target=pump)
        t.start()
        t.join()
        rc_dec, rc_enc = dec.wait(), enc.wait()
    if err or rc_dec or rc_enc:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"recompressing {layer['digest']} failed (unpack {rc_dec}, zstd {rc_enc}, {err})")
    got = "sha256:" + h.hexdigest()
    if got != diff_id:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"layer {layer['digest']}: content is {got}, but the config's diff_id is {diff_id}")
    digest = sha256_file(tmp)
    return {"mediaType": ZSTD, "digest": digest, "size": tmp.stat().st_size}, tmp


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("oci_dir", type=Path)
    ap.add_argument("--level", type=int, default=19)
    ap.add_argument("--long", type=int, default=27)
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 2)
    a = ap.parse_args(argv)
    root = a.oci_dir

    index_path = root / "index.json"
    index = json.loads(index_path.read_text())
    if len(index.get("manifests", [])) != 1:
        print("expected exactly one image in the layout", file=sys.stderr)
        return 2
    mdesc = index["manifests"][0]
    old_manifest_bytes = blob_path(root, mdesc["digest"]).read_bytes()
    manifest = json.loads(old_manifest_bytes)
    if "docker" in manifest.get("mediaType", "") or any("docker" in layer["mediaType"] for layer in manifest["layers"]):
        print("Docker schema 2 media types: zstd layers need an OCI manifest", file=sys.stderr)
        return 2
    config = json.loads(blob_path(root, manifest["config"]["digest"]).read_bytes())
    diff_ids = config["rootfs"]["diff_ids"]
    if len(diff_ids) != len(manifest["layers"]):
        print("config has a different number of diff_ids than the manifest has layers", file=sys.stderr)
        return 2

    layers = manifest["layers"]
    todo = [i for i, layer in enumerate(layers) if layer["mediaType"] in (GZIP, TAR)]
    # Several layers at once: zstd only spreads one stream over several
    # threads when it is much larger than its window, and most layers aren't.
    # Biggest first, so the longest one doesn't start last.
    todo.sort(key=lambda i: -layers[i]["size"])
    results: dict[int, tuple[dict, Path]] = {}
    failures: list[str] = []
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        futures = {pool.submit(recompress, root, layers[i], diff_ids[i], a.level, a.long, i): i for i in todo}
        for fut in as_completed(futures):
            i = futures[fut]
            try:
                results[i] = fut.result()
            except RuntimeError as e:
                failures.append(str(e))
                continue
            print(f"layer {i + 1}/{len(layers)}: {layers[i]['size']} -> {results[i][0]['size']} bytes", flush=True)
    if failures:
        for _, tmp in results.values():
            tmp.unlink(missing_ok=True)
        print("diff_id check or recompression failed, nothing changed:", *failures, sep="\n  ", file=sys.stderr)
        return 1

    before = sum(layer["size"] for layer in layers)
    new_layers, written, replaced = [], [], []
    for i, layer in enumerate(layers):
        if i in results:
            fields, tmp = results[i]
            written.append((tmp, blob_path(root, fields["digest"])))
            replaced.append(layer["digest"])
            new_layers.append({**layer, **fields})
        else:
            new_layers.append(layer)
    after = sum(layer["size"] for layer in new_layers)

    for tmp, final in written:
        os.replace(tmp, final)
    manifest["layers"] = new_layers
    new_mdesc = {**mdesc, **write_blob(root, json.dumps(manifest, separators=(",", ":")).encode())}
    index["manifests"][0] = new_mdesc
    tmp_index = index_path.with_name("index.json.tmp")
    tmp_index.write_text(json.dumps(index, separators=(",", ":")))
    os.replace(tmp_index, index_path)

    keep = {new_mdesc["digest"], manifest["config"]["digest"], *(layer["digest"] for layer in new_layers)}
    for d in [mdesc["digest"], *replaced]:
        if d not in keep:
            blob_path(root, d).unlink(missing_ok=True)
    print(f"layers: {before} bytes (gzip) -> {after} bytes (zstd -{a.level} --long={a.long}), "
          f"{100 * (before - after) / max(before, 1):.1f}% smaller")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
