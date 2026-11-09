# Lucent OS: two 2026 concept directions

Two separate looks for "feels like 2026, macOS-like". Both keep the fixed product
decisions: one bottom taskbar (launcher, search, centered apps, tray and clock),
window buttons on the right, menus inside windows, English UI, no ads, no
recommendations, no AI. Every icon and wallpaper is drawn for these mockups.
The app tiles, line glyphs and file icons come from `../lucent.js`.

| | Prism (A) | Pebble (B) |
| --- | --- | --- |
| Desktop + Files, taskbar hover preview | `prism/01-desktop.png` | `pebble/01-desktop.png` |
| Full-screen launcher | `prism/02-launcher.png` (empty, focused search over all apps) | `pebble/02-launcher.png` (search "pdf": best match, apps, files, settings) |
| Settings → Appearance | `prism/03-settings.png` | `pebble/03-settings.png` |
| Desktop + Files, dark | `prism/04-desktop-dark.png` | `pebble/04-desktop-dark.png` |

All screens are 2560×1440 at scale 1, the owner's monitor. Body text is 14–16 px.
Each direction has its own stylesheet (`prism/prism.css`, `pebble/pebble.css`).
Shared pieces (wallpapers, folders, taskbar) are in `shell.js`. To re-render,
open each HTML file in Chromium at 2560×1440 with deviceScaleFactor 1 and take a
screenshot. The fonts load from Google Fonts.

## A: Prism (layered glass)

Prism is the version closest to the 2025–26 macOS material. Every surface is
glass: a backdrop blur with extra saturation, a light tint, and a 1 px specular
rim that is bright at the top left and fades around the edge. Depth comes from
light and soft shadows, not borders. The sidebar is an inset floating panel.
The header is one glass sheet: a quiet menu row, then floating capsule groups.
The taskbar floats 12 px off the screen edges. The wallpaper, "Drift", puts
saturated ribbons behind the glass so the glass has something to pick up.
Radii nest 20 → 14 → 10. Type is Inter, with Inter Tight for headings. The accent
is a blue-to-violet gradient that glows slightly on progress bars and switches.

## B: Pebble (soft depth)

Pebble is warmer and calmer. The surfaces are matte frost: about 90 % opaque, with
a fine grain. Depth comes from long soft shadows, raised "pillow" controls and
recessed wells: the sidebar, the search field, the taskbar app group and the
progress tracks. The shapes are rounded rectangles, not capsules (18 → 14 → 10).
The header is a single row: menus, navigation, path, view, search and window
buttons. The taskbar is a solid slab attached to the bottom edge. Drive usage is
shown as rings, and the status bar has an inline copy progress bar. The
wallpaper, "Clay Hills", is layered paper-cut hills with a sun or moon. Type is
Figtree. The accent is clay (terracotta), with eight earthy alternatives.

**How they differ in practice:** Prism needs translucency on every window to
look right. Pebble looks almost the same with no transparency at all, which
makes it cheaper and more robust.

## Plasma 6 feasibility, per signature element

Cost scale: **Stock**: KWin or Plasma can already do it, set by config or theme.
**Theme**: Lucent's Plasma theme SVGs, Kvantum or `lucent-style` work, the kind
Lucent already does. **Custom**: new C++, QML or shader code.

### Prism

| Element | Cost | Notes |
| --- | --- | --- |
| Blurred glass taskbar, popups, launcher, hover preview | Stock | KWin Blur is already on. Plasma theme SVGs set the tint and mask. |
| Saturation boost under glass | Stock (shell only) | KWin "Background contrast" (contrast, intensity, saturation) works only on Plasma surfaces that request it: panel, dialogs, launcher. It does **not** work behind app windows, and KWin Blur has no saturation setting. |
| Glass app windows (blurred, see-through) | Theme, fragile | Kvantum `translucent_windows` + `blurring` works for most Qt Widgets apps. GTK, Electron, Java and some Flatpak apps stay opaque, so the desktop looks mixed. The cost also rises with every window, and blur is slow on software rendering (the llvmpipe VM). The "Reduce transparency" switch on the Settings mockup is the escape hatch, and it needs a small custom setting page (KCM). |
| Specular rim (gradient 1 px ring) | Theme for the shell, Custom for app windows | Plasma theme SVGs can draw gradient strokes on the panel and dialogs. Around app windows, KDE-Rounded-Corners (already shipped) only draws flat-colour outlines. A gradient rim needs a fork of that effect or a new KWin effect. |
| True refraction or edge lensing ("liquid" distortion) | Custom, high | Needs a KWin GLSL effect that warps the backdrop near edges. The mockups deliberately **don't** show it. Recommendation: skip it. It costs a lot, it is unusable on llvmpipe, and it breaks on mixed toolkits. |
| 20 px window corners, concentric inner radii | Stock / Theme | KDE-Rounded-Corners radius 14 → 20. Inner radii come from the Kvantum SVGs and the Aurorae generator (`design/gen_aurorae.py`). |
| Menu row + window buttons in the titlebar area | Custom, medium | Regular window decorations can't show menu items. A decoration that renders the app menu inline (the way the third-party "Material" decoration does, via DBusMenu) covers Qt apps. GTK and Electron apps would keep their own menu bar. |
| Sidebar running up to the top window edge | Not possible with server-side titlebars | The titlebar always spans the full width above the app. A realistic version starts the inset sidebar under the titlebar row. The mockup layout is only fully possible with client-side decorations. |
| Inset floating sidebar, floating capsule toolbars | Theme | `lucent-style` (QProxyStyle) already redraws Dolphin's path bar and view toggles, so this is the same kind of work. |
| Floating taskbar | Stock | Plasma 6 panel "Floating" mode. |
| Glow on progress, switches and focus ring | Theme | Kvantum SVG elements. |

### Pebble

| Element | Cost | Notes |
| --- | --- | --- |
| Matte frosted surfaces (about 90 % opaque) | Stock / Theme | A light KWin Blur behind nearly opaque fills. It looks the same with blur off, so it degrades well on weak GPUs and llvmpipe, and with GTK or Electron apps. |
| Grain texture | Stock for the shell, Theme for windows | KWin Blur has a stock **Noise strength** setting for blurred shell surfaces. In app windows the grain is baked into the Kvantum window background SVG; watch repaint cost. |
| Recessed wells, raised "pillow" controls | Theme | Kvantum frame SVGs with inner shadows and top highlights. This is the kind of work Lucent already does. |
| Long soft window shadows | Stock / Theme | Decoration shadow size and strength (Aurorae SVG shadow or Breeze settings). |
| 18 px corners, rounded-rectangle controls | Stock / Theme | Same as today, with a different radius. |
| One-row header (menus + navigation + path + search + window buttons) | Custom, medium–high | Doing it literally needs client-side decorations or per-app patches. The cheap version: a titlebar with inline menus and window buttons, plus the toolbar directly below with the same colour and no separator. It reads almost the same. |
| Edge-attached taskbar with a recessed app well | Stock + Theme | A normal panel. The well around the apps is drawn by the Plasma theme or the task manager QML. |
| Drive rings, inline copy progress in the status bar | Custom | Dolphin has no drive cards (this is also true of today's mockups). The status-bar progress needs a Dolphin patch or a plugin. |
| Grouped launcher search (best match, apps, files, settings) | Custom QML | KRunner/Milou already returns these categories. The layout is new QML in the Lucent search plasmoid. |
| Accent swatches, Light/Dark/Auto, wallpaper day/night | Stock + KCM | Accent colours (including "from wallpaper"), look-and-feel switching and day/night wallpapers already exist in Plasma 6. A single Appearance page that combines them is a small custom KCM. |

## Main caveats

1. **Prism's look depends on transparent app windows, and the Linux app mix
   breaks that.** Qt apps can be glass; GTK, Electron and many Flatpak apps
   cannot, so they will sit next to Qt apps as opaque windows. Pebble hides this
   because its surfaces are almost opaque anyway.
2. **No true refraction.** Prism stops at blur, tint and a specular rim. A
   liquid-glass edge distortion would be a new KWin shader effect, and it would be
   unusable on software rendering.
3. **Unified headers are not free on KDE.** Both directions merge menus into the
   titlebar area. With server-side decorations the realistic version is a
   titlebar row with inline menus and buttons, plus a seamless toolbar row below
   it. Prism's full-height sidebar is only possible with client-side decorations.
4. **Performance:** Prism blurs every window, which is slow on old iGPUs and in
   the llvmpipe test VM. Pebble costs about what Lucent costs today.
