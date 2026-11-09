/*
    Lucent dock search button (glass.css .dk with the search glyph): a 56 px
    tile, --state-hover on hover. Clicking it opens KRunner (Spotlight, the
    same as Win+Space); typing while it has focus does the same.

    SPDX-License-Identifier: Apache-2.0
*/
import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasma5support as P5Support

PlasmoidItem {
    id: root

    preferredRepresentation: fullRepresentation
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground

    readonly property bool dark: Kirigami.ColorUtils.brightnessForColor(Kirigami.Theme.backgroundColor) === Kirigami.ColorUtils.Dark
    readonly property color text1: dark ? "#eef0fa" : "#171a2b"   // --text-primary

    P5Support.DataSource {
        id: exec
        engine: "executable"
        connectedSources: []
        onNewData: (source) => disconnectSource(source)
    }

    function openLauncher() {
        exec.connectSource("dbus-send --session --type=method_call --dest=org.kde.krunner /App org.kde.krunner.App.display")
    }

    fullRepresentation: MouseArea {
        id: field
        Layout.minimumWidth: 56
        Layout.preferredWidth: 56
        Layout.maximumWidth: 56
        Layout.fillHeight: true
        hoverEnabled: true
        activeFocusOnTab: true
        Accessible.role: Accessible.Button
        Accessible.name: i18n("Search")
        onClicked: root.openLauncher()
        Keys.onPressed: (event) => { if (event.text.length > 0 || event.key === Qt.Key_Return) root.openLauncher() }

        Rectangle {     // .dk.hover: --state-hover, radius 14, no shadow
            anchors.centerIn: parent
            width: 56
            height: 56
            radius: 14
            color: root.dark ? Qt.rgba(220 / 255, 228 / 255, 1, field.pressed ? 0.11 : 0.07)
                             : Qt.rgba(48 / 255, 58 / 255, 120 / 255, field.pressed ? 0.10 : 0.06)
            opacity: field.containsMouse || field.activeFocus ? 1 : 0
            Behavior on opacity { NumberAnimation { duration: Kirigami.Units.shortDuration } }
        }
        Kirigami.Icon {
            anchors.centerIn: parent
            width: 24
            height: 24
            source: "search-symbolic"
            color: root.text1
            isMask: true
        }
    }
}
