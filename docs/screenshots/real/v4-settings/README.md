# Lucent Settings on a real boot (v4)

Real captures of **Lucent Settings** as installed in the image built by CI
from `def066d` (build run [42660774576](https://github.com/sidun-av/lucent-os/actions/runs/42660774576),
test-only qcow2 from `vm` run [42668937173](https://github.com/sidun-av/lucent-os/actions/runs/42668937173)),
booted **fresh** with `LUCENT_VM_RES=2560x1440 tools/vm/run.sh --fresh`
(aarch64, QEMU on an Apple M4, software rendering), at 1x like the mockups.
The app was started the way the launcher starts it (`/usr/bin/lucent-settings`
in a unit of the user's systemd manager); nothing in it was patched.

Target design: `docs/mockups/concepts-2026/pebble-drift/04-settings.png` and
`05-settings-dark.png` (the owner's "Pebble Drift" direction; every value is a
token in `apps/lucent-settings/lucent_settings/qml/Lucent/Theme.qml`).

| File | Section |
| --- | --- |
| `01-network.png` | Network & internet (wired only in a VM) |
| `02-bluetooth.png` | Bluetooth & devices: no adapter in a VM |
| `03-display.png` | Display: resolution, scale, night light |
| `04-sound.png` | Sound: PipeWire's dummy sink (no audio hardware in a VM) |
| `05-appearance-light.png`, `05-appearance-dark.png` | Appearance (compare with `04-settings.png`, `05-settings-dark.png`) |
| `06-wallpaper.png` | Wallpaper: Drift, Tide, Aurora (day and night), the system's, yours |
| `07-like-windows.png` | Like Windows: window buttons, Win-key shortcuts, double-click |
| `08-keyboard-language.png` | Keyboard & language |
| `09-windows-apps.png` | Windows apps on a fresh system (none yet; with Notepad++ installed it lists icon, size, "Works", "made for Intel/AMD, translated") |
| `10-updates-available.png`, `10-updates-light.png`, `10-updates-dark.png` | Updates: a newer CI image found, then downloaded and waiting for a restart |
| `11-users.png` | Users |
| `12-about.png` | About this PC |

## Done by hand on the fresh boot

- The first-run "Move from Windows" wizard closed; the pointer moved off the window for each shot.
- In Settings itself: the Drift wallpaper picked on Appearance; the name "Anna Smirnova" and the initials
  picture set on Users; Dark picked on Appearance for the dark shots.
- For the update shots the test image's origin (`localhost/lucent-vmtest`, which no registry serves)
  was pointed at `ghcr.io/sidun-av/lucent-os:latest-arm64` with `sudo`; then Check and Download were
  clicked in Settings.

## Proven in the VM (actions, not just screens)

Each action below was clicked in the app (QMP pointer/keyboard), and its
effect checked from outside the app (config files, D-Bus, the tools). Rows
marked **fresh** were repeated on the fresh boot above with the app as
installed in the CI image; the others were run earlier on the previous CI
image with the same code copied in.

| Section | Action | Checked with |
| --- | --- | --- |
| Appearance | **fresh**: Light → Dark; earlier also Auto; the whole desktop and Settings itself switch live | `LookAndFeelPackage` / `AutomaticLookAndFeel` in kdeglobals |
| Appearance | a pink accent, then back to the theme's own; "Match wallpaper" on (Plasma picks 123,146,246 from Drift) and off | kdeglobals `[Colors:Selection]`, `AccentColor`, `accentColorFromWallpaper` |
| Appearance / Wallpaper | **fresh**: pick Drift (day/night follows the mode); earlier Altai and Lucent | `plasma-org.kde.plasma.desktop-appletsrc` `Image=` |
| Appearance | animations off and back, text size | `AnimationDurationFactor` |
| Display | **fresh**: scale 125 %; earlier back to 100 % in the app; resolution 1920×1080 with the 15 s "Keep / Go back" banner reverting by itself; night light on/off | `kscreen-doctor -o`, KWin NightLight D-Bus `enabled` |
| Sound | **fresh**: drag volume to 48 %; earlier mute and unmute | `wpctl get-volume @DEFAULT_AUDIO_SINK@` |
| Network | **fresh**: Disconnect the wired NIC (SSH into the VM dropped), Connect again (SSH back) | `nmcli device` |
| Like Windows | window buttons left (KWin moved them live) and right; double-click off/on; layout switch Win+Space only / Alt+Shift | kwinrc `ButtonsOnLeft/Right`, kdeglobals `SingleClick`, kxkbrc `Options` |
| Users | **fresh**: name "Anna Smirnova" and the initials picture; earlier the password was changed through the polkit prompt, and the login screen showed the name after a reboot | AccountsService `RealName`, `IconFile` (the PNG), `/etc/shadow` changed and `sudo` accepts the password |
| Updates | **fresh**: Check found a newer CI image on ghcr, Download staged it (polkit, no prompt for the admin). Earlier: Restart now (Plasma's confirm) booted it; the **installed** Settings there showed "Previous version", Roll back + confirm, Restart booted the old one | `rpm-ostree status`, `skopeo inspect`, journal of rpm-ostreed |
| Windows apps | Notepad++ installed with `lucent-bridge run --silent`: listed with its icon, size, "Works", "made for Intel/AMD, translated" | `lucent-bridge list/plan --json` |
| About this PC | **fresh**: "Advanced settings…" opens KDE System Settings | `pgrep systemsettings` |
| Launcher, taskbar | **fresh**: the taskbar's pinned gear opens Lucent Settings; earlier, typing "settings" in the launcher offered it first and no longer KDE System Settings | process list, screenshot |


## Not possible in this VM

- **Wi-Fi**: QEMU's virtual NIC is wired; the Wi-Fi list, joining with a
  password and the Wi-Fi switch are covered by unit tests against `nmcli`'s
  documented terse output (escaped `:` and `\`, hidden networks).
- **Bluetooth**: no adapter (BlueZ doesn't start); the page shows its
  "No Bluetooth adapter found" state. Pairing, connecting and forgetting are
  covered by tests of the BlueZ D-Bus calls.
- **Sound hardware**: PipeWire has only its dummy sink, shown as "No sound
  device"; volume and mute were changed on it for real.
- **Battery**: none in the VM (Settings has no battery page).
- **Night light colours**: KWin's night light switched on and off (D-Bus
  state), but a VM screen grab doesn't show the gamma change.

## Still different from the mockups, and why

1. **Header row.** The mockup draws one 64 px row with the title, back /
   forward, search and the window buttons. Lucent windows keep KWin's title
   bar (server-side decorations), so Settings has its own row under it with
   back / forward and the centred search. Merging the two needs client-side
   decorations or the desktop restyle's title bar.
2. **Sidebar sections.** The mockup's Taskbar, Apps and Privacy & security
   sections have no page yet (no backend was written for them); Settings has
   Like Windows, Keyboard & language and Windows apps instead, which the task
   asked for.
3. **Comfort.** "Density", "Soft shadows" and "Accent on title bars" are not
   offered: Plasma has no setting behind them for Lucent's current theme, and
   a switch that does nothing would be dishonest. "Reduce motion" turns window
   animations off.
4. **Window translucency.** The mockup's window is 93 % opaque over the
   wallpaper; Settings draws an opaque surface (the design says it should look
   the same with translucency off).
5. Body text is 15 px, not 15.5 px (Qt sizes text in whole pixels).
