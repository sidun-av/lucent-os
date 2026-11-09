# lucent-devices fixtures

Each directory holds `udev.txt` (`udevadm info --export-db`) and `kernel.log`
(`journalctl -k -b 0 -o cat`), scrubbed of serial numbers, UUIDs, MACs and
host names by `tests/devices/scrub.py`.

| Directory | Where it comes from | Real or constructed |
| --- | --- | --- |
| `ci-runner-azure/` | GitHub's `ubuntu-24.04` runner (a Hyper-V VM on Azure): the published x86_64 image as a container reading the runner's udev database, plus the runner's kernel log. Recorded by `.github/workflows/devices.yml` (`container` job), run 42690273537. | Real output, virtual hardware |
| `ci-runner-azure-mana/` | Same recording on another runner (run 42692882984), whose NIC is a Microsoft MANA adapter the hwdb has no model name for. | Real output, virtual hardware |
| `vm-x86-kvm/` | The x86_64 image booted under QEMU/KVM on the runner with emulated e1000e, Intel HDA, xHCI USB (keyboard, tablet, audio, stick), VGA and `pci-testdev` (`vm-x86` job). `udev-unbound.txt` is the same boot after unbinding `snd_hda_intel`. | Real output, emulated hardware |
| `laptop-constructed/` | Written by hand in the export-db format to cover what CI cannot emulate: Wi-Fi with firmware fallbacks, Bluetooth and GPU firmware missing, an unclaimed Broadcom BCM4352, a probe failure, i2c touchpad, webcam, a fingerprint reader left to userspace. Kernel messages use the exact formats the drivers print. | **Constructed**, not recorded on a real laptop |

No fixture here was recorded on real (non-virtual) hardware yet.
