"""iso/zstd-oci.py: recompress the installer's OCI image layout (the
system image on the ISO, /container) from gzip to zstd without changing a
single byte of the layers' content (their diff_ids)."""
from __future__ import annotations

import gzip
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "iso" / "zstd-oci.py"
GZ = "application/vnd.oci.image.layer.v1.tar+gzip"
ZST = "application/vnd.oci.image.layer.v1.tar+zstd"

pytestmark = pytest.mark.skipif(not shutil.which("zstd"), reason="needs the zstd tool")


def digest(b: bytes) -> str:
    return "sha256:" + hashlib.sha256(b).hexdigest()


def put_blob(root: Path, data: bytes) -> dict:
    d = digest(data)
    (root / "blobs" / "sha256" / d.split(":")[1]).write_bytes(data)
    return {"digest": d, "size": len(data)}


def tar_of(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.PAX_FORMAT) as t:
        for name, content in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            info.mtime = 0
            t.addfile(info, io.BytesIO(content))
    return buf.getvalue()


def make_layout(root: Path, layers: list[tuple[str, bytes]], bad_diffid: int | None = None):
    """An OCI layout like bootc-image-builder's /container: index -> manifest -> config + layers."""
    (root / "blobs" / "sha256").mkdir(parents=True)
    (root / "oci-layout").write_text('{"imageLayoutVersion":"1.0.0"}')
    descs, diff_ids = [], []
    for i, (mt, raw_tar) in enumerate(layers):
        if mt == GZ:
            blob = gzip.compress(raw_tar, mtime=0)
        elif mt == ZST:
            blob = subprocess.run(["zstd", "-q", "-c"], input=raw_tar, capture_output=True, check=True).stdout
        else:
            blob = raw_tar
        desc = {"mediaType": mt, **put_blob(root, blob),
                "annotations": {"ostree.components": f"layer{i}"}}
        descs.append(desc)
        diff_ids.append(digest(raw_tar) if i != bad_diffid else digest(b"something else"))
    config = json.dumps({"architecture": "amd64", "os": "linux",
                         "config": {"Labels": {"containers.bootc": "1", "ostree.bootable": "1"}},
                         "rootfs": {"type": "layers", "diff_ids": diff_ids}}).encode()
    cdesc = {"mediaType": "application/vnd.oci.image.config.v1+json", **put_blob(root, config)}
    manifest = json.dumps({"schemaVersion": 2, "mediaType": "application/vnd.oci.image.manifest.v1+json",
                           "config": cdesc, "layers": descs,
                           "annotations": {"org.opencontainers.image.revision": "abc"}}).encode()
    mdesc = {"mediaType": "application/vnd.oci.image.manifest.v1+json", **put_blob(root, manifest),
             "annotations": {"org.opencontainers.image.ref.name": "latest"}}
    (root / "index.json").write_text(json.dumps({"schemaVersion": 2, "manifests": [mdesc]}))
    return config


def load(root: Path):
    index = json.loads((root / "index.json").read_text())
    mdesc = index["manifests"][0]
    mbytes = (root / "blobs" / "sha256" / mdesc["digest"].split(":")[1]).read_bytes()
    assert digest(mbytes) == mdesc["digest"] and len(mbytes) == mdesc["size"]
    return index, mdesc, json.loads(mbytes)


def blob(root: Path, d: str) -> bytes:
    return (root / "blobs" / "sha256" / d.split(":")[1]).read_bytes()


def run(root: Path, *args):
    return subprocess.run([sys.executable, str(SCRIPT), str(root), "--level", "3", *args],
                          capture_output=True, text=True)


def test_gzip_layers_become_zstd_with_identical_content(tmp_path):
    t1 = tar_of({"usr/bin/hello": b"hello world\n" * 1000})
    t2 = tar_of({"usr/share/doc/x": b"x" * 50000, "etc/os-release": b"ID=fedora\n"})
    config = make_layout(tmp_path, [(GZ, t1), (GZ, t2)])
    p = run(tmp_path)
    assert p.returncode == 0, p.stderr
    index, mdesc, manifest = load(tmp_path)
    assert [layer["mediaType"] for layer in manifest["layers"]] == [ZST, ZST]
    for layer, raw in zip(manifest["layers"], (t1, t2)):
        b = blob(tmp_path, layer["digest"])
        assert digest(b) == layer["digest"] and len(b) == layer["size"]
        out = subprocess.run(["zstd", "-dc"], input=b, capture_output=True, check=True).stdout
        assert out == raw
    # Config (diff_ids, labels) and every annotation are untouched.
    assert blob(tmp_path, manifest["config"]["digest"]) == config
    assert [layer["annotations"] for layer in manifest["layers"]] == [
        {"ostree.components": "layer0"}, {"ostree.components": "layer1"}]
    assert manifest["annotations"] == {"org.opencontainers.image.revision": "abc"}
    assert mdesc["annotations"] == {"org.opencontainers.image.ref.name": "latest"}


def test_old_blobs_are_removed(tmp_path):
    make_layout(tmp_path, [(GZ, tar_of({"a": b"a" * 4000}))])
    _, _, before = load(tmp_path)
    old = {before["layers"][0]["digest"]}
    old_manifest = json.loads((tmp_path / "index.json").read_text())["manifests"][0]["digest"]
    assert run(tmp_path).returncode == 0
    _, mdesc, after = load(tmp_path)
    present = {"sha256:" + p.name for p in (tmp_path / "blobs" / "sha256").iterdir()}
    assert present == {mdesc["digest"], after["config"]["digest"], after["layers"][0]["digest"]}
    assert not (old & present) and old_manifest not in present


def test_zstd_and_uncompressed_layers_are_handled(tmp_path):
    t_zst = tar_of({"already": b"z" * 3000})
    t_raw = tar_of({"plain": b"p" * 3000})
    make_layout(tmp_path, [(ZST, t_zst), ("application/vnd.oci.image.layer.v1.tar", t_raw)])
    _, _, before = load(tmp_path)
    assert run(tmp_path).returncode == 0
    _, _, after = load(tmp_path)
    assert after["layers"][0] == before["layers"][0]  # left as it was
    assert after["layers"][1]["mediaType"] == ZST
    out = subprocess.run(["zstd", "-dc"], input=blob(tmp_path, after["layers"][1]["digest"]),
                         capture_output=True, check=True).stdout
    assert out == t_raw


def test_a_layer_whose_content_does_not_match_its_diff_id_aborts_unchanged(tmp_path):
    make_layout(tmp_path, [(GZ, tar_of({"a": b"a" * 4000})), (GZ, tar_of({"b": b"b"}))], bad_diffid=1)
    index_before = (tmp_path / "index.json").read_bytes()
    blobs_before = sorted(p.name for p in (tmp_path / "blobs" / "sha256").iterdir())
    p = run(tmp_path)
    assert p.returncode != 0
    assert "diff_id" in p.stderr
    assert (tmp_path / "index.json").read_bytes() == index_before
    assert sorted(p.name for p in (tmp_path / "blobs" / "sha256").iterdir()) == blobs_before


def test_docker_media_types_are_refused(tmp_path):
    make_layout(tmp_path, [(GZ, tar_of({"a": b"a"}))])
    index, mdesc, manifest = load(tmp_path)
    manifest["layers"][0]["mediaType"] = "application/vnd.docker.image.rootfs.diff.tar.gzip"
    mbytes = json.dumps(manifest).encode()
    index["manifests"][0] = {**mdesc, **put_blob(tmp_path, mbytes)}
    (tmp_path / "index.json").write_text(json.dumps(index))
    p = run(tmp_path)
    assert p.returncode != 0 and "docker" in p.stderr.lower()


def test_reports_sizes(tmp_path):
    make_layout(tmp_path, [(GZ, tar_of({"a": bytes(range(256)) * 400}))])
    p = run(tmp_path)
    assert p.returncode == 0
    assert "gzip" in p.stdout and "zstd" in p.stdout and "bytes" in p.stdout


def test_many_layers_in_parallel_including_identical_ones(tmp_path):
    tars = [tar_of({f"f{i}": bytes([i]) * (1000 + 7 * i)}) for i in range(12)]
    tars.append(tars[0])  # the same layer twice, as layered images can have
    make_layout(tmp_path, [(GZ, t) for t in tars])
    p = subprocess.run([sys.executable, str(SCRIPT), str(tmp_path), "--level", "3", "--jobs", "4"],
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    _, _, manifest = load(tmp_path)
    assert len(manifest["layers"]) == len(tars)
    for layer, raw in zip(manifest["layers"], tars):
        out = subprocess.run(["zstd", "-dc"], input=blob(tmp_path, layer["digest"]),
                             capture_output=True, check=True).stdout
        assert out == raw
    assert not list((tmp_path / "blobs" / "sha256").glob(".zstd-oci-*"))
