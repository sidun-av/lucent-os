import QtQuick

Rectangle {
    id: it
    property string icon
    property string text
    property string target
    property int count: 0
    property bool selected: win.page === target
    readonly property var tk: store.t
    width: parent ? parent.width : 266
    height: store.t.sideItemHeight
    radius: store.t.radiusItem
    color: selected ? tk.sel : area.containsMouse ? tk.hover : "transparent"
    activeFocusOnTab: true
    Keys.onReturnPressed: win.go(target)
    Keys.onSpacePressed: win.go(target)

    Sym {
        id: ic
        name: it.icon
        tint: it.tk.accent
        size: 20
        x: 10
        anchors.verticalCenter: parent.verticalCenter
    }
    Text {
        anchors.left: ic.right
        anchors.leftMargin: 11
        anchors.right: badge.left
        anchors.verticalCenter: parent.verticalCenter
        text: it.text
        elide: Text.ElideRight
        font.pointSize: store.t.fontBody
        font.weight: it.selected ? Font.DemiBold : Font.Normal
        color: it.tk.text
    }
    Rectangle {
        id: badge
        visible: it.count > 0
        anchors.right: parent.right
        anchors.rightMargin: 10
        anchors.verticalCenter: parent.verticalCenter
        width: Math.max(height, n.implicitWidth + 16)
        height: 20
        radius: store.t.radiusButton
        color: it.tk.accent
        Text { id: n; anchors.centerIn: parent; text: it.count; color: "white"
               font.pointSize: store.t.fontLabel; font.weight: Font.DemiBold }
    }
    Rectangle {
        anchors.fill: parent; radius: parent.radius; color: "transparent"
        border.width: 2; border.color: it.tk.accent; opacity: 0.6; visible: it.activeFocus
    }
    MouseArea {
        id: area
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: win.go(it.target)
    }
}
