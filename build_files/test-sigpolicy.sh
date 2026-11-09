#!/usr/bin/bash
# CI test of the signature policy for updates, run as root inside the freshly
# built image (not part of it), with a throw-away registry on the host:
#   podman run --rm --network host -v ./build_files:/t:ro IMAGE /t/test-sigpolicy.sh localhost:5000
# The registry holds REGISTRY/lucent-sigtest:one and REGISTRY/other:one (tiny,
# unsigned). With an ephemeral key, this checks with the image's own
# containers/image and ostree-ext what installed systems will do once the
# image carries Lucent's key (build_files/container-policy.py):
#   - an update signed with the key is accepted;
#   - unsigned, or signed with another key: refused;
#   - other images still pull as before;
#   - ostree-ext (bootc/rpm-ostree's pull) accepts the policy for
#     `ostree-image-signed:` and refuses the unsigned image.
set -euo pipefail
reg=$1
repo=$reg/lucent-sigtest
step() { printf '\n== %s ==\n' "$*"; }
fail() { echo "FAIL: $*"; exit 1; }

# The local registry speaks plain HTTP.
mkdir -p /etc/containers/registries.conf.d
printf '[[registry]]\nlocation = "%s"\ninsecure = true\n' "$reg" > /etc/containers/registries.conf.d/50-sigtest.conf
printf 'docker:\n  %s:\n    use-sigstore-attachments: true\n' "$repo" > /etc/containers/registries.d/sigtest.yaml

step "sign the test image with an ephemeral key (skopeo, sigstore attachments)"
cd /tmp
printf 'test\n' > pass
skopeo generate-sigstore-key --output-prefix lucent --passphrase-file pass
skopeo generate-sigstore-key --output-prefix other --passphrase-file pass
skopeo copy --sign-by-sigstore-private-key lucent.private --sign-passphrase-file pass \
    "docker://$repo:one" "docker://$repo:signed"
skopeo copy --sign-by-sigstore-private-key other.private --sign-passphrase-file pass \
    "docker://$repo:one" "docker://$repo:wrongkey"

step "the policy, from this image's own policy.json"
base=/etc/containers/policy.json
[ -f "$base" ] || base=/usr/share/containers/policy.json
cp "$base" /tmp/base-policy.json
python3 -P /t/container-policy.py /tmp/base-policy.json --key /tmp/lucent.pub --scope "$repo" \
    --out /etc/containers/policy.json
cat /etc/containers/policy.json

pull() { skopeo copy "docker://$1" "dir:/tmp/out-$RANDOM" 2>&1; }

step "signed with the key: accepted"
pull "$repo:signed" || fail "a correctly signed image was refused"

step "unsigned: refused"
if out=$(pull "$repo:one"); then fail "an unsigned image was accepted"; fi
echo "$out" | tail -n 1
grep -qi 'signature' <<<"$out" || fail "refused, but not for its signature: $out"

step "signed with another key: refused"
if out=$(pull "$repo:wrongkey"); then fail "an image signed with another key was accepted"; fi
echo "$out" | tail -n 1

step "other images: as before"
pull "$reg/other:one" || fail "an unrelated image was refused"

step "ostree-ext (the update path of bootc and rpm-ostree)"
if ostree container --help >/dev/null 2>&1; then
    ostree --repo=/tmp/repo init --mode=bare-user
    # Unsigned: must be refused for its signature.
    if out=$(ostree container image pull /tmp/repo "ostree-image-signed:docker://$repo:one" 2>&1); then
        fail "ostree-ext pulled an unsigned image"
    fi
    echo "$out" | tail -n 2
    grep -qi 'signature' <<<"$out" || fail "ostree-ext refused the unsigned image, but not for its signature: $out"
    # Signed: gets past the signature check (it may then fail because the
    # test image is not a bootable ostree container, which is fine).
    out=$(ostree container image pull /tmp/repo "ostree-image-signed:docker://$repo:signed" 2>&1) || true
    echo "$out" | tail -n 2
    if grep -qiE 'signature was required|verification failed|invalid signature|insecureAcceptAnything' <<<"$out"; then
        fail "ostree-ext refused the signed image: $out"
    fi
    # And with a permissive default it would not even try.
    cp /tmp/base-policy.json /etc/containers/policy.json
    out=$(ostree container image pull /tmp/repo "ostree-image-signed:docker://$repo:signed" 2>&1) || true
    echo "$out" | tail -n 1
else
    echo "no 'ostree container' here; skipped"
fi

echo; echo "signature policy test passed"
