# Make a Lucent OS USB stick on Windows

You need: a Windows 10 or 11 PC, a USB stick of **16 GB or more** (everything
on it will be erased), and about 20 minutes.

## 1. Download and join the ISO

The installer is about 8 GB (the default apps are on it, so they install
without internet), and GitHub serves it in parts of under 2 GB.

1. Open the release page (<https://github.com/sidun-av/lucent-os/releases>)
   and download into **one folder** (your Downloads folder is fine):
   - every part of your ISO: `lucent-os-<version>-amd64.iso.001`, `.002`, ...
     (`amd64` is right for almost every PC; `arm64` only for ARM laptops),
   - `SHA256SUMS`,
   - `join-lucent-iso.cmd` and `join-lucent-iso.ps1`.
2. Double-click **`join-lucent-iso.cmd`**. Windows may first ask whether to
   run a file from the internet: choose **Run**.
3. It checks every part, joins them into `lucent-os-<version>-amd64.iso`
   and checks the result. If a part is missing or damaged it says which one:
   download just that part again and double-click the script again.
4. When it says **Ready**, you can delete the `.001`, `.002`, ... files.

The script uses only what Windows includes (Windows PowerShell 5.1) and
changes nothing outside that folder. To also check the release signature,
install [cosign](https://docs.sigstore.dev/cosign/system_config/installation/)
first; the script then checks it by itself.

## 2. Write the ISO to the stick

The Lucent ISO is a "hybrid" image: it has to be written **as an image,
byte for byte**. Copying the `.iso` file onto the stick in Explorer does
not make it bootable ([CentOS installation guide](https://docs.centos.org/en-US/centos/install-guide/Making_Media_USB_Windows/)
says the same for this kind of image).

### With Fedora Media Writer (recommended)

Lucent's installer is Fedora's installer, and Fedora Media Writer is
Fedora's own tool for it.

1. Download Fedora Media Writer for Windows from its
   [releases page](https://github.com/FedoraQt/MediaWriter/releases)
   (`FedoraMediaWriter-win64-<version>.exe`; 5.3.2 was current in November
   2026). Use **5.3.0 or newer**: 5.2.9 on Windows wrote sticks that failed
   the installer's media check ([Red Hat bug 2448757](https://bugzilla.redhat.com/show_bug.cgi?id=2448757),
   fixed in 5.3.0).
2. Run it and allow it to make changes (it needs administrator rights to
   write to a drive; its Windows manifest asks for them).
3. Under **Select Image Source**, choose **Select .iso file** and pick
   `lucent-os-<version>-amd64.iso`.
4. Pick your USB stick and click **Write**.

It writes the image byte for byte ("in a dd-like fashion", its
[README](https://github.com/FedoraQt/MediaWriter/blob/main/README.md)), reads
it back to verify, and then runs the ISO's own media check (the checksum
the Lucent build implants in every ISO; Media Writer's
[`writejob.cpp`](https://github.com/FedoraQt/MediaWriter/blob/main/src/helper/win/writejob.cpp)
calls `mediaCheckFD` on the written drive). If that check fails, try
another USB port or stick.

### With Rufus

[Rufus](https://rufus.ie) (4.15 was the current stable release in November
2026) works too, with one setting that matters:

1. In Rufus, choose the stick under **Device**, then **SELECT** the
   `lucent-os-<version>-amd64.iso`, and click **START**.
2. Rufus says *"ISOHybrid image detected"* and asks how to write it. Choose
   **Write in DD Image mode**, not the ISO Image mode it marks as
   recommended.

Why: in ISO Image mode Rufus copies the files and rewrites the installer's
boot options. Its fix for Fedora-family installers (`inst.stage2` →
`inst.repo`, so the installer finds its files on the stick) is only applied
to ISO labels it knows, Fedora 33 to 39
([`src/rufus.c`](https://github.com/pbatard/rufus/blob/master/src/rufus.c),
`redhat8_derivative`). Lucent's ISO is labelled `Fedora-S-dvd-<arch>-45`,
so that fix is skipped. DD Image mode writes the image exactly as Fedora
Media Writer does; Rufus itself suggests DD mode "if you encounter issues
during boot" ([`rufus.loc`](https://github.com/pbatard/rufus/blob/master/res/loc/rufus.loc), MSG_275).
ISO Image mode has not been tried with Lucent's ISO.

## 3. Boot from the stick

1. Plug the stick into the PC you want to install on and turn it on.
2. Open its boot menu (usually **F12**, **F11**, **F8** or **Esc** right
   after power-on; the PC maker's manual says which) and pick the USB stick,
   the **UEFI** entry if there are two.
3. Choose **Install Fedora Linux 45**: the boot menu and the installer are
   Fedora's, and what they install is Lucent OS. (**Test this media &
   install** checks the stick first.) The default apps come from the stick,
   no network needed.

Status: the ISOs are tested in CI by an unattended install in a virtual
machine; they have **not been tested on real hardware yet**, including with
Secure Boot on.

## Afterwards: the stick back to normal

After writing, Windows shows the stick oddly (small or unreadable
partitions): that is expected for an installer stick. To use it for files
again, use Fedora Media Writer's **Restore** option ("reformat the drive back
to a standard single-partition layout", [README](https://github.com/FedoraQt/MediaWriter/blob/main/README.md)),
Rufus with a non-bootable format, or Windows' Disk Management (delete the
stick's partitions, then create a new one).
