"""Unit tests for the hardware audit's pure logic (run on the CI host, no image needed)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import hw_audit as A  # noqa: E402


# --- module path -> device class -------------------------------------------

@pytest.mark.parametrize("rel,cls,core", [
    ("drivers/net/wireless/intel/iwlwifi/iwlwifi.ko.xz", "wifi", True),
    ("drivers/net/ethernet/realtek/r8169.ko.xz", "ethernet", True),
    ("drivers/net/usb/r8152.ko.xz", "ethernet", True),
    ("drivers/bluetooth/btusb.ko.xz", "bluetooth", True),
    ("sound/soc/sof/intel/snd-sof-pci-intel-tgl.ko.xz", "audio", True),
    ("drivers/gpu/drm/amd/amdgpu/amdgpu.ko.xz", "gpu", True),
    ("drivers/gpu/drm/nouveau/nouveau.ko.xz", "gpu", True),
    ("drivers/gpu/drm/xe/xe.ko.zst", "gpu", True),
    ("drivers/media/usb/uvc/uvcvideo.ko.xz", "webcam", False),
    ("drivers/media/pci/intel/ipu6/intel-ipu6.ko.xz", "webcam", False),
    ("drivers/staging/media/ipu7/intel-ipu7.ko.xz", "webcam", False),
    ("drivers/usb/misc/ezusb.ko", "usb", False),
    ("drivers/thunderbolt/thunderbolt.ko.xz", "usb", False),
    ("drivers/hid/intel-ish-hid/intel-ish.ko.xz", "input", False),
    ("drivers/input/touchscreen/goodix_ts.ko.xz", "input", False),
    ("drivers/mmc/host/rtsx_pci_sdmmc.ko.xz", "cardreader", False),
    ("drivers/platform/x86/thinkpad_acpi.ko.xz", "laptop", False),
    ("drivers/misc/mei/mei.ko.xz", "laptop", False),
])
def test_classify(rel, cls, core):
    assert A.classify(rel) == (cls, core)


@pytest.mark.parametrize("rel", [
    "drivers/gpu/drm/vc4/vc4.ko.xz",      # not an audited GPU family
    "drivers/media/pci/cx23885/cx23885.ko.xz",
    "fs/btrfs/btrfs.ko.xz",
    "drivers/net/wireguard/wireguard.ko.xz",
])
def test_classify_out_of_scope(rel):
    assert A.classify(rel) is None


# --- firmware presence -------------------------------------------------------

def touch(root, rel):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"x")
    return p


def test_present_plain_and_compressed(tmp_path):
    touch(tmp_path, "rtl_nic/rtl8168h-2.fw.xz")
    touch(tmp_path, "amdgpu/foo.bin.zst")
    touch(tmp_path, "plain.bin")
    assert A.present(str(tmp_path), "rtl_nic/rtl8168h-2.fw")
    assert A.present(str(tmp_path), "amdgpu/foo.bin")
    assert A.present(str(tmp_path), "plain.bin")
    assert not A.present(str(tmp_path), "rtl_nic/rtl8168e-3.fw")


def test_present_dangling_symlink_is_missing(tmp_path):
    (tmp_path / "link.bin.xz").symlink_to(tmp_path / "nowhere.bin.xz")
    assert not A.present(str(tmp_path), "link.bin")


def test_present_glob(tmp_path):
    touch(tmp_path, "intel/sof/sof-tgl.ri.xz")
    assert A.present(str(tmp_path), "intel/sof/sof-*.ri")
    assert not A.present(str(tmp_path), "intel/sof/sof-adl*.ri")


# --- driver-tried alternatives (older API versions) --------------------------

def test_iwlwifi_older_api_satisfied_by_any_version(tmp_path):
    touch(tmp_path, "iwlwifi-so-a0-gf-a0-89.ucode.xz")
    assert A.satisfied(str(tmp_path), "iwlwifi-so-a0-gf-a0-86.ucode") == "iwlwifi-so-a0-gf-a0-89.ucode.xz"
    assert A.satisfied(str(tmp_path), "iwlwifi-so-a0-gf-a0-89.ucode") == "iwlwifi-so-a0-gf-a0-89.ucode"
    assert A.satisfied(str(tmp_path), "iwlwifi-ty-a0-gf-a0-89.ucode") is None


def test_versioned_rule_does_not_merge_chip_revisions(tmp_path):
    # rtl8168e-2 and -3 are different chip revisions, not API versions.
    touch(tmp_path, "rtl_nic/rtl8168e-2.fw")
    assert A.satisfied(str(tmp_path), "rtl_nic/rtl8168e-3.fw") is None


# --- allowlist ---------------------------------------------------------------

def test_parse_allowlist():
    text = """
# comment
b43/*            Broadcom b43 needs firmware cut from the proprietary wl driver (b43-fwcutter)
isci/isci_firmware.bin   never released for redistribution
"""
    al = A.parse_allowlist(text)
    assert al.match("b43/ucode5.fw").startswith("Broadcom")
    assert al.match("isci/isci_firmware.bin") == "never released for redistribution"
    assert al.match("iwlwifi-x.ucode") is None


def test_allowlist_requires_reason():
    with pytest.raises(ValueError):
        A.parse_allowlist("b43/*\n")


# --- repoquery output --------------------------------------------------------

def test_parse_fedora_files():
    out = """@@PKG linux-firmware
/usr/lib/firmware/rtl_nic/rtl8168h-2.fw.xz
/usr/lib/firmware/amdgpu/foo.bin.xz
@@PKG intel-vsc-firmware
/usr/lib/firmware/intel/vsc/ivsc_fw.bin.zst
/usr/share/doc/intel-vsc-firmware/README
"""
    idx = A.parse_fedora_files(out)
    assert idx["rtl_nic/rtl8168h-2.fw"] == "linux-firmware"
    assert idx["intel/vsc/ivsc_fw.bin"] == "intel-vsc-firmware"
    assert "README" not in " ".join(idx)


def test_fedora_provider_glob_and_version():
    idx = {"iwlwifi-so-a0-gf-a0-89.ucode": "iwlwifi-mvm-firmware",
           "intel/sof/sof-tgl.ri": "alsa-sof-firmware"}
    assert A.fedora_provider(idx, "intel/sof/sof-*.ri") == "alsa-sof-firmware"
    assert A.fedora_provider(idx, "iwlwifi-so-a0-gf-a0-80.ucode") == "iwlwifi-mvm-firmware"
    assert A.fedora_provider(idx, "nope.bin") is None


# --- gate --------------------------------------------------------------------

def rec(fw, cls="wifi", core=True, provider=None, allow=None):
    return A.Missing(fw=fw, modules=["m"], cls=cls, core=core, provider=provider, allow_reason=allow)


def test_gate_fails_on_core_missing_that_fedora_ships():
    fails = A.gate([rec("a.bin", provider="linux-firmware", allow="x")], online=True)
    assert [f.fw for f in fails] == ["a.bin"]


def test_gate_fails_on_core_missing_not_allowlisted():
    assert len(A.gate([rec("a.bin")], online=True)) == 1
    assert len(A.gate([rec("a.bin")], online=False)) == 1


def test_gate_passes_allowlisted_and_noncore():
    recs = [rec("a.bin", allow="not redistributable"),
            rec("b.bin", cls="webcam", core=False),
            rec("c.bin", cls="laptop", core=False, provider="linux-firmware")]
    assert A.gate(recs, online=True) == []


# --- dnf group info ----------------------------------------------------------

def test_parse_group_info():
    out = """Id                   : printing
Name                 : Printing Support
Description          : Install these tools to enable the system to print or act as a print server.
Installed            : no
Order                :
Langonly             :
Uservisible          : yes
Repositories         : fedora
Mandatory packages   : cups
                     : cups-filters
Default packages     : hplip
                     : ipp-usb
Optional packages    : splix
Conditional packages : foo-bar
"""
    g = A.parse_group_info(out)
    assert g["mandatory"] == ["cups", "cups-filters"]
    assert g["default"] == ["hplip", "ipp-usb"]
    assert g["optional"] == ["splix"]
    assert g["conditional"] == ["foo-bar"]


# --- package list ------------------------------------------------------------

def test_parse_package_list():
    text = """
# comment
alsa-sof-firmware   any      Intel/AMD laptop audio DSP firmware
thermald            x86_64   Intel thermal daemon
"""
    pk = A.parse_package_list(text)
    assert [p.name for p in pk] == ["alsa-sof-firmware", "thermald"]
    assert [p.name for p in A.for_arch(pk, "aarch64")] == ["alsa-sof-firmware"]
    assert [p.name for p in A.for_arch(pk, "x86_64")] == ["alsa-sof-firmware", "thermald"]


def test_parse_package_list_rejects_bad_arch():
    with pytest.raises(ValueError):
        A.parse_package_list("foo  ppc64le  reason\n")
