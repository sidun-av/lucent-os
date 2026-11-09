/*
    Lucent taskbar search field (pebble-drift.css .tb-search): a 300 x 44
    sunken well (--surface-sunken, --shadow-sunken), radius 12. Clicking it,
    or typing while it has focus, opens the launcher (the panel applet that provides org.kde.plasma.launchermenu) with
    its search field focused, like the search box on the Windows taskbar.

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
    readonly property color text2: dark ? "#bcc1d6" : "#474d66"

    P5Support.DataSource {
        id: exec
        engine: "executable"
        connectedSources: []
        onNewData: (source) => disconnectSource(source)
    }

    function openLauncher() {
        // Same entry point as the Win key (kwinrc [ModifierOnlyShortcuts]).
        exec.connectSource("dbus-send --session --type=method_call --dest=org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.activateLauncherMenu")
    }

    fullRepresentation: MouseArea {
        id: field
        Layout.minimumWidth: Kirigami.Units.gridUnit * 16
        Layout.preferredWidth: 300
        Layout.maximumWidth: 300
        Layout.fillHeight: true
        hoverEnabled: true
        activeFocusOnTab: true
        Accessible.role: Accessible.Button
        Accessible.name: i18n("Search")
        onClicked: root.openLauncher()
        Keys.onPressed: (event) => { if (event.text.length > 0 || event.key === Qt.Key_Return) root.openLauncher() }

        Rectangle {
            anchors.verticalCenter: parent.verticalCenter
            width: parent.width
            height: 44
            radius: 12
            // --surface-sunken, a touch deeper on hover (--surface-sunken-strong)
            color: root.dark ? Qt.rgba(0, 0, 10 / 255, field.containsMouse ? 0.30 : 0.20)
                             : Qt.rgba(48 / 255, 58 / 255, 120 / 255, field.containsMouse ? 0.11 : 0.065)
            border.width: 1     // --shadow-sunken: inset 0 0 0 1px
            border.color: root.dark ? Qt.rgba(220 / 255, 228 / 255, 1, 0.04) : Qt.rgba(30 / 255, 40 / 255, 100 / 255, 0.05)
            Behavior on color { ColorAnimation { duration: Kirigami.Units.shortDuration } }
            Rectangle {         // --shadow-sunken: inset 0 1px 2px
                x: 8; y: 1
                width: parent.width - 16
                height: 1
                color: root.dark ? Qt.rgba(0, 0, 0, 0.35) : Qt.rgba(25 / 255, 35 / 255, 90 / 255, 0.10)
            }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 14
                spacing: 10
                Kirigami.Icon {
                    source: "search-symbolic"
                    Layout.preferredWidth: 18
                    Layout.preferredHeight: 18
                    color: root.text2
                    isMask: true
                }
                Text {
                    Layout.fillWidth: true
                    text: i18n("Search")
                    color: root.text2           // --text-secondary
                    font.family: Kirigami.Theme.defaultFont.family
                    font.pointSize: 11.625        // --type-body: 15.5 px
                    elide: Text.ElideRight
                }
            }
        }
    }
}
