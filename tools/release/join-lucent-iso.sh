#!/bin/sh
# Lucent OS: join the installer ISO downloaded in parts, and check it.
#
#   sh join-lucent-iso.sh [FOLDER]
#
# FOLDER (default: the folder this script is in) holds what you downloaded
# from the release page: lucent-os-<version>-<arch>.iso.001, .002, ... and
# SHA256SUMS. Works on macOS and Linux with the tools they come with.
#
# 1. If cosign is installed, checks that SHA256SUMS was signed by Lucent OS's
#    release workflow on GitHub (SHA256SUMS.sigstore.json).
# 2. Checks every part against SHA256SUMS and names the ones to download again.
# 3. Joins the parts and checks the finished ISO against SHA256SUMS.
# Nothing is deleted: the parts stay until you remove them.
set -u

IDENTITY_RE='^https://github\.com/sidun-av/lucent-os/\.github/workflows/release\.yml@refs/(tags/v.+|heads/main)$'
ISSUER='https://token.actions.githubusercontent.com'
GUIDE='https://github.com/sidun-av/lucent-os/blob/main/docs/install-usb.md'

partial=''
cleanup() { [ -n "$partial" ] && rm -f "$partial"; }
trap 'cleanup; exit 130' INT TERM HUP

say() { printf '%s\n' "$*"; }
fail() {
    cleanup
    printf '\nProblem: %s\n' "$1"
    shift
    for line in "$@"; do printf '%s\n' "$line"; done
    exit 1
}

# SHA-256 of standard input, as 64 lowercase hex digits.
sha256_stdin() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum | cut -c1-64
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 | cut -c1-64
    else
        openssl dgst -sha256 -r | cut -c1-64
    fi
}

file_size() { wc -c < "$1" | tr -d ' '; }

# "  - a" lines for a list of names.
bullets() { for x in "$@"; do printf '  - %s\n' "$x"; done; }

gb() { awk -v b="$1" 'BEGIN { printf "%.1f GB", b / 1e9 }'; }

if [ $# -ge 1 ]; then
    dir=$1
else
    dir=$(dirname "$0")
fi
cd "$dir" 2>/dev/null || fail "Cannot open the folder $dir."
dir=$(pwd)

say "Lucent OS installer: joining and checking the downloaded parts in"
say "  $dir"
say ""

[ -f SHA256SUMS ] || fail "SHA256SUMS is missing from this folder." \
    "Download SHA256SUMS from the same release page as the parts, put it next to them," \
    "and run this again."

# "hash name" pairs, lower-case hashes, without Windows line endings.
sums=$(tr -d '\r' < SHA256SUMS | sed -n 's/^\([0-9a-fA-F]\{64\}\) [ *]\(.*\)$/\1 \2/p' \
    | awk '{ print tolower($1), $2 }')
[ -n "$sums" ] || fail "SHA256SUMS is empty or damaged. Download it again from the release page."

expected() { printf '%s\n' "$sums" | awk -v n="$1" '$2 == n { print $1; exit }'; }
parts_of() { printf '%s\n' "$sums" | awk -v n="$1" '{ if (index($2, n ".") == 1 && substr($2, length(n) + 2) ~ /^[0-9][0-9][0-9]$/) print $2 }' | sort; }

# The ISOs whose parts (or finished file) are in this folder.
todo=''
for iso in $(printf '%s\n' "$sums" | awk '$2 ~ /\.iso$/ { print $2 }'); do
    here=''
    [ -f "$iso" ] && here=1
    for p in $(parts_of "$iso"); do [ -f "$p" ] && here=1; done
    [ -n "$here" ] && todo="$todo $iso"
done
[ -n "$todo" ] || fail "No ISO parts found in this folder." \
    "Put the downloaded files (lucent-os-...iso.001, .002, ...) in the same folder as" \
    "SHA256SUMS and this script, then run it again."

# 1. The signature of SHA256SUMS.
if [ -f SHA256SUMS.sigstore.json ]; then
    if command -v cosign >/dev/null 2>&1; then
        say "Checking the signature of SHA256SUMS with cosign..."
        if out=$(cosign verify-blob --bundle SHA256SUMS.sigstore.json \
            --certificate-identity-regexp "$IDENTITY_RE" \
            --certificate-oidc-issuer "$ISSUER" SHA256SUMS 2>&1); then
            say "Signature verified: SHA256SUMS was made by Lucent OS's release workflow on GitHub."
        else
            fail "The signature check failed: SHA256SUMS was not signed by Lucent OS's release workflow." \
                "cosign said: $(printf '%s\n' "$out" | tail -n 1)" \
                "Do not use these files. Download them again from" \
                "  https://github.com/sidun-av/lucent-os/releases" \
                "(The signature needs cosign 3 or newer; an older cosign can fail on it.)"
        fi
    else
        say "Note: the signature was not checked (cosign is not installed). The checksums"
        say "below still prove that every part arrived complete and undamaged."
    fi
else
    say "Note: SHA256SUMS.sigstore.json is not here, so the signature was not checked."
fi
say ""

for iso in $todo; do
    want=$(expected "$iso")
    parts=$(parts_of "$iso")
    n=$(printf '%s\n' "$parts" | grep -c .)

    if [ -f "$iso" ]; then
        say "Checking the finished $iso..."
        if [ "$(sha256_stdin < "$iso")" = "$want" ]; then
            say "$iso is already joined and checked."
            say ""
            continue
        fi
        say "The $iso here is incomplete or damaged; joining it again from the parts."
    fi

    missing=''
    for p in $parts; do [ -f "$p" ] || missing="$missing $p"; done
    # shellcheck disable=SC2086 # plain file names
    [ -z "$missing" ] || fail "Some parts of $iso are missing:" "$(bullets $missing)" \
        "Download them from the release page into this folder and run this again."

    need=0
    for p in $parts; do need=$((need + $(file_size "$p"))); done
    free=${LUCENT_TEST_FREE_BYTES:-$(df -Pk . | awk 'NR == 2 { print $4 * 1024 }')}
    if [ "$free" -lt "$need" ]; then
        fail "Not enough free space to join $iso: it needs $(gb "$need"), this drive has $(gb "$free") free." \
            "Free up some space, or move the parts to a bigger drive, and run this again."
    fi

    damaged=''
    i=0
    for p in $parts; do
        i=$((i + 1))
        say "Checking part $i of $n ($p)..."
        [ "$(sha256_stdin < "$p")" = "$(expected "$p")" ] || damaged="$damaged $p"
    done
    # shellcheck disable=SC2086 # plain file names
    [ -z "$damaged" ] || fail "Some parts of $iso are damaged (their checksum does not match SHA256SUMS):" \
        "$(bullets $damaged)" "Download them again from the release page, replace the old ones, and run this again."

    say "Joining $n parts into $iso..."
    partial="$iso.partial"
    rm -f "$partial"
    # shellcheck disable=SC2086 # $parts is a list of plain file names
    got=$(cat $parts | tee "$partial" | sha256_stdin)
    if [ "$(file_size "$partial")" != "$need" ]; then
        fail "Could not write $iso (is the drive full?)."
    fi
    if [ "$got" != "$want" ]; then
        fail "The joined $iso does not match SHA256SUMS, although every part did." \
            "SHA256SUMS may be from a different release: download it again and run this again."
    fi
    mv -f "$partial" "$iso"
    partial=''
    say "Ready: $dir/$iso ($(gb "$need")), checked against SHA256SUMS."
    say "You can delete the $n part files ($iso.001 ...) now."
    say ""
done

say "Next: write the ISO to a USB stick (16 GB or larger), see"
say "  $GUIDE"
