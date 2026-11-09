# Figtree UI font, English and Russian sessions: real screenshots

Real captures of the image built by CI from `e7817b4` (build run
[42682354588](https://github.com/sidun-av/lucent-os/actions/runs/42682354588),
test-only qcow2 from `vm` run
[42687488181](https://github.com/sidun-av/lucent-os/actions/runs/42687488181)),
booted fresh with `LUCENT_VM_RES=2560x1440 tools/vm/run.sh --fresh`
(aarch64, QEMU on an Apple M4, software rendering, 1x like the mockups).
The image has the Figtree change (`535ddc9`, `cd820a7`), the clock fix
(`afa4731`) and the Pebble Drift shell. These screenshots are about the
font; the shell's look is documented in `../v4-pebble-drift/`.

What was done by hand: four sample documents in `~/Documents` (one with a
Cyrillic name); Files, a notification (`notify-send`), the launcher (Win key)
and the Store opened. For the Russian session the language was changed the
way Settings → Language (KDE's Region & Language page) does it, by writing
`~/.config/plasma-localerc` (`[Translations] LANGUAGE=ru`, `[Formats]
LANG=ru_RU.UTF-8`), and then the session was logged out and back in through
the login screen.

| File | Session | What to look at |
| --- | --- | --- |
| `en-files.png` | English | Files: menus, sidebar, file names in Figtree Medium. The Cyrillic file name "Отчёт за октябрь.docx" is drawn in Inter, the fallback |
| `en-notification.png` | English | notification text in Figtree |
| `en-launcher.png` | English | launcher search, categories and app names in Figtree |
| `en-store.png` | English | the Store uses the system Figtree (no private copy) |
| `ru-files.png` | Russian | Files fully in Inter, including the Latin names "Family budget.xlsx" and "This PC"; no Figtree/Inter mix |
| `ru-notification.png` | Russian | notification and clock ("пн, нояб. 9") in Inter |
| `ru-launcher.png` | Russian | launcher in Inter |
| `ru-store.png` | Russian | the Store follows the session font: Inter for Cyrillic and Latin alike |
| `cmp-en.png`, `cmp-ru.png` | both | at 1:1, left the real Files sidebar, menus and clock, right the same parts of `docs/mockups/concepts-2026/pebble-drift/01-desktop.png` |
| `cmp-store.png` | both | at 1:1, the Store header in English (Figtree) over Russian (Inter) |

## Facts measured in the VM

| Check | English session | Russian session |
| --- | --- | --- |
| `lucent-theme font --json` | `{"family": "Figtree", "wanted": "Figtree", "languages": ["en"]}` | `{"family": "Inter", "wanted": "Inter", "languages": ["ru"]}` |
| Qt app font (KDE platform theme) | `Figtree,11,…,500` resolved to Figtree weight 500 | `Inter,11,…,400` resolved to Inter weight 400 |
| Qt draws "Documents" / "Документы" with | Figtree / Inter (fallback) | Inter / Inter |
| user `kdeglobals` font keys | none (the `/etc/xdg` default Figtree applies) | Inter, written at login by `lucent-ui-font.sh` |
| fontconfig | `fc-list Figtree:lang=ru` is empty; first fallback after Figtree is Inter; `sans-serif` is Inter; `monospace` is JetBrains Mono | same |
| Figtree files | `/usr/share/fonts/figtree/` (5 weights + `OFL.txt`); `/usr/lib/lucent/lucent_settings/fonts` is gone | same |

Live language switch: writing `plasma-localerc` in the running English
session changed `kdeglobals` to Inter within 6 seconds
(`lucent-kvantum-sync.path` runs `lucent-theme sync`, which runs the font
step). The UI itself turned Russian only after logging in again, as KDE
always does. Switching back to English keeps Inter until the next login,
deliberately: the running session still shows Russian text.

The image build checks the same on Fedora 45 (`build_files/design.sh`, run
42682354588 log): `fc-list 'Figtree:lang=en'` matches,
`fc-list 'Figtree:lang=ru'` does not, and the fallback after Figtree is
Inter.

## Compared with pebble-drift/01-desktop.png (at 1:1)

- Same typeface: the real Latin UI text is Figtree Medium, like the mockup's
  sidebar and menus.
- The real body text is 11 pt = 14.7 px; the mockup's rows are 15.5 px
  (`--type-body`). They look a little smaller.
- The clock: the mockup's time is 15.5 px at weight 650. The real one
  follows the session font now, but at `fontSize 11` it looks smaller, and
  the time looks regular rather than the 600 the layout script sets (both
  sessions). Not investigated further.
- Russian sessions are Inter by design (Figtree has no Cyrillic), so they
  differ from the mockup's letterforms on purpose.

## Open issues

1. Figtree has no italic files: italics are slanted by the renderer.
2. The lock screen (`LockScreenUi.qml`, `uiFont: "Inter"`) and the login
   screen (SDDM, `Font=Inter`) stay Inter in every language. They cover every
   language and don't mix, but they aren't Figtree in English.
3. "This PC" isn't translated in the Russian sidebar (the this-pc track's
   string).
4. A user who changes a font in KDE's own Fonts page keeps it:
   `lucent-theme font` only swaps keys that are Figtree or Inter.
