#!/bin/sh
# Print the draft release's notes (Markdown) for the assets in the current
# folder (SHA256SUMS and the ISO parts). Used by .github/workflows/release.yml.
#   release-notes.sh VERSION IMAGE_REF IMAGE_DIGEST DRY_RUN(true|false) IDENTITY_RE ISSUER
set -eu
version=$1 image_ref=$2 digest=$3 dry_run=$4 identity_re=$5 issuer=$6
repo=${GITHUB_REPOSITORY:-sidun-av/lucent-os}
server=${GITHUB_SERVER_URL:-https://github.com}

if [ "$dry_run" = true ]; then
    printf '> **Dry run** of the release workflow: do not publish this draft, delete it when done.\n\n'
fi
cat <<EOF
## Install Lucent OS $version

The installer is too big for a single GitHub download (8+ GB, because the
ten default apps are on it and install without internet), so each ISO comes
in parts of under 2 GB. Download **all the parts** of your ISO (\`amd64\` for
almost every PC, \`arm64\` for ARM laptops), \`SHA256SUMS\` and the join
script for your system into one folder:

- **Windows:** \`join-lucent-iso.cmd\` and \`join-lucent-iso.ps1\`, then
  double-click \`join-lucent-iso.cmd\`. It checks every part and joins them.
- **macOS, Linux:** \`join-lucent-iso.sh\`, then run \`sh join-lucent-iso.sh\`.

Then write the ISO to a USB stick of 16 GB or more:
$server/$repo/blob/main/docs/install-usb.md

| ISO | parts | size |
|---|---|---|
EOF
awk '$2 ~ /\.iso$/ { print $2 }' SHA256SUMS | while read -r iso; do
    n=$(awk -v p="$iso." 'index($2, p) == 1' SHA256SUMS | wc -l | tr -d ' ')
    bytes=$(cat "$iso".[0-9][0-9][0-9] | wc -c)
    # shellcheck disable=SC2016 # Markdown backticks, not a command
    printf '| `%s` | %s | %s |\n' "$iso" "$n" "$(awk -v b="$bytes" 'BEGIN { printf "%.2f GB", b / 1e9 }')"
done
cat <<EOF

## Check the download

The join scripts check every part, and the finished ISO, against
\`SHA256SUMS\`. \`SHA256SUMS\` itself is signed by this release's GitHub
Actions workflow (Sigstore, keyless): with
[cosign](https://docs.sigstore.dev/cosign/system_config/installation/)
installed the scripts check that too, or by hand:

\`\`\`
cosign verify-blob --bundle SHA256SUMS.sigstore.json \\
  --certificate-identity-regexp '$identity_re' \\
  --certificate-oidc-issuer $issuer SHA256SUMS
\`\`\`

## Updates

An installed system follows \`$image_ref\` (at this release the multi-arch
image \`sha256:$digest\`). New versions download in the background and start
at the next restart; the previous version stays one step away. See
$server/$repo/blob/main/docs/updates.md.

Built from ${GITHUB_SHA:-?} by $server/$repo/actions/runs/${GITHUB_RUN_ID:-?}.
EOF
