#!/usr/bin/bash
# "This PC" in Files (docs/this-pc.md): the kio_thispc worker behind
# thispc:/, its kded refresher, translations, and the checks. Called by
# build.sh after the Lucent Python packages are in /usr/lib/lucent; context
# at /ctx. Built against this image's KF6 and Qt, then the toolchain goes
# again (only what this step added; nothing of the base is removed).
#
# Only stable KF6 interfaces are used (KIO::WorkerBase, Solid, KRecentDocument,
# KDEDModule): Dolphin and Frameworks updates don't touch this build.
set -xeuo pipefail
src=/ctx/build_files/thispc
DNF=$(command -v dnf5 || command -v dnf)

rpm -qa --qf '%{NAME}\n' | sort > /tmp/before-thispc.txt
"$DNF" -y --setopt=install_weak_deps=False install gcc-c++ cmake make \
    qt6-qtbase-devel kf6-kio-devel kf6-solid-devel kf6-ki18n-devel kf6-kcoreaddons-devel kf6-kdbusaddons-devel
cmake -S "$src" -B /tmp/thispc -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr
cmake --build /tmp/thispc --parallel
# The logic's unit tests, here with Fedora's ICU collation (group order).
(cd /tmp/thispc && ctest --output-on-failure)
cmake --install /tmp/thispc
rpm -qa --qf '%{NAME}\n' | sort > /tmp/after-thispc.txt
mapfile -t added < <(comm -13 /tmp/before-thispc.txt /tmp/after-thispc.txt)
if ((${#added[@]})); then
    "$DNF" -y --setopt=clean_requirements_on_remove=False remove "${added[@]}"
fi
rm -rf /tmp/thispc /tmp/before-thispc.txt /tmp/after-thispc.txt

# Translations (the migration wizard's .mo writer; no gettext tools needed).
for po in "$src"/po/lucent-thispc.*.po; do
    lang=${po%.po}
    lang=${lang##*.}
    PYTHONPATH=/usr/lib/lucent python3 -P -c \
        'import sys; from pathlib import Path; from lucent_migrate.i18n import compile_po; compile_po(Path(sys.argv[1]), Path(sys.argv[2]))' \
        "$po" "/usr/share/locale/$lang/LC_MESSAGES/lucent-thispc.mo"
done

# inode/x-lucent-removable-drive (USB drives get "Eject" on the page).
update-mime-database /usr/share/mime

# Checks: the worker and the kded module load, KIO knows thispc:/, a
# removable drive is a kind of folder.
ls /usr/lib*/qt6/plugins/kf6/kio/thispc.so /usr/lib*/qt6/plugins/kf6/kded/thispcnotifier.so
QT_QPA_PLATFORM=offscreen python3 -P - <<'EOF'
from PySide6.QtCore import QMimeDatabase
m = QMimeDatabase().mimeTypeForName("inode/x-lucent-removable-drive")
assert m.isValid() and m.inherits("inode/directory"), m.name()
print("mime OK:", m.name(), m.comment())
EOF
# No session or udisks in a build container: the page still lists the
# system drive (measured at $HOME).
QT_QPA_PLATFORM=offscreen timeout 120 kioclient ls thispc:/ | tee /tmp/thispc-ls.txt
grep -qx 'drive-home' /tmp/thispc-ls.txt
rm -f /tmp/thispc-ls.txt
