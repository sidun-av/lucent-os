import QtQuick
import QtQuick.Controls.Basic as C

C.TextField {
    id: f
    implicitHeight: Theme.controlHeight
    implicitWidth: 280
    font.family: Theme.font
    font.pixelSize: Theme.fontBody
    color: Theme.text
    placeholderTextColor: Theme.text3
    selectionColor: Theme.sel
    selectedTextColor: Theme.text
    leftPadding: 12
    rightPadding: 12
    background: Rectangle {
        radius: Theme.radiusControl
        color: Theme.field
        border.width: f.activeFocus ? 2 : 1
        border.color: f.activeFocus ? Theme.accent : Theme.line
    }
}
