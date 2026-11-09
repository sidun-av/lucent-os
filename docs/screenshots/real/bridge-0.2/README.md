# Windows programs in Lucent's look (lucent-bridge 0.2)

Real screenshots from lucent-bridge's end-to-end test on x86-64,
[run 42683248645](https://github.com/sidun-av/lucent-bridge/actions/runs/42683248645)
(commit e4f8388; the v0.2.0 tag adds only documentation on top): the official
installers of Notepad++ 8.9.9, 7-Zip 26.06 and KeePass 2.62, installed and
started from their launcher entries with real Wine 11.20 in a Fedora 45
container with Lucent OS's Wine package set and Inter, no network. Xvfb at
1280x800 with no window manager, so there are no title bars; crops at 1:1.

Top to bottom in each image:

1. **Wine's own look**, what Lucent OS showed until now (the E2E pass with
   `LUCENT_BRIDGE_APPEARANCE=off`): Tahoma without anti-aliasing, Wine's
   grey-blue system colours.
2. **Light**: Pebble Drift light system colours (`--surface-window-solid`
   chrome, `--surface-raised` content, `--accent` selection), Wine's Aero
   visual style, Inter Medium 9 pt for menus/status/messages and Inter for
   dialogs, ClearType text.
3. **Dark**, after `~/.config/kdeglobals` changed to Lucent Dark's window
   colour, the way Plasma writes it: Pebble Drift dark colours, classic
   controls with softened bevels, brighter text gamma.
4. Notepad++ only: its own "Follow Windows" dark mode switched on, which
   reads the same Windows setting lucent-bridge writes. Notepad++ keeps
   Lucent's light colours otherwise (compat `colors = "light"`), because its
   light theme draws the active tab label in black over the system colours.
   Its menu bar stays light: Notepad++ paints a dark menu bar through
   undocumented `WM_UAHDRAWMENU` messages that Wine doesn't send.

| File | What |
| --- | --- |
| `notepadplusplus-classic-light-dark-own.png` | Notepad++: classic, light, dark, its own dark mode |
| `7-zip-classic-light-dark.png` | 7-Zip File Manager: classic, light, dark |
| `keepass-classic-light-dark.png` | KeePass's first-run dialog (.NET WinForms on Wine Mono): classic, light, dark |
| `notepadplusplus-144dpi.png` | Notepad++ after `Xft.dpi: 144` (Plasma at 150 %): LogPixels 144 |

The checks behind them (all PASS on x86-64 and AArch64 in that run):
dark mode followed at launch (7-Zip's registry: `AppsUseLightTheme=0`,
`Window="44 47 68"`); Notepad++ keeps light colours but hears dark mode;
Notepad++'s own dark mode follows Lucent's; LogPixels 144 from Xft.dpi 144;
"MS Shell Dlg" = Inter with Tahoma linked as fallback; Notepad++, 7-Zip and
KeePass not running as Administrator; D3D11 renders with DXVK 3.1.1 on
Xvfb's 0 Hz screen.

The same look in a real Plasma session (and the "Preparing Windows program"
sheet) is in `../x86-acceptance/`.
