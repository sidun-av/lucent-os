# Theming Lucent OS

Lucent's look is **Pebble Drift**: Pebble's matte, near-opaque materials in
Prism's cool blue-violet palette, light and dark
(`docs/mockups/concepts-2026/pebble-drift/`). This page explains where the
look comes from, how to change it, and the `lucent-theme` command that
switches light/dark and the accent colour.

## One source of truth

`docs/mockups/concepts-2026/pebble-drift/pebble-drift.css`, part 1, holds
every design token (`:root` for light, `.dark` for what dark mode
overrides). `design/tokens.py` reads it, resolving `var()` per mode, so the
generators never copy values by hand:

```python
import tokens
t = tokens.load()
t.light["surface-window-solid"]   # "#f2f3fa"
t.dark["accent"]                  # "#7088ff"
tokens.flatten(t.light["surface-sunken"], t.light["surface-window-solid"])  # alpha composited: "#e5e7f2"
tokens.shadows(t.light["shadow-raised"])  # [(dx, dy, blur, spread, colour), ...]
```

The accent swatches (Indigo, Azure, Lagoon, Violet, Orchid, Rose, Pine,
Slate) live in `system_files/usr/lib/lucent/lucent_theme/accents.py`,
tested against the Settings mockup. Indigo uses the tokens as they are
(light `#4257e8`, dark `#7088ff`); the other swatches use the same derived
shades as Lucent Settings (`Qt.lighter`/`Qt.darker`, reproduced exactly).

## Generators

Run them from the repository root after changing the tokens (Python 3 with
`numpy` and `pillow`); their output is committed.

| Generator | Output | What it draws |
| --- | --- | --- |
| `design/gen_colors.py` | `usr/share/color-schemes/Lucent{Light,Dark}.colors`, the `[Colors:*]` block of `etc/xdg/kdeglobals` | KDE colour schemes: window `--surface-window-solid`, header the same (one block with the title bar), view/buttons `--surface-raised`, selection `--accent` with `--text-on-accent` |
| `design/gen_kvantum.py` | `usr/share/Kvantum/Lucent*/` | Qt widget style: raised pillow buttons/combos/tabs, sunken wells for fields and segmented tracks, matte popover menus, `.card.sel` selection. One theme per accent (`Lucent` = Indigo, `LucentAzure` ... `LucentSlate`), each with its `…Dark` variant |
| `design/gen_aurorae.py` | `usr/share/aurorae/themes/Lucent{,Dark}/` | window frame: 48 px header in the window colour, 44 x 36 rounded buttons on the right, radius 18, `--shadow-window` |
| `design/gen_plasma_theme.py` | `usr/share/plasma/desktoptheme/lucent{,-dark}/` | taskbar (a 68 px slab attached to the bottom edge), popovers (`dialogs/background`: menus, OSD, notifications, calendar, tray), tooltips, task buttons, list highlights, text fields |

The design tests (`pytest design/tests`, also in CI) check the parser,
the accent maths, that the committed files are what the generators produce
now, and that every SVG piece stays inside its slice (QtSvg sizes an
element by its content, clip paths don't count).

Hand-written QML follows the same tokens, with the CSS variable named next
to each value: the launcher and taskbar search (`usr/share/plasma/plasmoids/org.lucent.*`),
Alt+Tab (`usr/share/kwin/tabbox/org.lucent.switcher`), the login screen
(`usr/share/sddm/themes/lucent`) and the lock screen
(`usr/share/lucent/design/lockscreen/LockScreenUi.qml`). Alt+Tab, login and
lock use Drift night (the `.dark` tokens and the Drift night wallpaper) in
both modes. KWin's rounded corners (`etc/xdg/kwinrc` `[Round-Corners]`)
use `--radius-window` (18 px).

## How the accent reaches everything

| Part | Mechanism |
| --- | --- |
| Colour scheme (Plasma, Kirigami apps, the launcher, Settings) | KDE's accent override: `plasma-apply-colorscheme --accent-color #hex`. Plasma 6 keeps no `AccentColor` key: it writes the colour into every set's `DecorationFocus` (exactly) and a tinted shade into `Colors:Selection`; `lucent-theme` reads `[Colors:Window] DecorationFocus` to know what is applied. Indigo is the schemes' own (`#4257e8` light, `#7088ff` dark), so choosing it re-applies the global theme |
| Plasma theme | everything drawn in the accent is a vector shape with `class="ColorScheme-Highlight"`, which Plasma recolours |
| Qt widget apps (Kvantum) | Kvantum's SVGs can't follow the palette, so each accent is a theme; `~/.config/Kvantum/kvantum.kvconfig` names it (`theme=LucentAzure`) and the widget style `lucent` / `lucent-dark` picks the light or dark variant |
| Flatpak Qt apps | `/usr/libexec/lucent/kvantum-flatpak-sync` copies the active theme into each app (`~/.var/app/<id>/config/Kvantum`) with `QT_STYLE_OVERRIDE=kvantum` set by `lucent-flatpak-setup` |
| Login, lock, Alt+Tab | Drift night with the default indigo (the login screen runs before any user's choice) |

## `lucent-theme`

```
lucent-theme apply [--mode light|dark|auto] [--accent NAME|#RRGGBB]
lucent-theme status [--json]
lucent-theme sync
lucent-theme font [--apply] [--json]
lucent-theme accents [--json]
```

- `apply` changes the mode, the accent, or both (at least one is
  required), live, without logging out:
  - `--mode light|dark`: `plasma-apply-lookandfeel -a org.lucent.desktop[.dark]`
    when it isn't already the current global theme (colour scheme, Plasma
    theme, widget style, window frame, icons), keeping the window-button
    layout the person chose; turns Plasma's automatic mode off.
  - `--mode auto`: Plasma's own automatic mode (`kdeglobals [KDE]
    AutomaticLookAndFeel=true`, Lucent light by day and dark by night).
  - `--accent`: a swatch id or name (case-insensitive), or any `#rrggbb`,
    which snaps to the nearest swatch. Sets KDE's accent (Indigo: removes
    the override and re-applies the global theme so its own colours come
    back), switches Kvantum to that accent's theme and tells running Qt
    apps to reload their style (`org.kde.KGlobalSettings.notifyChange`).
  - Always: Flatpak Qt apps are synced, and a desktop showing one image of
    a wallpaper package (`/usr/share/wallpapers/<name>/contents/images…`)
    is put back on the package, so Plasma shows its day or night image.
  - The choice is saved in `~/.config/lucent-themerc` (`[Theme] Mode=`,
    `Accent=`). If Lucent Settings' `~/.config/lucent-settingsrc` exists,
    its `[Appearance] Accent` is kept the same (`#rrggbb`, empty for Indigo),
    so Settings' own accent keeper never fights it.
- `status` prints what is chosen and what is showing; with `--json`:

  ```json
  {"mode": "dark", "effective_mode": "dark", "accent": "rose", "accent_name": "Rose",
   "accent_hex": "#cf4f86", "accent_from_wallpaper": false,
   "kvantum_theme": "LucentRose", "look_and_feel": "org.lucent.desktop.dark"}
  ```

  `mode` is the choice (`auto` stays `auto`), `effective_mode` what is on
  screen now.
- `sync` puts the chosen look back after something else changed
  `kdeglobals`: Plasma's automatic mode switching the global theme drops
  KDE's accent, so `sync` re-applies it; with Plasma's "accent from
  wallpaper" (or an accent set in System Settings and nothing chosen
  through Lucent), Kvantum follows the nearest swatch and the colours are
  left alone. It changes nothing when everything already matches, so it
  can't loop. The per-user `lucent-kvantum-sync.path` runs it whenever
  `kdeglobals` or the installed Flatpak apps change.
- `accents` lists the swatches (`--json`: `[{"id", "name", "hex"}, ...]`).

Exit codes: `0` done, `1` a step failed (each failure on stderr, the other
steps still ran), `2` bad arguments.

Examples:

```sh
lucent-theme apply --mode dark --accent azure
lucent-theme apply --accent "#40a070"      # -> pine
lucent-theme apply --mode auto
lucent-theme status --json
```

## The UI font

Pebble Drift's typeface is **Figtree** (`--font-sans`), installed once,
system-wide, in `/usr/share/fonts/figtree/` (SIL OFL, `OFL.txt` beside it).
It is the Plasma UI font (`/etc/xdg/kdeglobals`: Figtree Medium 11 pt =
14.7 px, the mockups' 15 px body at their weight 500; window titles
SemiBold), and Settings, the Store, the launch sheet and the "Move from
Windows" wizard use the same copy. Monospace stays JetBrains Mono.

Figtree has Latin only (Western and Central European; no Cyrillic, Greek or
Vietnamese). A Russian session in Figtree would draw Latin letters in
Figtree and Cyrillic ones in a fallback font, so **the UI font follows the
session's language**:

| Session | UI font |
| --- | --- |
| every language of the session covered by Figtree (English, German, French, Polish, ...) | Figtree |
| any other (Russian, Ukrainian, Greek, Vietnamese, Chinese, ...) | Inter |

- "Covered" is fontconfig's own answer (`fc-list Figtree:lang=ru`), not a
  list kept by hand. The session's languages are the UI language (first
  entry of `LANGUAGE`) and the formats' (`LC_TIME`, `LANG`: Russian formats
  put Cyrillic month names in the clock), from `~/.config/plasma-localerc`
  (what Settings → Language, KDE's Region & Language page, writes) and the
  environment.
- `lucent-theme font --apply` writes the five font keys of `kdeglobals`
  (`font`, `menuFont`, `toolBarFont`, `smallestReadableFont`, `[WM]
  activeFont`). It only touches keys that are Figtree or Inter: a font the
  person picked stays, and so does the size (Settings → Text size); only
  the family (and Figtree's 500 / Inter's 400 default weight) changes.
- It runs at every login before KWin and the shell start
  (`/etc/xdg/plasma-workspace/env/lucent-ui-font.sh`), and from
  `lucent-theme sync` when `plasma-localerc` changes
  (`lucent-kvantum-sync.path`): switching to Russian turns the UI to Inter at
  once; switching back to English keeps Inter until the next login, when the
  new language actually shows (the running session is still Russian).
- Lucent's own apps follow it: when the session's UI font is Inter they put
  Inter before Figtree, so a Russian session is Inter throughout.
- Text in another script inside a Figtree session (a Cyrillic file name)
  falls back to Inter first (`/etc/fonts/conf.d/60-lucent-fonts.conf`).
  Non-KDE apps that ask fontconfig for `sans-serif` get Inter, which covers
  every language the installer offers.

```
lucent-theme font [--apply] [--json]
{"family": "Figtree", "wanted": "Figtree", "languages": ["en"]}
```

## Limits

- Kvantum themes are per accent, so an arbitrary colour (e.g. Plasma's
  accent taken from the wallpaper) shows the nearest swatch in Qt widget
  apps while Plasma and Kirigami use the exact colour.
- In dark mode the scheme's selected text is `--text-on-accent` (`#0e1230`,
  dark, for the light dark-mode Indigo `#7088ff`). Plasma has one
  selected-text colour per scheme, so with a darker custom accent selected
  text in Kirigami lists stays dark (Settings uses white there).
- Flatpak apps on a KDE runtime with no Kvantum build on Flathub keep
  Breeze; GTK and Electron Flatpaks take the colour scheme through Plasma's
  GTK integration only.
