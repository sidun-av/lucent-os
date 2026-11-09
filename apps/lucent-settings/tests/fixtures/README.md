# Test fixtures

Captured on the Lucent OS test VM (aarch64, Fedora 45 base, image from CI
`vm` run 42631597857), with the command in parentheses:

- `nmcli-device.txt` (`nmcli -t -f DEVICE,TYPE,STATE,CONNECTION device`), `nmcli-general.txt`
  (`nmcli -t -f WIFI-HW,WIFI,NETWORKING general`): wired only, no Wi-Fi hardware.
- `wpctl-status.txt`, `pactl-sinks.json`, `pactl-sources.json` (`pactl -f json list sinks|sources`):
  the VM's PipeWire with no audio hardware (Dummy Output).
- `kscreen.json` (`kscreen-doctor -j`): virtio-gpu output Virtual-1.
- `accounts-user.txt` (`busctl --json=short get-property ... org.freedesktop.Accounts.User
  UserName RealName IconFile AccountType`).
- `rpm-ostree-booted.json` (`rpm-ostree status --json`, trimmed to the keys used).
- `bridge-list.json`, `bridge-app.desktop`, `bridge-plan.json` (`lucent-bridge list --json`,
  the launcher entry it wrote, `lucent-bridge plan --json --assume-tools <exe>`) after a real
  silent install of Notepad++ 8.8.9 through lucent-bridge in the VM.
- `lscpu.json`, `meminfo.txt`, `os-release.txt`.

Constructed (a VM can't produce them), in the tools' documented formats:

- `nmcli-wifi-list.txt`, `nmcli-device-wifi.txt`, `nmcli-connections.txt`, `nmcli-general-wifi.txt`:
  a laptop with Wi-Fi; includes escaped `:` and `\` and a hidden network.
- `bluez-objects.json`: BlueZ `GetManagedObjects` as busctl prints it (the VM has no adapter).
- `rpm-ostree-staged.json`: the booted deployment plus a staged update and a rollback
  deployment, same keys as the captured one.
- `pactl-sinks-laptop.json`: two real-looking sinks (speakers, HDMI) for device choice.
- `skopeo-index.json`, `skopeo-arm64-manifest.json` (`skopeo inspect --raw docker://ghcr.io/sidun-av/lucent-os:latest`
  and `:latest-arm64`, build 5e52d69): what the update check compares with the deployment's digest.
