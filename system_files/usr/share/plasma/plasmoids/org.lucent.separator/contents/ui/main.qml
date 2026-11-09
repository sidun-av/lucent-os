/*
    Lucent dock separator (glass.css .dk-sep): a 1 x 40 px --line-strong line
    with 8 px either side, between the running apps and the tray.

    SPDX-License-Identifier: Apache-2.0
*/
import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore

PlasmoidItem {
    id: root
    preferredRepresentation: fullRepresentation
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    readonly property bool dark: Kirigami.ColorUtils.brightnessForColor(Kirigami.Theme.backgroundColor) === Kirigami.ColorUtils.Dark
    readonly property bool vertical: Plasmoid.formFactor === PlasmaCore.Types.Vertical

    fullRepresentation: Item {
        Layout.minimumWidth: root.vertical ? -1 : 17
        Layout.maximumWidth: root.vertical ? -1 : 17
        Layout.minimumHeight: root.vertical ? 17 : -1
        Layout.maximumHeight: root.vertical ? 17 : -1
        Layout.fillHeight: !root.vertical
        Layout.fillWidth: root.vertical
        Rectangle {
            anchors.centerIn: parent
            width: root.vertical ? 40 : 1
            height: root.vertical ? 1 : 40
            color: root.dark ? Qt.rgba(220 / 255, 228 / 255, 1, 0.14) : Qt.rgba(40 / 255, 50 / 255, 110 / 255, 0.16)
        }
    }
}
