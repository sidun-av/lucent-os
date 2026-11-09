# Lucent OS: Pebble Drift (hybrid direction)

Pebble's materials and structure in Prism's colours. The owner picked Pebble
because it is cheap to run, but preferred Prism's cool palette. This direction
combines the two.

| Screen | File |
| --- | --- |
| Desktop + Files "This PC", light | `01-desktop.png` |
| Desktop + Files "This PC", dark | `02-desktop-dark.png` |
| Full-screen launcher (search "pdf"), light | `03-launcher.png` |
| Settings → Appearance, light | `04-settings.png` |
| Settings → Appearance, dark | `05-settings-dark.png` |

All screens are 2560×1440 at deviceScaleFactor 1. Body text is 15–16 px, and
nothing is smaller than 14 px. To re-render, open each HTML file in Chromium at
that size and take a screenshot once `body[data-ready]` is set. The Figtree font
loads from Google Fonts.

Files: `pebble-drift.css` holds the tokens (part 1) and the mockup components
(part 2). `drift-shell.js` holds the wallpapers, folders and taskbar. It is a
separate copy, so the shared `../shell.js` is unchanged. The app tiles, glyphs
and file icons come from `../../lucent.js`.

## What comes from where

**From Pebble (materials and structure):**
- matte frosted surfaces that are 93 % opaque, with a fine paper grain;
- long soft shadows;
- raised "pillow" controls and sunken wells: the sidebar, fields, segmented
  controls, progress tracks and the taskbar app group;
- rounded rectangles with nested radii 18 → 14 → 10 → 6, not capsules;
- a one-row window header;
- a taskbar attached to the bottom edge;
- ring drive gauges and inline copy progress in the status bar;
- the grouped launcher search;
- the Figtree typeface;
- all screen layouts.

**From Prism (colour):**
- the "Drift" wallpaper (day and night), with Pebble's grain added;
- an indigo-blue accent, used as a flat matte fill with no glow or gradient;
- cool neutral surfaces, text, lines and shadows, all tinted toward Drift's
  indigo (Pebble's were warm brown).

**New in this direction:**
- folders in the accent family, coloured through the `--folder-*` tokens;
- gauges that use `--gauge-1` (accent) for the system drive, `--gauge-2`
  (slate) for the read-only Windows drive and `--gauge-3` (violet) for the USB
  drive;
- eight cool accent swatches: Indigo, Azure, Lagoon, Violet, Orchid, Rose, Pine
  and Slate;
- two original wallpapers, both with day and night versions:
  - **Tide**: paper-cut swells in Drift's palette under a pale sun or moon.
    It is Pebble's shape in Prism's colours.
  - **Aurora**: three sweeping light curtains with vertical streaks.

The Settings page has a "Reduce motion" switch and a "Match wallpaper" accent
switch. It has no Glass or transparency section, because none is needed.

## Resource note

This direction costs the same as Pebble. Every surface is at least 92 %
opaque. The only blur is the optional `--surface-blur` (24 px, with no
saturation boost), and the design looks almost the same with it off. That
means it degrades cleanly on llvmpipe and weak iGPUs, and next to opaque GTK or
Electron apps. The grain is a static tile: the KWin Blur noise setting draws it
on shell surfaces, and the Kvantum background SVG draws it in app windows.
Drift is a static wallpaper with no cost at runtime. The Plasma feasibility
table for Pebble in `../README.md` applies here unchanged.

## Token summary

The full, commented list is in `pebble-drift.css`, part 1. Names follow the
pattern `--<group>-<role>[-<variant>]`.

| Group | Light | Dark |
| --- | --- | --- |
| `--accent` / `-hover` / `-pressed` | `#4257e8` / `#3549d6` / `#2c3dbb` | `#7088ff` / `#8297ff` / `#5f77f0` |
| `--accent-text` (accent as text) | `#3346cf` | `#9aabff` |
| `--accent-soft` (selection tint) | indigo 12 % | indigo 18 % |
| `--accent-2` (secondary violet) | `#7a55e0` | `#a084ff` |
| `--text-on-accent` | `#ffffff` | `#0e1230` |
| `--text-primary` / `-secondary` / `-tertiary` | `#171a2b` / `#474d66` / `#525972` | `#eef0fa` / `#bcc1d6` / `#9ca2bb` |
| `--surface-window` (matte frost) | `rgba(244,245,251,.93)` | `rgba(29,31,46,.93)` |
| `--surface-raised` → `-raised-2` (pillow gradient) | `#fdfdff` → `#f3f4fb` | `#33364d` → `#2c2f44` |
| `--surface-sunken` / `-strong` (wells) | indigo-grey 6.5 % / 11 % | black 20 % / 30 % |
| `--surface-selected` → `-2` | `#eef0ff` → `#e6e9fd` | `#343b6a` → `#2e345e` |
| `--surface-taskbar` / `-popover` / `-scrim` | 93 % / 96 % / 78 % | 93 % / 97 % / 84 % |
| `--line` / `-strong` / `-control` | indigo 10 % / 17 % / 30 % | white-blue 8 % / 14 % / 38 % |
| `--status-danger` / `-success` / `-warning` | `#cf3a48` / `#2f8a5c` / `#b7791f` | `#ef5f6b` / `#56c08a` / `#e3a547` |
| `--radius-window` / `-card` / `-control` / `-chip` | 18 / 14 / 10 / 6 px | same |
| `--shadow-window` | 1 px indigo ring, then 16 px and 50/110 px soft drops, tinted `rgba(25,35,90,…)` | the same shape in black |
| `--shadow-raised` / `-lift` / `-sunken` / `-popover` | pillow, hover lift, inset well, popover | same roles |
| `--highlight-top` | inset 1 px white 90 % | inset 1 px 8 % |
| `--focus-ring` | 2 px accent + 6 px `--accent-soft` | same |
| `--grain-image` / `-opacity` / `-blend` | cool fractal noise, 0.07, multiply | 0.09, screen |
| `--space-1 … --space-10` | 4, 8, 12, 16, 20, 24, 32, 40 px | same |
| `--type-display / title / heading / subhead / body / small / caption` | 32 / 22 / 19 / 17 / 15.5 / 14.5 / 14 px | same |
| `--folder-*`, `--gauge-*`, `--knob`, `--motion-*` | artwork and motion tokens that follow the palette | |

**Contrast (WCAG AA).** These ratios were checked against the window surface
composited over the most saturated part of Drift, and against the raised,
selected and strong-well surfaces:

| Text token | Light | Dark |
| --- | --- | --- |
| `--text-primary` | ≥ 12:1 | ≥ 10:1 |
| `--text-secondary` | ≥ 5.9:1 | ≥ 6.6:1 |
| `--text-tertiary` | ≥ 4.9:1 | ≥ 4.7:1 |
| `--accent-text` | ≥ 5.1:1 | ≥ 5.4:1 |

White text on the accent is 5.6:1 in light mode. Dark text on the accent is
5.8:1 in dark mode.
