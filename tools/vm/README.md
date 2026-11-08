# tools/vm — boot the real Lucent OS image locally (QEMU, Apple Silicon)

**Test images only.** The `vm` workflow (`.github/workflows/vm.yml`) builds a
throw-away derivative of the published image (`tools/vm/image/`) and turns it
into a qcow2 with bootc-image-builder. It adds things a release must never
have: user `lucent` / password `lucent` with the SSH key
`image/lucent_vm_ed25519.pub`, sshd enabled, SDDM autologin. Locale and
keyboard are the release defaults (English, `us`).
It also ships `windows-disk.qcow2`, a 1 GB fake Windows disk (NTFS,
`Windows\System32`, profile `Users\Anna`) so the migration wizard has
something to find. The workflow runs after every successful `build` on main
(arm64) or manually (`gh workflow run vm -f arch=both`).

Needs: Homebrew `qemu`, `gh` (logged in), the private key
`~/.ssh/lucent_vm_ed25519` (ask the maintainer, or generate your own pair and
replace the `.pub`).

```sh
tools/vm/fetch.sh            # newest CI image -> ~/VMs/lucent/ (replaces the old one)
tools/vm/run.sh --fresh      # boot as on day one (drops the overlay); without --fresh: resume
tools/vm/ssh.sh              # shell as lucent;  ssh.sh --session qdbus6 ...  inside Plasma's env
tools/vm/shot.sh out.png     # QMP screendump
tools/vm/keys.sh meta        # Win key alone; also meta-e, alt-tab, alt-shift, esc, alt-f4
tools/vm/keys.sh --type 'text'
tools/vm/run.sh --stop       # ACPI power-down, then kill
```

The VM is aarch64 with HVF (`-cpu host`, 4 vCPU, 6 GB, 1920x1080
virtio-gpu, no virgl → KWin renders in software). VNC: `127.0.0.1:5901`
(macOS Screen Sharing: `open vnc://127.0.0.1:5901`). `run.sh` writes to an
overlay (`run-arm64.qcow2`) on top of the pristine CI image, so `--fresh`
always gives a true first boot. Settings live in `lib.sh` and can be
overridden with `LUCENT_VM_*` environment variables.
