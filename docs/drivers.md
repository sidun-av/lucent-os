# Proprietary drivers: Broadcom Wi-Fi, NVIDIA, Secure Boot

Status: research and a recommendation, 2026-11-09. Nothing here is
implemented. The owner decides the open questions at the end.

The owner's requirement is that sound, Bluetooth, USB, Wi-Fi and the
network work out of the box, as they do on Windows. Almost all of that
comes from the in-kernel drivers and `linux-firmware`, which Lucent
already ships. Two families of common hardware are the exception, because
their best (or only) driver is proprietary and built outside the kernel:
older Broadcom Wi-Fi chips and NVIDIA graphics. On a PC with Secure Boot
on, any driver built outside the kernel also brings a key-enrollment
screen. This document covers all three and ends with a recommendation.

When something doesn't work, `lucent-devices` (and the planned Settings >
Devices page, [specs/devices-page.md](specs/devices-page.md)) says so. An
unclaimed Broadcom chip already gets its own explanation there.

## 1. Broadcom Wi-Fi and `wl`

### Which chips need `wl`

Fedora's kernel has four open drivers for Broadcom Wi-Fi: `brcmfmac`
(FullMAC: newer PCIe, SDIO and USB chips), `brcmsmac` (older SoftMAC
PCIe chips), `b43` and `b43legacy` (older SoftMAC chips, reverse
engineered). Broadcom's own `wl` ("Broadcom STA") is the only driver for
the rest.

| Chip | PCI ID | Open driver | Notes |
| --- | --- | --- | --- |
| BCM4360 | 14e4:43a0 (and 14e4:4360) | none | `b43`: no. Not in `brcmfmac`'s PCIe table. **`wl` only.** |
| BCM4352 | 14e4:43b1 | none | `b43`: no. Not in `brcmfmac`'s table. **`wl` only.** |
| BCM43142 | 14e4:4365 | none in practice | `b43`: no. `brcmfmac` claims 4365 only with Broadcom's own subsystem ID 14e4:4365 (the BCM4365 router chip), not laptop cards. **`wl` only.** |
| BCM4331 | 14e4:4331 | `b43` (since Linux 3.2) | Works without `wl`. |
| BCM43224 / BCM43225 | 14e4:4353 / 4357 | `b43`, `brcmsmac` | Works without `wl`. |
| BCM43227 / BCM43228 | 14e4:4358 / 4359 | `b43` (since 3.17) | Works without `wl`. |
| BCM4313 | 14e4:4727 | `brcmsmac` | Works without `wl`. |
| BCM4312, BCM4321, BCM4322 | 14e4:4315, 4328/4329, 432b... | `b43` (BCM4321: partly) | Mostly work without `wl`. |
| BCM4350, 4354, 4356, 43570, 4358, 43602, 4364, 4377, 4378, 4387, 43752... | 14e4:43a3, 43df, 43ec, 43d9, 43e9, 43ba, 4464, 4488, 4425, 4433, 449d... | `brcmfmac` | Works without `wl` (needs firmware from `linux-firmware`, which Lucent ships). |

Sources: the b43 support table on
[wireless.docs.kernel.org](https://wireless.docs.kernel.org/en/latest/en/users/drivers/b43.html);
`brcmf_pcie_devid_table` in
[brcmfmac/pcie.c](https://github.com/torvalds/linux/blob/master/drivers/net/wireless/broadcom/brcm80211/brcmfmac/pcie.c)
and the IDs in
[brcm_hw_ids.h](https://github.com/torvalds/linux/blob/master/drivers/net/wireless/broadcom/brcm80211/include/brcm_hw_ids.h)
(checked 2026-11-09: no 43a0, 43b1 or 4360, and 4365 only as
`BRCMF_PCIE_DEVICE_SUB(0x4365, BRCM_PCIE_VENDOR_ID_BROADCOM, 0x4365, BCA)`).

### How common they are in 2015-2026 laptops

I found no public statistics that give a share. Qualitatively: the
`wl`-only chips are 802.11ac (BCM4352, BCM4360) or 802.11n (BCM43142)
parts from roughly 2012-2016. Known users are Intel MacBooks of 2013-2015
(BCM4360), some Dell XPS 13 (9343) and other ultrabooks of 2014-2015
(BCM4352), and low-end HP, Lenovo and Dell laptops of 2013-2016
(BCM43142). After about 2016 laptop makers moved to Intel, Realtek,
MediaTek and Qualcomm Wi-Fi, which all have in-kernel drivers; current
Apple Silicon and Intel Macs with BCM4364/4377/4378/4387 use `brcmfmac`.
So the affected group is real but small and shrinking: people bringing a
laptop from 2013-2016 to Lucent. This is my reading, not a measurement.

### What shipping `wl` costs

- **It breaks other Broadcom Wi-Fi.** RPM Fusion's `broadcom-wl` package
  installs a modprobe blacklist for `ssb`, `bcma`, `b43`, `brcmsmac` and
  `brcmfmac`
  ([broadcom-wl-blacklist.conf](https://github.com/rpmfusion/broadcom-wl/blob/master/broadcom-wl-blacklist.conf)),
  because `bcma` would otherwise claim the same chips first. Installed
  as-is, it would take Wi-Fi away from every `brcmfmac`/`b43` machine.
  Universal Blue ships `wl` **disabled** for this reason and offers
  `ujust configure-broadcom-wl` to turn it on ("Enabling WL breaks
  numerous other Wi-Fi adapters"):
  [50-akmods.just](https://github.com/ublue-os/packages/blob/main/packages/ublue-os-just/src/recipes/50-akmods.just).
  Lucent would have to do the same, or write a udev rule that loads `wl`
  only for the three IDs above (and keeps `bcma` off them).
- **It is abandonware kept alive by patches.** The last Broadcom release
  is 6.30.223.271 (2015). Distributions patch it for each new kernel;
  RPM Fusion added a patch for Linux 7.2 on 2026-07-28
  ([akmod-wl changelog](https://download1.rpmfusion.org/nonfree/el/updates/8/x86_64/repoview/akmod-wl.html)).
  Lucent tracks Fedora's kernel, so a `wl` that stops building would hold
  back the image or drop Wi-Fi for those users until RPM Fusion catches up.
- **It is out of tree**, so with Secure Boot on it needs the key
  enrollment in section 3.

## 2. NVIDIA

### What the open stack does on Fedora 45

Lucent already ships the open NVIDIA stack: the in-kernel `nouveau`
driver, NVIDIA's GSP firmware (`nvidia-gpu-firmware`, part of
`linux-firmware`) and Mesa's `nouveau` OpenGL and **NVK** Vulkan drivers
(Fedora's `mesa-vulkan-drivers` builds `libvulkan_nouveau.so`;
[mesa.spec](https://src.fedoraproject.org/rpms/mesa/blob/rawhide/f/mesa.spec),
Mesa 26.2). `nouveau` is signed with the Fedora kernel, so it loads under
Secure Boot with no extra step.

| GPU generation | Example cards | Open stack today | Proprietary driver |
| --- | --- | --- | --- |
| Turing, Ampere, Ada, Blackwell | GTX 16xx, RTX 20/30/40/50 | Good desktop. NVK is a conformant Vulkan 1.4 driver; the GSP firmware gives automatic reclocking, so the GPU runs at full clocks. Games run, at roughly half the proprietary driver's speed (below). | Current branch 620; since 615 NVIDIA ships only the open kernel modules ("nvidia-open"). |
| Maxwell 2, Pascal, Volta | GTX 9xx, GTX 10xx, Titan V | Desktop works, but nouveau cannot reclock these (their firmware must be signed by NVIDIA), so the GPU stays at boot clocks: fine for the desktop and video, poor for games. | Legacy branch 580 only (the last for these GPUs; security fixes into 2028). |
| Kepler, Maxwell 1 | GTX 6xx/7xx, GTX 750 | NVK supports Kepler and later; manual reclocking only. | No longer supported by NVIDIA (470 legacy). |

Sources: [NVK in the Mesa docs](https://docs.mesa3d.org/drivers/nvk.html)
("Kepler ... and later GPUs up to and including Ada", plus Blackwell;
conformant Vulkan 1.4); reclocking per generation on the
[nouveau project page](https://nouveau.freedesktop.org/); Turing and
Ampere GSP use by default in Fedora per the
[nouveau patch removing DRM_NOUVEAU_GSP_DEFAULT](https://lists.freedesktop.org/archives/nouveau/2025-July/048305.html);
580 as the last branch for Maxwell, Pascal and Volta per
[Tom's Hardware](https://www.tomshardware.com/pc-components/gpu-drivers/nvidia-to-axe-maxwell-pascal-and-volta-gpus-with-end-of-driver-support-580-series-drivers-will-be-the-last-to-support-gtx-900-and-1000-cards);
"starting in 615 only OpenGPU" from NVIDIA staff on the
[615 release thread](https://forums.developer.nvidia.com/t/615-release-feedback-discussion/382815);
the open kernel modules need the GSP, which Maxwell-Volta lack
([NVIDIA's blog](https://developer.nvidia.com/blog/nvidia-transitions-fully-towards-open-source-gpu-kernel-modules/)).
The 620.70.06 packages are current in the
[negativo17 repository](https://negativo17.org/repos/nvidia/fedora-44/x86_64/)
(checked 2026-11-09).

### The gaming gap

Phoronix's most recent full comparison (Linux 7.0, Mesa 26.1-dev, RTX
5080 against NVIDIA 590.48.01;
[review](https://www.phoronix.com/review/linux-70-nouveau)) found the
open stack slower in every test: about 72% of the proprietary driver in
the best case (3DMark Wild Life Extreme), about 50% in Batman: Arkham
Knight, Cyberpunk 2077 (low settings only; higher settings at 4K hung) and
HITMAN 3, about 40% in Counter-Strike 2, about 25% in YQuake2. Compute
(OpenCL via Rusticl) was not competitive. The Mesa 25.2 round put an RTX
4070 SUPER at about 47% and an RTX 4080 SUPER at about 45%
([review](https://www.phoronix.com/review/mesa-252-nvk-nvidia)). Mesa 26.2
(July 2026) narrowed the gap further but the proprietary driver still led
in most games ([news](https://phoronix.com/news/NVK-Mesa-26.2-Performance)).
Ray tracing and DLSS are behind as well (DLSS on NVK is experimental).

I could not open the Phoronix pages directly (HTTP 403 to automated
requests); the figures above come from the search engine's extracts of
those pages, so check them before quoting.

Summary for a Windows user: with a GTX 16xx or any RTX card the open stack
gives a working desktop, video, browsers and light games on day one; a
gamer loses about half their frame rate until they switch to NVIDIA's
driver. With a GTX 9xx/10xx the open stack is only good for the desktop.

## 3. Secure Boot and out-of-tree modules

Lucent boots under Secure Boot because it uses Fedora's shim and Fedora's
signed kernel. The kernel's lockdown then refuses any module not signed
by a key it trusts. `wl` and NVIDIA's modules (open or not) are built
outside Fedora, so someone has to sign them, and the PC has to trust that
key:

1. Lucent's CI signs the modules with a Lucent key (the private key in a
   CI secret), and the image carries the public certificate.
2. Once per PC, `mokutil --import lucent.der` queues the key with a
   one-time password.
3. On the next boot, before Lucent starts, **MokManager** appears: a
   plain blue text screen, in English only, with a short countdown.
   The user must choose "Enroll MOK", "Continue", "Yes", type the
   password they were shown, and reboot. Universal Blue's instructions
   show exactly this
   ([Bazzite: Secure Boot](https://docs.bazzite.gg/General/Installation_Guide/secure_boot/)).
   If it is skipped, the driver does not load (the open stack keeps
   working, so the desktop still appears).

For someone coming from Windows this is the scariest moment Lucent could
show: it looks like firmware setup or an error, and it is the only part
of Lucent that is not translated and not in Pebble Drift. Turning Secure
Boot off is not an acceptable instruction for this audience (Windows 11
needs it, and it is a security downgrade).

Fedora is working on a guided MOK flow for NVIDIA in GNOME Software
([bug 2300340](https://bugzilla.redhat.com/show_bug.cgi?id=2300340)),
but that targets package-based Workstation, not KDE or bootc images.

## 4. How Universal Blue and Bazzite do it

- **Modules built in CI, not on the PC.** `ublue-os/akmods` builds Fedora
  kernels and kmods daily in GitHub Actions and publishes them as OCI
  images per kernel: `common` (includes `wl`), `extra`, `nvidia`,
  `nvidia-open`, `zfs`
  ([ublue-os/akmods](https://github.com/ublue-os/akmods)). The `wl` build
  is `akmods --force --kernels "$KERNEL" --kmod wl` against the exact
  image kernel
  ([build-kmod-wl.sh](https://github.com/ublue-os/akmods/blob/main/build_files/common/build-kmod-wl.sh)).
- **Signed with their key.** The private key is a CI secret (the
  repository has an empty placeholder `certs/private_key.priv`); the
  public `certs/public_key.der` ships in the images via
  `ublue-os-akmods-addons`. They sign their own kernels with the same
  key.
- **Variant images.** Downstream images `COPY --from` the akmods image
  and install the RPMs: Bazzite publishes `bazzite` and `bazzite-nvidia`
  (and `-nvidia-open`), Bluefin publishes `-nvidia` / `-nvidia-open`. A
  user moves between them with `bootc switch` / `rpm-ostree rebase`. Their
  maintainers say the closed-module images will be dropped once they
  stop building
  ([forum](https://universal-blue.discourse.group/t/base-nvidia-images-nvidia-vs-nvidia-open/8157)).
- **Key enrollment** is either queued by the installer, so MokManager
  appears right after installation, or later with
  `ujust enroll-secure-boot-key`; the MOK password is the fixed string
  `universalblue`
  ([Bazzite: Secure Boot](https://docs.bazzite.gg/General/Installation_Guide/secure_boot/)).
  Their forums show where this goes wrong: firmware that never shows
  MokManager, users who miss the screen, updates that fail to boot until
  the key is enrolled.

## 5. The minimal honest path for Lucent

**Now: ship nothing proprietary; make the gap visible.** The default
image stays fully open, as the owner's "open source by default" asks:
every Wi-Fi chip with an in-kernel driver works out of the box, NVIDIA
cards from Turing on get a working desktop through `nouveau` + NVK with
no key enrollment. `lucent-devices` already reports an unclaimed Broadcom
chip as "Needs a driver" with its own explanation, and reports firmware
that failed to load. Cost: none beyond what is in this commit.

**Next, when the owner wants games on NVIDIA: one `lucent-os-nvidia`
variant, opt-in from the Devices page.**

- **Image.** `FROM ghcr.io/sidun-av/lucent-os` plus NVIDIA's open kernel
  modules (branch 620, Turing and newer) built in CI against that image's
  exact kernel, signed with a Lucent key, plus the userspace driver from
  negativo17 or RPM Fusion; x86_64 only. If the module fails to build
  against a new Fedora kernel, the variant keeps its previous build and
  the main image is not held back.
- **Switch.** On a PC with an NVIDIA GPU, the Devices page offers "Use
  NVIDIA's driver (better for games)". It runs `bootc switch` to the
  variant; if Secure Boot is on, it shows a one-time password (a few
  words, in large type) and a Pebble Drift walkthrough with photos of the
  four MokManager screens, then restarts. After the restart the page
  checks that the driver loaded and offers "Switch back" (`bootc switch`
  to the main image; `bootc rollback` also works).
- **Not included at first:** GTX 9xx/10xx (needs the separate 580 legacy
  branch, a second variant for an ageing group) and `wl` (rare hardware,
  and section 1's blacklist problem).

**Cost estimate** (estimates, not measured on a variant build):

- **CI time:** one more x86_64 image job per push to main. Today's amd64
  image job takes about 25 minutes (run 42682354588: 19:23:41-19:48:48).
  The variant is a layer on the published image plus a module build of
  about 5-10 minutes, so roughly 10-20 runner minutes per push. A
  separate installer ISO for the variant would add the `iso` workflow's
  time again; switching from an installed system avoids it.
- **Image size:** NVIDIA 620's packages are about 310 MB compressed without
  CUDA (x86_64 and 32-bit libs for Steam/Wine: `nvidia-driver-libs` 164 MB
  + 20 MB i686, `nvidia-driver-common` 32 + 33 MB, `nvidia-kmod-common`
  61 MB of GSP firmware; CUDA libs another 89 MB). The installed size is
  larger. Users of the main image download none of it.
- **Maintenance:** a kernel/driver mismatch roughly every few Fedora
  kernel releases; a signing key that must never leak (anyone with it can
  sign modules every enrolled Lucent PC trusts) and can't be rotated
  without every user enrolling again; support for the MokManager step;
  re-checking NVIDIA's licence for redistribution in an image (Universal
  Blue and RPM Fusion already redistribute it).

## Decisions only the owner can make

1. **Default image stays fully open?** (recommended: yes; no `wl`, no
   NVIDIA modules in the main image.)
2. **Build `lucent-os-nvidia` at all, and when?** It is the only way to
   close the ~50% gaming gap on NVIDIA. It means Lucent signs proprietary
   kernel modules with its own key and asks users through MokManager.
3. **Who holds the Secure Boot signing key** and where (a GitHub Actions
   secret, as Universal Blue does, or an offline key with a manual signing
   step)?
4. **Should the installer queue key enrollment** for NVIDIA PCs (the
   scary screen right after installation, as Bazzite does), or only when
   the user picks the NVIDIA driver later (recommended: only on request)?
5. **GTX 9xx/10xx (580 legacy) and Broadcom `wl`:** leave unsupported, with
   the Devices page's explanation, or add a second variant / an opt-in
   switch later?
