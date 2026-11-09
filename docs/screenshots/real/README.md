# Real Lucent OS in a VM: screenshots, measurements, gaps

These are real captures of the **published image** (`ghcr.io/sidun-av/lucent-os`,
commit `b1728a9`), booted with `tools/vm/` (QEMU 11.1, aarch64 + HVF on an
Apple M4, 4 vCPU, 6 GB RAM, 1920x1080 virtio-gpu, **software rendering**: no
virgl on macOS). The VM disk is the test-only qcow2 from the `vm` workflow
(autologin user `lucent`, SSH key, plus a fake 4 GB NTFS "Windows" disk), so
there is no installer step. The release image has none of these extras.

## Screenshots

| File | What it shows |
| --- | --- |
| `00-before-fix-plasma-setup-blocks-boot.png` | **Before the fix** (first CI image, from `7d7e9c4`): a fresh boot lands on Fedora's *plasma-setup* "Welcome to KDE Plasma / Start setup" screen instead of the desktop, although a user already exists. That build still forced a Russian locale. |
| `01-first-login-desktop-wizard.png` | Fresh first boot, English: top bar (launcher left; tray and clock right; no global menu), floating dock, and **Move from Windows** autostarted because a Windows disk is present. Window buttons are on the right. The dock shows blank placeholder icons for Firefox, ONLYOFFICE and Okular because their Flatpaks are still downloading. |
| `02-launcher-meta.png` | The Win key alone opens the launcher, and Favorites are now filled. Firefox and Okular are missing from Favorites because they were not installed yet at first login. |
| `03-dolphin-meta-e.png` | Win+E opens Dolphin (Files). Under Devices, the Windows partition row has **no name**: just a red capacity bar. |
| `04-alt-tab.png` | Alt+Tab with the thumbnail grid (Konsole and Dolphin). Captured on the previous build; the window-switcher config is the same. |
| `05-russian-user-wizard-ru-layout.png` | A second user with a Russian locale, on a system whose installer layouts were `us,ru`: the wizard is in Russian, the date uses the Russian format, and the tray shows **ru** after Alt+Shift. |

## Checks

| Check | Result | How it was checked |
| --- | --- | --- |
| Fresh boot reaches the desktop | **PASS** after fix (was FAIL, `00`) | `01`; `plasma-setup.service` skipped by `ExecCondition` ("a regular user already exists") |
| English by default | **PASS** | `LANG=en_US.UTF-8`, UI in English (`01`–`03`) |
| Top bar: launcher, tray, clock; no global menu | **PASS** | `01`; panel applets: kickoff, panelspacer, systemtray, digitalclock (no appmenu) |
| Floating bottom dock as taskbar | **PASS** | `01`, `03`: pinned apps, running app highlighted, grouped |
| Window buttons on the right (minimise, maximise, close) | **PASS** | `01`, `03`; kwinrc `ButtonsOnRight=IAX` |
| Win alone opens the launcher | **PASS** | `02` |
| Win+E opens Dolphin | **PASS** | `03` |
| Alt+Tab with thumbnails | **PASS** | `04` |
| Win+D shows the desktop; Win+L locks | **PASS** | screenshots during the run; `LockedHint=yes` after Win+L |
| Alt+Shift and Win+Space switch layouts (2+ layouts) | **PASS** | `05`; layout index 0→1 with Alt+Shift, 1→0 with Win+Space |
| Installer layouts are used (no hard-coded us+ru) | **PASS** | English user: no `LayoutList` (plain `us`); after `localectl set-x11-keymap us,ru`, the new user got `LayoutList=us,ru` |
| First-boot Flatpaks | **PASS** | 10/10 apps (`flatpak list`), about 2 min, `flatpaks-v1.done`; no longer holds up boot |
| Wizard autostarts on first login | **PASS** | `01` (English), `05` (Russian). It no longer starts for the `plasma-setup` system user. |
| Wizard can read the Windows disk | **FAIL** | "Whose files…" page: `udisksctl mount` → `NotAuthorizedCanObtain`. See gap 1. |
| Windows drive name in Dolphin | **FAIL** | udisks `HintName: Windows (C:)` is correct, but Dolphin's Devices row shows no text (`03`). See gap 2. |
| Launcher Favorites | **PARTIAL** | filled (fix), but Flatpak entries that arrive after first login are dropped (`02`) |
| Lock-screen password entry | not verified | QMP typing did not reach the greeter field; unlocked via `loginctl unlock-session`. This is a harness issue, not a product finding. |

## Measurements

| Metric | Value |
| --- | --- |
| Boot, normal (2nd+ boot) | **4.96 s** to `graphical.target` (kernel 0.26 s + initrd 1.28 s + userspace 3.42 s; UEFI firmware not included) |
| Boot, first (Flatpaks downloading) | **8.7 s** (before the fix: **2 min 4 s**, because `lucent-flatpak-setup` was `Type=oneshot`) |
| Idle RAM, 2 min after login | **2422 MB used** of 5889 MB (1938 free, 2135 cache, 3467 available), swap 0 |
| Largest processes (PSS) | plasmashell 540 MB, plasma-keyboard 202 MB, kwin_wayland ~385 MB RSS. The on-screen keyboard is enabled by Fedora's `kde-settings` (`kwinrc InputMethod=…plasma.keyboard`, `VirtualKeyboardEnabled=true`), even without a touchscreen. llvmpipe inflates all three. |
| Running services | **30** system, **34** user (206 loaded units) |
| Disk | `/sysroot` **18 GB used** of 40 GB: OS deployment ≈ 9.4 GB plus Flatpaks **8.6 GB** (10 apps with runtimes). `/` is composefs (read-only, always "100%") |
| Failed units | none |

## What was broken and is fixed (`b1728a9`, `c9360fe`)

1. **plasma-setup blocked boot**: Fedora 45 runs it on every boot until `/etc/plasma-setup-done` exists, even when the installer created a user. It now runs only when no regular user exists.
2. **Wizard autostarted inside the plasma-setup session** (uid 969): it now autostarts only for uid ≥ 1000 (with a test).
3. **First boot waited about 2 min** for Flathub (`Type=oneshot` holds `graphical.target`): the unit is now `Type=exec`.
4. **Empty launcher Favorites**: the layout script set `favoritesPortedToKAstats=true`, which skips seeding. That line is removed; Lucent's list is in `/etc/xdg/kicker-extra-favoritesrc`.
5. **English as the primary language** (owner decision): gettext catalogs (`migration-wizard/po/ru.po`), "Local Disk (C:)" / "Data (D:)", `en_US.UTF-8` default, installer keyboard layouts instead of a hard-coded us+ru.
6. VM test image: Fedora 45 uses **Plasma Login Manager**, not SDDM, so the autologin config moved to `/etc/plasmalogin.conf.d/`.

## Open functional gaps (next phase)

1. **The wizard can't mount an internal Windows disk.** udisks classifies internal disks as *system* devices, and mounting one (`org.freedesktop.udisks2.filesystem-mount-system`) needs admin auth, while `volumes.udisksctl_mount_cmd` passes `--no-user-interaction`. This hits real laptops too, not only the VM. Fix: either a polkit rule that allows read-only NTFS mounts for active local `wheel` users, or drop `--no-user-interaction` and let polkit-kde ask for the password. Either way, verify in the VM.
2. **Dolphin Devices shows a blank name** for the NTFS partition, both with and without the udev `UDISKS_NAME`. Investigate the Solid/Dolphin item text (the narrow Places panel may elide it).
3. **Favorites lose apps installed after first login** (Firefox, Okular). Seed Favorites after `lucent-flatpak-setup` finishes, or preinstall the Flatpaks in the image.
4. **No progress UI for first-boot apps**: the dock shows blank icons for about 2 minutes.
5. **plasma-keyboard runs on every desktop** (~200 MB PSS here). Decide whether to disable it when no touchscreen is present.
6. **Lock screen and login screen use Fedora's wallpaper**, not Lucent's.

## Delta vs `docs/mockups/` (ordered by visual impact)

1. **Panel layout differs from the mockups.** The mockups have **one bottom bar**: launcher button, a "Поиск" search field, the centred dock, and the tray (RU, Wi-Fi, volume, battery) with a two-line clock. The configured design (and the real desktop) is a **thin top bar plus a separate small floating dock**. The design decision has to be made before polishing either.
2. **Launcher.** Mockup `02`: full-screen overlay with a centred large search field, category chips (Офис, Графика…), 80 px colourful app tiles in a 6-column grid, and Win/Esc hints. Real: stock **Kickoff** popup (about 400×330 px, top-left) with a category sidebar, green "new" dots, 48 px icons, and a Sleep/Restart/Shut Down/Session text footer.
3. **Migration wizard.** Mockup `04`: "Добро пожаловать в Lucent" two-pane window with a step list on the left, a found-disk card, checkbox lists with sizes, and a primary "Перенести" button. Real: plain `QWizard`, a bold heading over an empty white page, a grey button strip, no steps, and no branding.
4. **Files (Dolphin).** Mockup `01`: "Этот компьютер" view with folder cards (item counts), drive cards with capacity bars and a "только чтение" badge, recent files, and a classic **menu bar**. Real: stock Dolphin home with an icon grid and no menu bar (hamburger instead), a cramped Places panel ("Recent Loc…" truncated), the unnamed drive row, and a small default window (~950×720).
5. **Window decoration.** Mockup: thin `–  ▢  ×` glyphs, title centred, the title bar merges with the toolbar. Real: Breeze chevrons `⌄ ⌃ ✕`, and the grey title bar is a separate band above a second grey toolbar band.
6. **Dock.** Mockup: 40–44 px colourful rounded icons on a translucent blurred bar with dot indicators. Real: about 32 px icons in a white box with a hairline border, and the active app marked by a square blue fill.
7. **Tray and clock.** Mockup: `RU`, Wi-Fi, volume, battery and a two-line clock (`14:32` / `вс, 8 нояб.`). Real: monochrome Breeze symbols (a muted-speaker icon with a red slash, a brightness sun, a display icon, an expander chevron) and a one-line `11/9/26 7:31 AM`.
8. **Settings and store** (mockups `03`, `03b`, `03c`, `06`). Real: stock System Settings and Discover. There is no "Как в Windows" page, no Windows-equivalent app cards, and no "Новое поколение" section.
9. **Wallpaper and colour.** Real Lucent gradient is pale lavender. Mockups use a richer blue→pink→peach gradient. Lock and login screens show Fedora's gear artwork.
10. **Icons.** Mockup: custom saturated app icons (Files, Store, Settings). Real: Breeze icons (dark-blue folders, a grey placeholder page for apps not yet installed, the system-settings "sliders" icon on black).

### Dated or heavy elements, per screenshot (element → what's wrong → what it should be)

**`01` desktop and wizard**
- Top bar → flat opaque white strip with a hard 1 px bottom line, ~26 px tall, 16 px icons hugging the edges → translucent blurred bar with ~8 px side padding and 18–20 px icons, or drop it per delta 1.
- Dock container → white rectangle with ~4 px corners, a grey hairline border and a tight 4 px inner padding → 16–20 px radius, no border, soft large-radius shadow, 8–10 px padding, 40+ px icons.
- Running-app marker → full-height square blue fill behind the icon (Breeze task highlight) → small dot or pill under the icon.
- Wizard window → Breeze title bar with chevron buttons, then a bold left-aligned heading with no margin above it, then ~400 px of empty white → generous 32–40 px content padding, a step sidebar, content cards with 12 px radius.
- Wizard footer → grey band with a hairline separator and three equal grey buttons ("Next" barely tinted) → white footer; one filled accent primary button; quiet text-style secondary buttons.
- Checkbox "Don't show this again at login" → default Breeze 16 px square with a thin grey border → accent-coloured rounded checkbox or a switch.

**`02` launcher**
- Popup → hard-edged panel attached to the top-left corner, thin border, no shadow separation from the bar → floating, rounded (16 px), blurred, centred or full-screen.
- Category sidebar → dense 34 px rows with outline icons and green "new" dots → chips or a lighter list with more spacing; no dots.
- App grid → 48 px icons with wrapping two-line labels in tight cells, a selected tile shown as a square blue box → 64–80 px icons, rounded hover only, even spacing.
- Footer → four text buttons with small outline icons (Sleep/Restart/Shut Down/Session ▾) crammed in a row → a single power icon menu and the user avatar at top-right.
- User header → pink placeholder "L" circle with a small grey name → real avatar or a monogram on an accent gradient, bigger name.
- Search field → small (~28 px), grey-bordered, with a filter-sliders button and a pin button next to it → large rounded field with a placeholder and no extra buttons.

**`03` Dolphin**
- Title bar and toolbar → two stacked grey bands (title, then a toolbar with back/forward arrows, view-mode menu, "Split", search, hamburger) → unified header with the breadcrumb, view toggles and search in one row, plus an optional menu bar as in the mockup.
- Breadcrumb → square-cornered grey field with a ">" chevron → rounded field, "This PC" root.
- Places panel → ~120 px wide with truncated labels, section headers in grey caps-less small text, Devices rows with a red/blue capacity line → 220 px panel, larger rows, drives shown as cards in the main view.
- Folder icons → Breeze saturated dark-blue folders with glyph overlays → lighter, softer folder icons as in the mockup.
- Status bar → "9 folders" in a tab-shaped chip at bottom-left → plain one-line status text with free-space info on the right.
- Selection → rectangle with a 1 px blue outline and pale fill around "Desktop" → rounded 8 px soft fill.

**`04` Alt+Tab**
- Switcher panel → light-grey box with square corners and no blur, selected item as a flat blue rectangle with a close "×" → rounded (16 px), blurred backdrop, larger thumbnails with the app icon below, and an accent ring on the selected item.

**`05` Russian session**
- Same wizard issues as `01`. The keyboard indicator is a plain lower-case "ru" text → small rounded badge "RU" as in the mockup.

## Reproduce

```sh
tools/vm/fetch.sh && tools/vm/run.sh --fresh   # then tools/vm/shot.sh, keys.sh, ssh.sh
```
