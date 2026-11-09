#!/usr/bin/bash
# org.lucent.chrome (build_files/lucent-chrome): the one-row window header of
# Lucent's own apps (Settings, Store). A tiny QML module: KWin-drawn shadow
# (KWindowShadow), kwinrc's button order and double-click action (live), and
# the QML buttons / drag / resize pieces. Called by build.sh before the apps'
# own steps, whose --check / screenshot runs then load it. Built against this
# image's Qt and KF6, then the toolchain goes again (only what this step
# added; nothing of the base is removed).
#
# Never blocks an image: if it doesn't build or its test fails, the module
# isn't installed and both apps keep KWin's title bar (two rows), as they
# detect the module at start (lucent_settings/app.py, lucent_store/app.py).
set -xeuo pipefail
src=/ctx/build_files/lucent-chrome
DNF=$(command -v dnf5 || command -v dnf)

rpm -qa --qf '%{NAME}\n' | sort > /tmp/before-chrome.txt
"$DNF" -y --setopt=install_weak_deps=False install gcc-c++ cmake make \
    qt6-qtbase-devel qt6-qtdeclarative-devel kf6-kwindowsystem-devel kf6-kconfig-devel
qml=$(qtpaths6 --query QT_INSTALL_QML 2>/dev/null || echo /usr/lib64/qt6/qml)
if cmake -S "$src" -B /tmp/lucent-chrome -DCMAKE_BUILD_TYPE=Release -DQMLDIR="$qml/org/lucent/chrome" &&
   cmake --build /tmp/lucent-chrome --parallel &&
   (cd /tmp/lucent-chrome && QT_QPA_PLATFORM=offscreen ctest --output-on-failure) &&
   cmake --install /tmp/lucent-chrome; then
    ls "$qml/org/lucent/chrome/qmldir"
else
    echo "::warning title=Lucent window header::org.lucent.chrome did not build or its test failed; Settings and the Store keep KWin's title bar in this image (build_files/lucent-chrome.sh)"
    rm -rf "$qml/org/lucent/chrome"
fi
rpm -qa --qf '%{NAME}\n' | sort > /tmp/after-chrome.txt
mapfile -t added < <(comm -13 /tmp/before-chrome.txt /tmp/after-chrome.txt)
if ((${#added[@]})); then
    "$DNF" -y --setopt=clean_requirements_on_remove=False remove "${added[@]}"
fi
rm -rf /tmp/lucent-chrome /tmp/before-chrome.txt /tmp/after-chrome.txt
