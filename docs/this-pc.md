# "This PC" in Files

Files (Dolphin) opens on **This PC**, as Explorer does, following
`docs/mockups/concepts-2026/pebble-drift/01-desktop.png`:

- **Drives and devices**: the system drive as **Home** with the free space
  of the volume the user's files are really on; Windows partitions under
  the names `lucent-drive-letters` gives them (**"Local Disk (C:)"**), marked
  **Read-only**; USB drives, with **Eject**. Each drive's icon is a ring
  showing how full it is (accent for the system drive, slate for Windows,
  violet for USB, as the mockup's gauges).
- **Folders**: Desktop, Documents, Downloads, Pictures, Music, Videos (the
  XDG user folders, so localised names work), each with its item count.
- **Recent files**: the ten newest files the user opened (KDE's recent
  documents list), with their folder and date.

**This PC** is also the first entry of the sidebar, and what Home and New
Tab open. Screenshots from the VM: `docs/screenshots/real/v4-this-pc/`.

## The decision: a KIO worker, not a Dolphin patch

Robustness came first: Fedora updates Dolphin often, and anything that has
to be rebuilt or re-patched for every update can block every image build.
Closeness to the mockup came second. Three ways were evaluated.

| | (a) Dolphin patch, rebuilt from Fedora's SRPM | (b) KIO worker `thispc:/` (**chosen**) | (c) a plugin that draws its own page over Dolphin's view |
| --- | --- | --- | --- |
| How | Patch Dolphin's view container to show an overview page; rebuild `dolphin` from the SRPM in a build stage for x86_64 and aarch64 and replace the base image's package | A small C++ KIO worker (`build_files/thispc/`) lists folders, drives and recent files as items; Dolphin shows them like any folder | An in-process plugin (Dolphin loads overlay-icon and style plugins) finds Dolphin's view widget at runtime and covers it with a custom page when the URL is `thispc:/` |
| Interfaces it depends on | Dolphin's private source: `dolphinviewcontainer.cpp`, `dolphinmainwindow.cpp`, `views/dolphinview.cpp` | KF6's public, ABI-stable API (`KIO::WorkerBase`, `KRecentDocument`, Solid and `KDEDModule` for the refresher), `lsblk`, udisks | Dolphin's private widget tree (class names, layout) at runtime |
| What an update can break | **The build**: the patch stops applying, or the SRPM version no longer matches the base image | Nothing in Dolphin; a KF6 major release (KF7) would need a port | No build, but the page can misbehave or vanish silently after any Dolphin release |
| Closeness to the mockup | Exact (cards, ring gauges, a recent-files table) | Grouped icon view: section headers, ring icons, two grey detail lines; Dolphin's look, not the mockup's cards | Close (custom drawing), but focus, keyboard, selection, drag and drop and context menus all have to be rebuilt by hand |

**Evidence for (a).** Measured in the aarch64 test VM (4 vCPU, Apple M4,
Fedora 45 container), with Fedora's `dolphin-26.08.2-3.fc45` SRPM and a
3-line patch (`viewproperties.cpp`): `dnf builddep` installs **254 packages**
(172 MiB download, 722 MiB installed), `rpmbuild -bb` takes **157 s** for
243 compile units; the spec uses `%autosetup -p1`, so a `PatchN:` line is
enough. The build cost is not the problem. The churn is:

- Fedora shipped **20 stable `dolphin` updates to F44** between October 2025
  and November 2026 (three feature releases: 25.12, 26.04, 26.08) and 14 to
  F45 since February 2026 (Bodhi). Every one needs the patched RPM rebuilt
  from exactly that SRPM, or the image keeps an older Dolphin than the base.
- Upstream, in the year before 26.08: **19 commits** to
  `dolphinviewcontainer.cpp`, **32** to `dolphinmainwindow.cpp`, **39** to
  `views/dolphinview.cpp` (invent.kde.org API). An overview page touches all
  three, so a rebase is likely at every feature release (three a year).

So (a) costs a rebuild in CI for every Dolphin update (about 3 to 5 min per
architecture, plus 254 build dependencies) and a patch rebase several times
a year, and when the rebase is late, either the image build fails (blocking
every update, including security fixes) or the build falls back to stock
Dolphin and the page silently disappears.

**(c)** cannot break the build, but it trades that for runtime breakage
nobody notices until a user does, and a hand-made page loses everything
Dolphin's view gives for free (keyboard navigation, type-ahead, selection,
drag and drop, "Open with", accessibility). Not worth it for one page.

**(b)** uses only interfaces KDE keeps stable for the life of KF6, is built
in the image against whatever KF6 the base has (about 20 s of compiling;
the worker is 240 KB, the refresher 80 KB), and leaves Dolphin untouched: a
Dolphin update can't break it, and items behave like files and folders
everywhere else (double-click, drag and drop onto a folder, copy, "Open
with", Properties). Listing `thispc:/` takes 0.08 s in the VM
(`kioclient ls`, process start included).

**(b) has one cost (c) and (a) don't:** Dolphin 26.08 keeps its own view
for a non-local location only when each folder keeps its own view, and then
shares that one view among all non-local locations. So Lucent turns
`GlobalViewProps` off (Explorer remembers each folder's view too), and the
view seeded for This PC (grouped, two grey lines, no previews) is also what
a phone (`mtp:/`), a network share or Network show until the user changes
it there.

### Maintenance cost of (b)

- **Per Dolphin update: none.** Per KF6 update: none expected (public API).
  The image build compiles and unit-tests the worker every time, and **never
  fails because of it**: if the worker doesn't build, its tests fail or it
  can't list `thispc:/`, the image is built anyway with Files opening on Home
  as stock Dolphin does and no This PC in the sidebar, and the CI run shows a
  warning annotation (`build_files/thispc.sh`). Updates are never held back.
- **What it relies on in Dolphin's behaviour** (not its code), checked in
  `docs/screenshots/real/v4-this-pc/`: grouping by "Type" puts folders
  before files and then orders groups by their text (so drives, folders,
  recent files in English and Russian); the "Owner" and "User Group" roles
  are the two grey lines under each name; non-local locations share one set
  of view properties (`~/.local/share/dolphin/view_properties/remote/`). If
  Dolphin changed any of these, This PC would still list everything, only
  less neatly.
- **Translations** must stay short: a detail line has about 17 characters
  under a 64 px icon ("USB drive · %1" is "USB · %1" in Russian; the comment
  in `po/lucent-thispc.ru.po` says so).
- **KF7** (no date announced) will need a port of ~500 lines, as every KIO
  worker will.

### Where (b) differs from the mockup

- Dolphin draws items, not cards: folders and drives are 64 px icons with
  two grey lines ("212 items"; "18 GiB free" / "of 40 GiB"; "4.0 GiB free" /
  "Read-only"; "1.8 GiB free" / "USB drive · 4.0 GiB"; "Documents" /
  "Today") instead of cards with bold names and a "Read-only" pill (a lock
  emblem sits on the Windows drive's ring); recent files are icons, not a
  table with Folder / Modified / Size columns.
- The grey lines are Dolphin's "Owner" and "User Group" columns, so the
  Details view (Ctrl+3) of This PC titles them that way.
- **Drives come first**, then folders, then recent files (the mockup has
  folders first). Dolphin sorts groups by their title with ICU collation,
  which ignores spaces and punctuation, so no invisible prefix can reorder
  them (tried: hair spaces, U+200A; the unit test caught it on Fedora). It
  matches Windows 11, whose This PC shows only the drives.
- Within a section Dolphin sorts by name, not by the mockup's order: folders
  alphabetically, drives alphabetically ("Home", "KINGSTON", "Local Disk
  (C:)"), recent files alphabetically (they are the ten newest).
- The percentage is drawn by the ring, not written inside it; the ring's
  colours are fixed between the light and dark tokens (they don't follow a
  changed accent), see `design/gen_drive_gauges.py`.
- USB drives are named by their label ("KINGSTON"); only NTFS partitions get
  drive letters (`lucent-drive-letters`, unchanged).
- Opening a drive that isn't mounted yet (only when polkit wouldn't let the
  page mount it silently, or after the user unmounted it) shows that drive's
  top folder once in This PC's grouped view: Dolphin doesn't reload view
  properties after a KIO redirection (`DolphinView::slotDirectoryRedirection`).
  Its subfolders, and the drive opened when mounted, look as usual (`08`).
- Removing a file from the recent list from This PC isn't offered: nothing on
  the page can be renamed, moved or deleted (`thispc.json`), so This PC can't
  delete a user folder by accident either.

## How it works

| Piece | File | What |
| --- | --- | --- |
| Logic | `build_files/thispc/core/` | Which drives to show and how to name them (from `lsblk`'s JSON; the VM's own output is a test fixture), free space, ring step, size precision, user folders, recent files, the items' fields. Plain Qt Core; `tests/core_test.cpp` (28 tests), run on the Mac, on Ubuntu in CI and on Fedora in the image build |
| Worker | `build_files/thispc/worker.cpp`, `thispc.json` | `thispc:/`: reads `lsblk`, `/proc/self/mountinfo`, `statvfs`, `KRecentDocument`, the XDG dirs on every listing (Solid's cache inside the long-lived worker missed a drive it had just mounted and newly plugged sticks); mounts a drive when it is opened (udisks; polkit may ask), redirects to its folder. Also answers "free space" for the status bar on This PC |
| Refresh | `build_files/thispc/notifier.cpp` | kded module: a drive plugged in, removed, mounted or unmounted refreshes an open This PC (KDirNotify), no process of its own |
| Text | `build_files/thispc/core/text.cpp`, `po/lucent-thispc.ru.po` | English source, Russian translation (KI18n domain `lucent-thispc`); `tests/test_i18n.py` checks every string |
| Eject | `system_files/usr/share/kio/servicemenus/lucent-thispc-eject.desktop`, `usr/libexec/lucent/thispc-eject`, `usr/share/mime/packages/lucent-thispc.xml` | USB drives on the page are `inode/x-lucent-removable-drive` (a kind of folder) and get **Eject** in the context menu: unmount every partition, power the drive off (udisks), "It is safe to remove the drive now." Only removable disks are ever powered off (tested) |
| Ring icons | `design/gen_drive_gauges.py` → `usr/share/icons/hicolor/scalable/devices/lucent-drive-*` | 84 rings (4 kinds × 0–100 % in steps of 5) plus "not opened yet", in colours that read on light and dark windows (KDE recolours `ColorScheme` SVGs only in themes that follow the colour scheme, not hicolor; the Lucent themes are rebuilt from scratch by `design/gen_icons.py`) |
| Start page, sidebar, view | `system_files/etc/xdg/dolphinrc`, `usr/libexec/lucent/design-defaults` | `HomeUrl=thispc:/`; `GlobalViewProps=false` (each folder keeps its own view, as in Explorer, and This PC can keep its grouped view); This PC first in the sidebar (added once to existing sidebars); the view of `thispc:/` seeded per user |
| Build | `build_files/thispc.sh` | Compiles against the image's KF6, runs the unit tests (Fedora's ICU), installs, removes the toolchain, checks the worker lists `thispc:/` |

Drives the page lists: every file system `lsblk` sees, except the OS's own
(the devices behind `/`, `/sysroot`, `/etc`, `/var`, `/boot`, `/boot/efi`,
swap), EFI / Microsoft reserved / Windows recovery partitions, containers
(LUKS, BitLocker, LVM, RAID members: a locked BitLocker partition is not
shown) and internal partitions under 1 GiB (recovery and OEM tools; the same
rule as `lucent-drive-letters`). Windows partitions and USB
drives that aren't mounted yet are mounted while the page is listed, without
a password prompt (`auth.no_user_interaction`; polkit decides: USB drives of
the active user, and Lucent's rule for wheel members' Windows partitions,
always read-only), so their free space shows as in Explorer. A Windows
partition is opened this way once per session: unmounted by the user, it
stays unmounted. If polkit says no, the page shows the size, and the drive
is mounted (polkit may ask) when it is opened.

## The "0 B free" status bar

Dolphin's status bar showed "0 B free" (a full bar) in every folder of the
home directory. Root cause, read in the sources of the versions in the image
(Dolphin 26.08.2, KF 6.31) and confirmed in the VM:

1. Dolphin asks Solid which volume holds the folder
   (`Solid::Device::storageAccessFromPath`, `statusbar/mountpointobservercache.cpp`):
   the longest volume mount path that is a prefix of the folder.
2. Solid's UDisks2 backend gives each block device **one** mount path. The
   system partition is mounted four times (`/etc`, `/sysroot`,
   `/sysroot/ostree/deploy/default/var`, `/var`) and none of them is the
   btrfs root of the subvolume, so Solid picks the first: **`/etc`**
   (`solid-hardware6 details …/vda3` → `StorageAccess.filePath = '/etc'`).
3. The only other candidate is Solid's entry for the read-only composefs
   root, **`/`**. It wins for `/var/home/anna`, and `/` has 0 bytes free.

Qt's `QStorageInfo("/var/home/anna")` itself answers correctly (`/var`,
29 GB free in the VM), as does `df`. Dolphin's exact steps, run in the VM's
session (a 30-line tool calling the same Solid and KIO functions):

```
/var/home/lucent/Documents
  Solid volume: /org/kde/fstab/overlay/ (/)
  KIO free space of file:///      total  0.0 GiB, available  0.0 GiB
thispc:/
  KIO free space of thispc:/      total 40.0 GiB, available 17.9 GiB
$ df -h /var/home/lucent
/dev/vda3   40G   22G   18G  55% /var
```

What Lucent does: **This PC shows the right numbers** (it measures the home
folder itself with `statvfs`, and it never asks Solid for the system
volume), and **the status bar on This PC** gets them too (the worker
answers Dolphin's free-space request, above). In ordinary folders the Lucent style
plugin keeps hiding the free-space part when it would show the composefs root
(`build_files/lucent-style`, track restyle-shell). A real fix belongs in
Solid (consider every mount point of a device, or skip a read-only overlay
root when a deeper mount matches); patching Solid in the image would have the
same rebuild problem as (a).
