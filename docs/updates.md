# Updates: channels, signatures, background updates

How Lucent OS updates itself, and the interface the Settings → Updates page
(`apps/lucent-settings/lucent_settings/backends/updates.py`) works with.

In plain words: a new version of the whole system downloads in the
background, next to the running one, and starts at the next restart. The
previous version stays on disk, so going back is one step.

## Channels (image tags)

The image is `ghcr.io/sidun-av/lucent-os`, one multi-arch index for x86_64
and aarch64. `.github/workflows/build.yml` publishes:

| Tag | What | Who follows it |
|---|---|---|
| `:stable` | the latest release (`release.yml`, on a `vX.Y.Z` tag) | systems installed from a release ISO |
| `:X.Y.Z` | one release, never moves | nobody automatically (pin it with a switch, below) |
| `:testing` | every build of `main`, and the weekly rebuild | testers |
| `:latest` | the same image as `:testing` | older installs, test ISOs, the test VMs |
| `:<commit sha>` | one build of `main` | nobody automatically |

An installed system follows the tag its installer ISO was built from:
bootc-image-builder writes it into the system's origin. Release ISOs are
built from `:stable` (the release workflow checks that `:stable` is the
image of the release commit); manual test ISOs from `:latest` unless the
`iso` workflow is given another `image_tag`. The `iso` install test checks
the installed system's origin.

Every published index and each architecture's image is signed with
Sigstore, keyless: the certificate says it was made by
`https://github.com/sidun-av/lucent-os/.github/workflows/build.yml@refs/heads/main`
(testing) or `...@refs/tags/vX.Y.Z` (releases). Anyone can check:

```sh
cosign verify ghcr.io/sidun-av/lucent-os:stable \
  --certificate-identity-regexp '^https://github\.com/sidun-av/lucent-os/\.github/workflows/build\.yml@refs/(heads/main|tags/v.+)$' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
```

## Background updates (on by default)

- `/etc/rpm-ostreed.conf`: `[Daemon]` `AutomaticUpdatePolicy=stage`.
  rpm-ostree: *"The "stage" policy downloads and unpacks the update, queuing
  it for the next boot"* (`man rpm-ostreed.conf`).
- `rpm-ostreed-automatic.timer` is enabled (build and
  `10-lucent-updates.preset`): first run an hour after boot, then a day
  after the previous run ends (`OnBootSec=1h`, `OnUnitInactiveSec=1d`,
  `Persistent=true`). It runs
  `rpm-ostree upgrade --quiet --trigger-automatic-update-policy`.
- Nothing restarts the computer by itself. bootc's own
  `bootc-fetch-apply-updates.timer`, which runs `bootc upgrade --apply` and
  reboots, is disabled (and `disable` in the preset).

The image's smoke test checks all three, also after applying the first-boot
presets. Not yet checked on an installed system in this change: a staged
update arriving by the timer (CI has no long-running installed system).

## Signed updates

**Status: ready, waiting for a signing key (owner decision).**

Installed systems can't check the keyless signatures above:
containers/image (what bootc and rpm-ostree pull with) matches Fulcio
certificates only by `subjectEmail`, and a GitHub Actions certificate has a
URI, not an e-mail (see `containers-policy.json(5)`; support for workflow
identities is an open pull request upstream, containers/container-libs#625).
So installed systems check a second signature, made with a Lucent key:

1. The owner creates the key pair, the private half straight into the
   repository's secrets: `cosign generate-key-pair github://sidun-av/lucent-os`
   (creates `COSIGN_PRIVATE_KEY` and `COSIGN_PASSWORD`), and commits the
   public half as `system_files/etc/pki/containers/lucent-os.pub`.
2. From then on `build.yml` also signs every image with that key, with
   containers/image's own signer (`skopeo copy --sign-by-sigstore-private-key`,
   stored as sigstore attachments next to the image).
3. `build.sh` writes `/etc/containers/policy.json`
   (`build_files/container-policy.py`): `ghcr.io/sidun-av/lucent-os` needs a
   `sigstoreSigned` signature from `/etc/pki/containers/lucent-os.pub`
   (`signedIdentity: matchRepository`); the default becomes `reject`, which
   ostree-ext requires before it checks anything, with every transport's
   `""` scope keeping the old default, so all other images pull as before.
   `/etc/containers/registries.d/lucent-os.yaml` turns on
   `use-sigstore-attachments` (shipped already).
4. The installer switches the new system to pull with signature checks
   (`iso/lucent-updates.ks`:
   `bootc switch --mutate-in-place --enforce-container-sigpolicy`), so its
   origin becomes `ostree-image-signed:docker://ghcr.io/sidun-av/lucent-os:stable`.
   From then on an unsigned or wrongly signed update is refused.

`build_files/test-sigpolicy.sh` runs in every image build: with the
image's own skopeo and ostree-ext, an ephemeral key and a local registry, it
checks that a signed image is accepted and an unsigned or wrongly signed one
refused, and that other images still pull. Until step 1 is done, nothing
changes on installed systems: their origin stays
`ostree-unverified-registry:` and updates are not signature-checked.

Rotating the key later: ship the new public key next to the old one
(`keyPaths`) in an image signed with the old key, then switch signing.

## For Settings → Updates

Everything below works without root unless noted; changes go through
rpm-ostree's daemon and polkit, as Settings does now.

| Need | How |
|---|---|
| Versions on disk, which is booted, which is staged | `rpm-ostree status --json`: `deployments[]` with `booted`, `staged`, `version`, `timestamp`, `checksum`, `container-image-reference`, `container-image-reference-digest`. Same data on D-Bus: `org.projectatomic.rpmostree1`, `/org/projectatomic/rpmostree1/Sysroot`, property `Deployments`. |
| Channel followed | booted deployment's `container-image-reference`, e.g. `ostree-unverified-registry:ghcr.io/sidun-av/lucent-os:stable` → tag `stable` (text after the last `:` of the repository part). |
| Are updates signature-checked | the same field starts with `ostree-image-signed:` (e.g. `ostree-image-signed:docker://ghcr.io/sidun-av/lucent-os:stable`); `ostree-unverified-registry:` means not checked. `bootc status --json`: `.spec.image.signature` is `"containerPolicy"` (checked) or `"insecure"`. |
| Release version | `version` of the deployment: releases carry the label `org.opencontainers.image.version=X.Y.Z`; testing builds show the base image's version. Also `/usr/lib/os-release` `PRETTY_NAME`. |
| Is an update available | registry manifest digest for this CPU, `skopeo inspect --raw docker://ghcr.io/sidun-av/lucent-os:<tag>` → `manifests[]` with `platform.architecture` `amd64`/`arm64` → `digest`, compared with the deployments' `container-image-reference-digest` (what Settings does; `rpm-ostree upgrade --check` is unreliable for container images, coreos/rpm-ostree#1579). See the note on ISO installs below. |
| Download now and stage | `rpm-ostree upgrade` (D-Bus: `org.projectatomic.rpmostree1.OS.Upgrade` on the booted OS object), polkit `org.projectatomic.rpmostree1.upgrade`. |
| An update is waiting for a restart | a deployment with `"staged": true` (index 0, not booted). Show "Restart to finish updating". |
| Restart | Plasma's prompt: `org.kde.LogoutPrompt /LogoutPrompt org.kde.LogoutPrompt.promptReboot` (session bus), or `systemctl reboot`. |
| Go back to the previous version | `rpm-ostree rollback` (D-Bus `OS.Rollback`), then restart. |
| Automatic downloads on/off | read `/etc/rpm-ostreed.conf` `[Daemon] AutomaticUpdatePolicy` (`stage` = on, `none`/`check` = off; also D-Bus property `AutomaticUpdatePolicy` on `/org/projectatomic/rpmostree1/Sysroot`). Write: `pkexec /usr/libexec/lucent/settings-helper auto-updates on\|off` (writes the policy, `rpm-ostree reload`, enables/disables `rpm-ostreed-automatic.timer`). Default now: **on**. |
| When it last checked / next check | `systemctl show rpm-ostreed-automatic.timer -p LastTriggerUSec -p NextElapseUSecRealtime`; result of the last run: `systemctl show rpm-ostreed-automatic.service -p Result -p ExecMainExitTimestamp` (D-Bus: `org.freedesktop.systemd1` unit properties). |
| Switch channel (advanced) | `rpm-ostree rebase ostree-unverified-registry:ghcr.io/sidun-av/lucent-os:testing` (or `ostree-image-signed:docker://...` when signed), or `bootc switch [--enforce-container-sigpolicy] ghcr.io/sidun-av/lucent-os:testing`; polkit `org.projectatomic.rpmostree1.rebase` may ask for the admin password. Staged like an update; the previous version stays. |

### Note: the first update after installing from an ISO

ostree-container stores image layers under their compressed digest. The
ISO carries the system image recompressed (bootc-image-builder writes it
again from local storage, and the `iso` workflow recompresses it with zstd
to make the ISO smaller), so its digests are not the registry's: right
after an ISO install, the check above reports an update even when the
registry has the same build, and the first update downloads the image's
layers. The `iso` run summary shows how much ("First update after
installing ..."), measured for the layers as bootc-image-builder wrote them
and after zstd.
