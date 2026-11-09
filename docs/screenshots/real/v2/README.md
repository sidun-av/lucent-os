# Real Lucent OS, look v2: screenshots next to the mockups

Real captures of the image built by CI from `@COMMIT@` (the test-only
qcow2 from the `vm` workflow), booted **fresh** with
`LUCENT_VM_RES=2560x1440 tools/vm/run.sh --fresh`, the same size and scale
(1x) as `docs/mockups/*.png`. Software rendering (QEMU on an Apple M4,
llvmpipe), so blur and shadows are exactly what a GPU would draw, only slower.
Nothing was changed by hand after boot except opening the windows shown.

@TABLE@

## What the look is made of

| Part | Choice | Why |
| --- | --- | --- |
| Taskbar | One floating Plasma panel, Lucent Plasma theme (`desktoptheme/lucent*`), own search-field applet | Exactly the mockup's bar: 64 px, radius 20, 14/12 px gap, translucent + blur; active tile with accent bar, running dot. Stock Plasma panel, so it stays configurable. |
| Launcher | `org.lucent.launcher` (QML on Plasma's kicker backend) | Neither Kickoff nor Application Dashboard can be styled into `02-launcher`; the kicker backend keeps Plasma's app list, KRunner search and session actions. |
| Window frame | Aurorae v2 theme `Lucent` / `LucentDark` + KDE-Rounded-Corners | Aurorae v2 is KWin's native SVG decoration in 6.8 (no QML, fast). Klassy/Darkly have no maintained Fedora 45 builds for both arches; the rounded-corners effect does (author's COPR, built per KWin release). |
| Widgets | Breeze, driven by Lucent colour schemes from the mockup tokens, Inter 11 pt, frosted menus | Most Lucent apps are Flatpaks: they get Breeze from the KDE runtime but not a host Kvantum theme. One engine everywhere beats a prettier host-only one. |
| Icons | Lucent theme (the mockups' tiles and folders, 80 % safe area) over Papirus (Fedora package) | Papirus is maintained, GPL-3.0, flat, blue folders close to the mockups; Fluent/Colloid aren't packaged in Fedora. |
| Wallpaper | "Lucent Flow" rendered from the mockup SVG at 3840x2160 / 3840x2400, light + dark | Pixel-identical to the mockups; also on the lock and login screens. |
| Motion | 0.7x durations, scale for open/close, squash for minimise, fading popups; wobbly off | Quick and calm; no genie (macOS) or wobble. |

@GAPS@

Generators: `design/` (each script names its source in `docs/mockups/`).
Licenses: `THIRD_PARTY.md`. Reproduce: `tools/vm/fetch.sh &&
LUCENT_VM_RES=2560x1440 tools/vm/run.sh --fresh`.
