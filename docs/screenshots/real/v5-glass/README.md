# v5-glass: Glass Card dock and cards, real VM (2026-11-10)

aarch64 QEMU VM, 2560x1440 at 1x, KWin on OpenGL ES / llvmpipe (software; blur effect loaded).
Image: CI `vm` run 42728640086 (main 45009d5: dock + glass cards), fresh boot. The dock cell
size fix in the commit that adds this folder (50 px tiles, one-row tray, `iconSpacing` 0) was
applied live from `~/.local/share/plasma` before these shots, then plasmashell restarted.

| File | What |
| --- | --- |
| `desktop-light.png`, `desktop-dark.png` | the floating dock: start, search, pinned apps, separator, tray, clock |
| `dock-light.png`, `dock-dark.png` | the dock cropped at full size |
| `settings-light.png`, `settings-dark.png` | Settings → Appearance: glass sidebar card, accent-pill selection, cards, flat tracks; focused-app dash under Settings in the dock |

Compared with `docs/mockups/concepts-2026/glass/01-desktop-*` and `03-settings-*`. Known gaps:
the dock shows one dot/dash per app (not per window), the tray has no EN/battery items in
the VM, the "Light" mode tile in Settings did not follow a mode change made by
`lucent-theme` while the window was open. Not captured: the hover preview, Spotlight,
the Start menu, Store and Files (out of scope for this round).

Idle, no windows, 3 x 60 s each (`used` = MemTotal − MemAvailable):

| | used RAM | kwin_wayland PSS | plasmashell PSS | kwin CPU | plasmashell CPU |
| --- | --- | --- | --- | --- | --- |
| before (2d0a404) | 2092 MiB | 330 MiB | 463 MiB | 0.03–0.06 % | 0.06 % |
| after (45009d5 + cell fix) | 2212 MiB | 337 MiB | 512 MiB | 0.01–0.13 % | 0.05–0.08 % |

The runs are not like for like: "after" was measured after opening Settings, two theme
switches and two plasmashell restarts with a second copy of the Plasma theme and plasmoids
in `~/.local`; "before" only after closing the migration wizard. CPU is unchanged; the
+49 MiB plasmashell PSS needs a clean fresh-boot re-measure before it counts as a regression.
