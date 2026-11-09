/*
    Lucent taskbar search field (lucent.css #taskbar .tsearch): a 300 x 42
    rounded field. Clicking it, or typing while it has focus, opens the
    launcher (the panel applet that provides org.kde.plasma.launchermenu) with
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
            height: 42
            radius: 12
            color: root.dark ? Qt.rgba(1, 1, 1, field.containsMouse ? 0.10 : 0.06)
                             : Qt.rgba(1, 1, 1, field.containsMouse ? 0.75 : 0.55)
            border.width: 1
            border.color: root.dark ? Qt.rgba(1, 1, 1, 0.09) : Qt.rgba(20 / 255, 28 / 255, 45 / 255, 0.10)
            Behavior on color { ColorAnimation { duration: Kirigami.Units.shortDuration } }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 14
                spacing: 10
                Kirigami.Icon {
                    source: "search-symbolic"
                    Layout.preferredWidth: 18
                    Layout.preferredHeight: 18
                    color: Kirigami.Theme.textColor
                    isMask: true
                    opacity: 0.75
                }
                Text {
                    Layout.fillWidth: true
                    text: i18n("Search")
                    color: Kirigami.Theme.textColor
                    opacity: 0.72
                    font.family: Kirigami.Theme.defaultFont.family
                    font.pixelSize: 15
                    elide: Text.ElideRight
                }
            }
        }
    }
}
