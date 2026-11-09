# Pebble Drift assets: previews

The assets the Pebble Drift restyle ships, as they come out of the
repository. Target look: `docs/mockups/concepts-2026/pebble-drift/` (tokens
in `pebble-drift.css`). None of these is a capture of a running Lucent OS;
what each one is, and what still has to be checked in the VM, is listed per
file. Everything is at scale 1, the size it has on the owner's 2560x1440
monitor.

| File | What it is | Made with |
| --- | --- | --- |
| `01-wallpapers.jpg` | Drift (default), Tide and Aurora, day (`images/`) and night (`images_dark/`), scaled down from the shipped 2560x1440 files; under each, the sizes in the package | `design/preview-wallpapers.py` |
| `02-folder-icons.png` | Lucent's own folders, 16 to 128 px, light (`Lucent`) and dark (`Lucent-Dark`) on each mode's window surface, drawn by QtSvg (Plasma's SVG renderer) | `design/preview-icons.py` |
| `03-papirus-folders-indigo.png` | Papirus folders before and after `build_files/papirus-indigo.sh`: upstream blue, upstream indigo, indigo recoloured to the Drift folder tokens (what the image ships), next to Lucent's own. Rendered from upstream Papirus SVGs fetched from GitHub with the script run on them; the image build runs it on Fedora's Papirus and checks the result | one-off script; the build check is in `build_files/design.sh` |
| `04-app-tiles.png` | every app tile of the Lucent icon theme at 96 px (launcher) and 38 px (taskbar) on the light and dark window surface: the palette check. None clashes, so none was redrawn: the Pebble Drift mockups use these same tiles, and Lucent's own (Move from Windows, the start mark) are already blue-indigo | `design/preview-icons.py` |
| `05-boot-splash-simulated.jpg` | **simulated** Plymouth frame at 2560x1440: `background.png` scaled to the screen, the Lucent mark and one throbber frame placed at the theme's alignments, as two-step does. Not a boot capture | `design/preview-bootsplash.py` (throbber: plymouth's upstream `themes/spinner/throbber-0001.png`) |
| `06-wizard-*-{light,dark}.png`, `06-wizard-3/4-*-light-ru.png` | "Move from Windows", every page, light and dark, plus two pages in Russian: a real Qt window (macOS, `cocoa`), captured from the screen, 1180x780, against a fake Windows disk (copying and the summary are staged, nothing is copied) | `design/preview-wizard.py OUT [--dark] [--lang ru]` |

## What the wizard previews can't show

They were taken on a Mac, not on Plasma, so:

- the widget style underneath is Fusion, not Lucent's Kvantum-based
  `lucent` style; anything the style sheet doesn't cover (scrollbars at the
  edges, focus frames, the native window frame) can look different;
- macOS draws text heavier (CoreText) than Fedora's FreeType: Figtree
  Medium looks semibold here;
- Qt on macOS reports Figtree ExtraBold as weight 900, so the 800-weight
  page headings fall back to Bold here; on Fedora fontconfig calls it 800;
- the palette was set by the script (a plain light or dark one), not by
  Lucent Light / Lucent Dark;
- the title bar is KWin's on Lucent, and is not in the shots.

## Check in the VM (restyle-shell)

1. **Wallpaper default**: a fresh user gets Drift on the desktop
   (`plasma-org.kde.plasma.desktop-appletsrc` →
   `Image=file:///usr/share/wallpapers/Drift/`), the night version after
   switching to Lucent Dark (Plasma picks `images_dark/`), and the
   2560x1440 file on a 2560x1440 screen (`LUCENT_VM_RES=2560x1440`).
2. **Lock screen and login screen** show Drift night
   (`/usr/share/wallpapers/Drift/contents/images_dark/3840x2160.jpg`), blurred
   and dimmed, and the login splash (KSplash) the Drift day or night image.
3. **Boot splash**: the blurred Drift night `background.png` fills the whole
   screen (not tiled, i.e. `ScaleBackgroundImage` works in Fedora 45's
   Plymouth), the Lucent mark sits slightly above the middle, the spinner
   below it, and the handover to SDDM shows no colour jump. On a machine
   without Secure Boot, Plymouth may add its "Secure Boot disabled" emblem
   (copied from Fedora's spinner theme, as before).
4. **Folders** in Dolphin, icons view and details view, light and dark:
   Lucent's own folders at 32 px and up, Papirus's recoloured indigo below
   32 px and for Templates/Public; the build log shows
   `papirus-indigo: N names pointed at indigo, M indigo icons recoloured`
   and `Papirus 16x16/places/folder -> folder-indigo.svg`.
5. **Move from Windows** (autostarts with the fake Windows disk): every
   page in Lucent Light and Lucent Dark at 1x, on the real `lucent` style:
   - Figtree is used (`/usr/lib/lucent/lucent_settings/fonts`), headings
     in ExtraBold, body text Medium, nothing below 14 px;
   - the sidebar well, the raised current step, the list cards and the
     pillow buttons have visible edges in both modes;
   - checkboxes and radios: the check / dot in `--text-on-accent` (white on
     indigo light, dark on indigo dark), hover ring in the accent;
   - switching light/dark from Settings while it is open restyles it at once,
     and Settings → Text size resizes its text;
   - the hairline above the buttons is light, not black;
   - the summary page has only Finish;
   - Russian strings fit (sidebar, buttons).
