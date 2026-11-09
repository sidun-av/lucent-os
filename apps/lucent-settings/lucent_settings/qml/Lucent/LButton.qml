import QtQuick
import QtQuick.Layouts

// .btn (40 px, 10 px corners, 15/600) and .btn.primary; `busy` shows a spinner.
Rectangle {
    id: b
    property string text
    property string icon
    property bool primary: false
    property bool danger: false
    property bool flat: false
    property bool busy: false
    property int h: Theme.controlHeight
    signal clicked()
    implicitHeight: h
    implicitWidth: row.implicitWidth + 36
    radius: Theme.radiusControl
    opacity: enabled ? 1 : 0.5
    color: flat ? (mouse.containsMouse ? Theme.hover : "transparent")
                : primary ? (mouse.pressed ? Qt.darker(Theme.accent, 1.12) : mouse.containsMouse ? Qt.lighter(Theme.accent, 1.06) : Theme.accent)
                : (mouse.pressed ? Qt.darker(Theme.field, 1.06) : mouse.containsMouse ? Qt.darker(Theme.field, Theme.dark ? 0.9 : 1.03) : Theme.field)
    border.color: primary || flat ? "transparent" : Theme.line
    border.width: 1
    RowLayout {
        id: row
        anchors.centerIn: parent
        spacing: 8
        Spinner { visible: b.busy; size: 16; color: b.primary ? "#ffffff" : Theme.text2 }
        Sym {
            visible: b.icon !== "" && !b.busy
            name: b.icon
            size: 18
            color: b.primary ? "#ffffff" : b.danger ? Theme.danger : b.flat ? Theme.accent : Theme.text
        }
        LText {
            text: b.text
            px: Theme.fontBody
            weight: Theme.weightStrong
            color: b.primary ? Theme.accentText : b.danger ? Theme.danger : b.flat ? Theme.accent : Theme.text
            elide: Text.ElideNone
        }
    }
    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        enabled: b.enabled && !b.busy
        cursorShape: Qt.PointingHandCursor
        onClicked: b.clicked()
    }
}
