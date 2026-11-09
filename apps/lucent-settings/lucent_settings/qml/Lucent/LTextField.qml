import QtQuick
import QtQuick.Controls.Basic as C

// .field: light glass with a hairline; focused = an accent ring.
C.TextField {
    id: f
    implicitHeight: Theme.fieldHeight
    implicitWidth: 280
    font.family: Theme.font
    font.pixelSize: Theme.fontBody
    color: Theme.text
    placeholderTextColor: Theme.text3
    selectionColor: Theme.accentSoft
    selectedTextColor: Theme.text
    leftPadding: 14
    rightPadding: 14
    background: Item {
        Rectangle {
            anchors.fill: parent; anchors.margins: -6
            radius: Theme.radiusControl + 6
            color: Theme.accentSoft
            visible: f.activeFocus
        }
        Rectangle {
            anchors.fill: parent; anchors.margins: -2
            radius: Theme.radiusControl + 2
            color: Theme.accent
            visible: f.activeFocus
        }
        Rectangle { anchors.fill: parent; radius: Theme.radiusControl; color: Theme.raised; visible: f.activeFocus }
        Well { anchors.fill: parent; visible: !f.activeFocus; tint: Theme.glassField }
    }
}
