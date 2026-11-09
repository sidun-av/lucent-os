# Lucent Store: live check in the test VM (v4)

Real captures of the test VM (QEMU aarch64 on an Apple M4, software rendering,
2560x1440, 1x), slot B. Two images from CI were used:

- `vm` run 42668937173 (`def066d`): checklist items 1–10. The Store ran from
  this repo's `apps/lucent-store` (commit `001fc9f`, so with the one-row
  header of `../v4-chrome/`), started like the launcher starts it.
- `vm` run 42692475018 (image `7841365`), booted **fresh**: the first-boot
  window, `01`/`02` (Store from `2d0a404`, the fix below).

## Checklist

| # | Check | Result |
|---|---|---|
| 1 | `lucent-flatpak-setup` finished; `lucent-store.mo` (ru); Discover hidden | finished (`Result=success`, 2 min on first boot); `.mo` present. **Discover was not hidden**: its entry carries its own `NoDisplay=false` further down, which wins, so launcher search for "discover" listed it (`15-…`). Fixed in `83a1a65` (drop the old key first; same for System Settings) |
| 2 | Taskbar bag icon, launcher "Store", one entry when opened | bag icon pinned where Discover was; clicking it opens the Store and highlights that pin, no second entry |
| 3 | Home, light: cards, Installed, 7-Zip "Built in", beta 2×2, no QML errors | `03`: ONLYOFFICE, GIMP, Okular + PDF Arranger "Installed", Archives "Built in", beta 2×2; no Store QML warnings in `journalctl --user -b` |
| 4 | Dark switches live | `04` (Light → Dark with the Store open) |
| 5 | Search "photoshop" → GIMP first; "pdf" → PDF Arranger, verified, licence | `05`, `06` |
| 6 | Install Inkscape: "Installing NN %", Installed, no password for the wheel user; remove through the confirm dialog | `07` remove confirm, `08` "Installing… 75 %" with bar, `09` Installed + toast; `flatpak list --system` matched each step; no polkit prompt |
| 7 | GIMP page: screenshots, chips, "What it can access" | `10` |
| 8 | Updates count = `flatpak remote-ls --system --updates`; "Open Settings" | 0 = 0 (`11`); "Open Settings" opens Settings on Updates (`12`) |
| 9 | Beta: WordCraft → Try installs to `--user`, shows Open, downloads only 0.17.0 | `13`; processes during the install: one `curl` of `releases/download/v0.17.0/wordcraft-0.17.0-linux-aarch64.flatpak` (+ the release JSON), `flatpak install --user --bundle`; `flatpak list --user`: `ai.storyteller.wordcraft 0.17.0` |
| 10 | Russian session: labels, «Установленные» | `14` |

## First boot: "?" pins and "Install" on apps that come with Lucent

Both have the same cause. On the online path (disk image or `bootc switch`,
not the ISO, which brings the apps on the install media) `lucent-flatpak-setup`
downloads the 10 default apps **after** login; it took ~2 minutes here.

- Taskbar: the pinned Firefox, ONLYOFFICE, Okular and GIMP launchers don't
  exist until their Flatpak is installed, so the pins show "?". Each pin gets
  its icon as its app arrives, without logging out (`01` → `02`). Not a bug
  in the pins; it lasts as long as the download.
- Store: it read the installed list once at start, so a Store opened during
  the download kept offering **Install** for Okular + PDF Arranger, Kdenlive,
  ... after they had arrived (until it ran a job of its own). That was a real
  bug: fixed in `2d0a404`, the Store now watches the flatpak installations.
  `01` is the Store opened at 21:01:44 with no app yet, `02` the same window at
  21:03:47 after the setup finished, nothing clicked.

## Also fixed

- `001fc9f`: after searching, going to another section left the old query in
  the search field.
