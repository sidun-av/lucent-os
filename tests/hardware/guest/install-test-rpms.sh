#!/usr/bin/bash
# TEST-ONLY (hardware-live), as root in the test VM. Installs the test rig's
# packages (kernel-modules-internal for mac80211_hwsim, hostapd, dnsmasq,
# iw and whatever they need that the image lacks) into a TRANSIENT /usr
# overlay: gone at the next boot, never in any image.
#   install-test-rpms.sh DIR_WITH_RPMS
set -uo pipefail
dir=$1
if ! bootc usr-overlay 2>&1; then
    rpm-ostree usroverlay 2>&1 || { echo "no /usr overlay"; exit 1; }
fi
need=()
for r in "$dir"/*.rpm; do
    n=$(rpm -qp --nosignature --qf '%{NAME}' "$r" 2> /dev/null) || continue
    if [ "$n" = kernel-modules-internal ] || ! rpm -q "$n" > /dev/null 2>&1; then
        need+=("$r")
    fi
done
echo "installing into the transient /usr overlay: ${need[*]##*/}"
if ! rpm -i "${need[@]}"; then
    echo "rpm -i refused; retrying without signature check (koji build)"
    rpm -i --nosignature "${need[@]}" || rpm -i --nosignature --nodeps "${need[@]}" || exit 1
fi
depmod -a "$(uname -r)"
modinfo -n mac80211_hwsim
modinfo -F signer mac80211_hwsim
