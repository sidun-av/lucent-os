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
# Never block an image (and the updates in it) on This PC: if it doesn't
# build or its tests fail, Files opens on Home as stock Dolphin does, the
# sidebar entry isn't added (design-defaults checks for the worker), and CI
# shows a warning on the run.
if cmake -S "$src" -B /tmp/thispc -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr &&
   cmake --build /tmp/thispc --parallel &&
   (cd /tmp/thispc && ctest --output-on-failure) &&   # with Fedora's ICU collation (group order)
   cmake --install /tmp/thispc; then
    thispc=1
else
    thispc=0
    echo "::warning title=This PC::kio_thispc did not build or its tests failed; this image's Files opens on Home (see the build log, build_files/thispc.sh)"
    sed -i '/^HomeUrl=thispc:/d' /etc/xdg/dolphinrc
fi
rpm -qa --qf '%{NAME}\n' | sort > /tmp/after-thispc.txt
mapfile -t added < <(comm -13 /tmp/before-thispc.txt /tmp/after-thispc.txt)
if ((${#added[@]})); then
    "$DNF" -y --setopt=clean_requirements_on_remove=False remove "${added[@]}"
fi
rm -rf /tmp/thispc /tmp/before-thispc.txt /tmp/after-thispc.txt

# inode/x-lucent-removable-drive (USB drives get "Eject" on the page).
update-mime-database /usr/share/mime
((thispc)) || exit 0

# Translations (the migration wizard's .mo writer; no gettext tools needed).
for po in "$src"/po/lucent-thispc.*.po; do
    lang=${po%.po}
    lang=${lang##*.}
    PYTHONPATH=/usr/lib/lucent python3 -P -c \
        'import sys; from pathlib import Path; from lucent_migrate.i18n import compile_po; compile_po(Path(sys.argv[1]), Path(sys.argv[2]))' \
        "$po" "/usr/share/locale/$lang/LC_MESSAGES/lucent-thispc.mo"
done

# Checks: the worker and the kded module are installed, a removable drive is
# a kind of folder, and KIO really lists thispc:/ (no session or udisks in a
# build container: the page still has the system drive, measured at $HOME).
check() {
    ls /usr/lib*/qt6/plugins/kf6/kio/thispc.so /usr/lib*/qt6/plugins/kf6/kded/thispcnotifier.so &&
    QT_QPA_PLATFORM=offscreen python3 -P -c '
from PySide6.QtCore import QMimeDatabase
m = QMimeDatabase().mimeTypeForName("inode/x-lucent-removable-drive")
assert m.isValid() and m.inherits("inode/directory"), m.name()
print("mime OK:", m.name(), m.comment())' &&
    QT_QPA_PLATFORM=offscreen timeout 120 kioclient ls thispc:/ | tee /tmp/thispc-ls.txt &&
    grep -qx 'drive-home' /tmp/thispc-ls.txt
}
if ! check; then
    echo "::warning title=This PC::kio_thispc built but does not list thispc:/; this image's Files opens on Home (build_files/thispc.sh)"
    sed -i '/^HomeUrl=thispc:/d' /etc/xdg/dolphinrc
    rm -f /usr/lib*/qt6/plugins/kf6/kio/thispc.so
fi
rm -f /tmp/thispc-ls.txt
