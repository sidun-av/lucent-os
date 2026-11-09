import QtQuick
import QtQuick.Layouts

// .pb.raised pillow button; primary = accent fill; flat = text only.
Item {
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
    implicitWidth: row.implicitWidth + (b.text !== "" ? 32 : 18)
    opacity: enabled ? 1 : 0.5
    Raised {
        anchors.fill: parent
        visible: !b.flat
        radius: Theme.radiusControl
        lifted: mouse.containsMouse && !mouse.pressed
        topColor: b.primary ? Qt.lighter(Theme.accent, 1.06) : (mouse.pressed ? Theme.raised2 : Theme.raised)
        bottomColor: b.primary ? Theme.accent : Theme.raised2
        ring: b.primary ? Qt.rgba(0, 0, 0, 0.10) : Theme.ringRaised
    }
    Rectangle {
        anchors.fill: parent
        visible: b.flat && mouse.containsMouse
        radius: Theme.radiusControl
        color: Theme.hover
    }
    RowLayout {
        id: row
        anchors.centerIn: parent
        spacing: 8
        Spinner { visible: b.busy; size: 16; color: b.primary ? Theme.textOnAccent : Theme.text2 }
        Sym {
            visible: b.icon !== "" && !b.busy
            name: b.icon
            size: 18
            color: b.primary ? Theme.textOnAccent : b.danger ? Theme.danger : Theme.text2
        }
        LText {
            visible: b.text !== ""
            text: b.text
            px: Theme.fontBody
            weight: Theme.weightButton
            color: b.primary ? Theme.textOnAccent : b.danger ? Theme.danger : Theme.text
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
