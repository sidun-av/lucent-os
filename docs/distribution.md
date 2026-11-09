# Distributing the installer ISOs

The installer ISOs are large because the ten default apps (with their
runtimes, 8.3 GB installed) are on them, so a new system has them before its
first boot without a network. Measured in CI (November 2026):

| | amd64 | arm64 |
|---|---|---|
| ISO before this work | 8.29 GB | 8.4 GB |
| ISO now (zstd system image and app bundle, see [below](#making-the-iso-smaller)) | see the [iso run](#making-the-iso-smaller) | see the [iso run](#making-the-iso-smaller) |

GitHub release assets must each be [under 2 GiB](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)
("Each file included in a release must be under 2 GiB. There is no limit on
the total size of a release, nor bandwidth usage."), so a whole ISO can't be
one GitHub download.

## Recommendation

1. **Now, with nothing to sign up for: GitHub Releases, each ISO in parts.**
   This is what `.github/workflows/release.yml` does: parts of 1900 MiB,
   `SHA256SUMS`, its Sigstore signature, and join scripts that need nothing
   installed (Windows: double-click `join-lucent-iso.cmd`; macOS and Linux:
   `sh join-lucent-iso.sh`). Free, no bandwidth limit, the files are next to
   the source and the release notes. The cost is one extra step for the
   user, which the scripts make safe: they name a missing or damaged part
   and check the finished ISO. Every release is a **draft** until a
   maintainer publishes it.
2. **When a single-file download matters (it will, for people leaving
   Windows): Cloudflare R2 behind a Lucent domain**, as an extra mirror the
   release workflow uploads to. Storage is about $0.015 per GB-month with
   no charge for downloads at all, so two releases kept online cost well
   under a dollar a month however many people download them. Needs a
   Cloudflare account and a domain on it (the owner's decision, see
   [Accounts](#what-the-owner-would-have-to-create)).
3. **Optional: an Internet Archive item per release** as a free second
   mirror; the Archive makes a torrent with web seeds for it by itself.

Not recommended: SourceForge (ads on its download pages, against the spirit
of an OS without ads; per-file limits not documented), ghcr/ORAS as the
user-facing download (needs a command-line tool; fine as a developer
mirror), and self-hosting (home or small-server bandwidth can't carry
8-GB downloads).

## The options

| | One file for the user? | Cost | Account the owner must create | Notes |
|---|---|---|---|---|
| **GitHub release, multi-part** (implemented) | no: parts + join script | free | none | [under 2 GiB per asset, no total or bandwidth limit, up to 1000 assets](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases) |
| **ghcr.io OCI artifact (ORAS)** | yes, but only with the `oras` CLI | free for public packages | none | [10 GB per layer, 10-minute upload timeout](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry); a browser can't fetch a registry blob (it needs a token header) |
| **BitTorrent with web seeds** | yes, with a torrent client | free | none, if the web seed is a host we already have | web seeds ([BEP 19](https://www.bittorrent.org/beps/bep_0019.html)) need the *whole* file on an HTTP server, so a one-file torrent needs one of the hosts below; a torrent of the GitHub parts would still need joining. Torrent clients are not on a new Windows PC and are blocked on some networks |
| **Internet Archive** | yes | free | archive.org account | [1 TB per item, at most 1000 files / 500 GB recommended](https://help.archive.org/help/uploading-tips/); [torrents made automatically, Archive servers as web seeds](https://help.archive.org/help/archive-bittorrents/); download speed is not guaranteed |
| **SourceForge** | yes | free | SourceForge account, project | download pages carry ads; [Files docs](https://sourceforge.net/p/forge/documentation/Files/) give no size limit and recommend rsync over 100 MB; an undated [support reply](https://sourceforge.net/p/forge/feature-requests/844/) mentions 2.8 GB for rsync |
| **Cloudflare R2** | yes | [$0.015/GB-month, egress free; free tier 10 GB-month, 1M Class A, 10M Class B operations](https://developers.cloudflare.com/r2/pricing/) | Cloudflare account; a domain added to it | the free `r2.dev` URL is ["rate-limited and should only be used for development"](https://developers.cloudflare.com/r2/buckets/public-buckets/); production needs a custom domain (CDN cache). Third-party setup guides report a payment method is requested before the first bucket; Cloudflare's pricing page doesn't say |
| **Backblaze B2** | yes | [$6.95/TB-month, first 10 GB free; free egress up to 3x the stored data, then $0.01/GB](https://www.backblaze.com/cloud-storage/pricing) | Backblaze account | cheaper storage than R2, but downloads beyond 3x storage are billed: 1000 ISO downloads (8.4 TB) would be about $84 |

### Rough monthly cost, two releases online (both ISOs, ~33 GB)

| | storage | 1000 ISO downloads a month (~8.4 TB) |
|---|---|---|
| GitHub release | $0 | $0 |
| Cloudflare R2 | (33 − 10 free) GB x $0.015 = ~$0.35 | $0 egress; ~1000 GET requests, inside the free 10M Class B |
| Backblaze B2 | ~$0.16 | ~100 GB free (3x storage), the rest ~$83 |
| Internet Archive | $0 | $0 |

(Download managers split one download into many ranged requests; each is a
Class B operation on R2, still far inside the free 10 million.)

## What the owner would have to create

Nothing for the recommended first step: it uses this repository's releases
and its `GITHUB_TOKEN`.

For a single-file mirror on R2:

1. A Cloudflare account, with R2 enabled (a payment method may be asked for).
2. A domain on that account (or a subdomain via a partial CNAME setup), for
   example `download.<lucent domain>`, connected to the bucket.
3. An R2 API token limited to that bucket, stored as repository secrets
   (`R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_ENDPOINT`). The release
   workflow would then upload the whole ISOs (S3 multipart upload) next to
   the GitHub parts; the same `SHA256SUMS` covers both.

For an Internet Archive mirror: an archive.org account and its S3-style keys
as secrets; the `internetarchive` CLI can upload from the workflow.

None of these has been created, and nothing has been published: the release
workflow only makes drafts.

## Making the ISO smaller

Where the bytes are (amd64, before; from the `iso` run logs): the ISO from
bootc-image-builder is 5.81 GB, of which the system image (`/container`, 261
gzip layers) is about 4.6 GB and the installer environment
(`images/install.img`, squashfs zstd) 0.98 GB; the app bundle adds 2.48 GB.

Changed (safe: no content removed, every layer checked):

- **System image layers gzip → zstd -19** (`iso/zstd-oci.py`): each layer is
  decompressed, its content checked against the image config's `diff_id`,
  and compressed again with zstd -19 (window 2^27, which every zstd decoder
  accepts without extra memory). Only the compression changes; the
  installer's ostree-container reads zstd layers. The ISO is rebuilt by
  xorriso replaying the same boot records.
- **App bundle zstd -12 → -19, members sorted** (`iso/bundle-members.py`):
  the same file of two versions of a runtime (KDE 6.10 and 6.11, GNOME 50
  and 51, GL 25.08 and 26.08) sits side by side inside zstd's window.

Not changed, and why:

- **Firmware and the installer environment** (`install.img`): needed for
  real hardware; bootc-image-builder builds it and offers no compression
  setting.
- **Languages.** App translations in the bundle are already limited to
  English and Russian (`flatpak config languages 'en;ru'`). The system
  image keeps every language the installer offers (README: "Russian, and
  any other language the installer offers"); removing files in Lucent's own
  layer would not shrink the image anyway, because the base image's layers
  still carry them.
- **Deduplication against the base image**: files that Lucent's build
  replaces or deletes (removed packages, the rewritten RPM database) still
  sit in the base layers. Re-chunking the image (`rpm-ostree compose
  build-chunked-oci`) would drop them and also make updates smaller; it
  changes how every image is built, so it is a separate step for the image
  build, not done here.
