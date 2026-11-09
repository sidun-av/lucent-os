#!/usr/bin/bash
# Check an app bundle the way the installer uses it, in a clean Fedora
# container: verify, unpack into an empty /var/lib/flatpak, and make sure
# flatpak itself sees every default app, offline.
#   podman run --rm --network none -v .:/src:ro -v OUT:/out:ro IMAGE /src/iso/check-app-bundle.sh /out
# IMAGE should be the Lucent image itself (it has flatpak, zstd and tar).
set -euo pipefail
b=$1/lucent-apps
list=/src/system_files/usr/share/lucent/flatpaks.list
(cd "$b" && sha256sum --quiet -c SHA256SUMS)
rm -rf /var/lib/flatpak && mkdir -p /var/lib/flatpak
cat "$b"/flatpak.tar.zst.* | zstd -dc | tar -x --numeric-owner -C /var/lib/flatpak
flatpak remotes --system --show-details
fail=0
while read -r app; do
    if flatpak info --system "$app" >/dev/null; then
        echo "ok      $app"
    else
        echo "MISSING $app"; fail=1
    fi
done < <(grep -Ev '^\s*(#|$)' "$list")
# Every app's runtime must be there too, or it would not start offline.
for app in $(flatpak list --system --app --columns=application); do
    rt=$(flatpak info --system --show-runtime "$app")
    flatpak list --system --runtime --columns=ref | grep -qxF "$rt" \
        || { echo "MISSING runtime $rt of $app"; fail=1; }
done
exit $fail
