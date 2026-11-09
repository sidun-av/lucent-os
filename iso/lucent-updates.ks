# Lucent OS installer: signed updates (docs/updates.md).
# Merged into the ISO's kickstart by iso/make-config.py, which fills in the
# image reference the ISO was built from (LUCENT_IMAGE_REF).
#
# bootc-image-builder's own %post, earlier in the kickstart, points the new
# system at that image for its updates. If the image requires signatures for
# its own updates (its /etc/containers/policy.json has a rule for
# ghcr.io/sidun-av/lucent-os, see build_files/container-policy.py), the new
# system is switched to pull with signature checks (origin
# `ostree-image-signed:`): from then on an unsigned or wrongly signed update
# is refused. Without such a rule nothing changes. Never fails the install.
%post --interpreter=/usr/bin/bash --log=/tmp/lucent-updates.log
set -u
ref='@IMAGE_REF@'
case "$ref" in
    ''|@*) echo "lucent-updates: no image reference given; origin unchanged"; exit 0 ;;
esac
if python3 -c 'import json, sys
p = json.load(open("/etc/containers/policy.json"))
sys.exit(0 if "ghcr.io/sidun-av/lucent-os" in p.get("transports", {}).get("docker", {}) else 1)' 2>/dev/null; then
    if bootc switch --mutate-in-place --enforce-container-sigpolicy --transport registry "$ref"; then
        echo "lucent-updates: updates of $ref are signature-checked"
    else
        echo "lucent-updates: could not turn on signature checks for $ref; updates stay unchecked"
    fi
else
    echo "lucent-updates: the image has no signature policy for its updates yet; origin unchanged"
fi
exit 0
%end
