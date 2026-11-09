import QtQuick

Item {
    id: it
    property string icon
    property string text
    property string target
    property int count: 0
    property bool selected: win.page === target
    readonly property var tk: store.t
    width: parent ? parent.width : 266
    height: store.t.sideItemHeight
    Rectangle { anchors.fill: parent; radius: store.t.radiusItem; color: it.tk.hover
                visible: area.containsMouse && !it.selected }
    Raised { anchors.fill: parent; radius: store.t.radiusItem; visible: it.selected }
    activeFocusOnTab: true
    Keys.onReturnPressed: win.go(target)
    Keys.onSpacePressed: win.go(target)

    Sym {
        id: ic
        name: it.icon
        tint: it.selected ? it.tk.accent : it.tk.text2
        size: 20
        x: 12
        anchors.verticalCenter: parent.verticalCenter
    }
    Text {
        anchors.left: ic.right
        anchors.leftMargin: 12
        anchors.right: badge.left
        anchors.verticalCenter: parent.verticalCenter
        text: it.text
        elide: Text.ElideRight
        font.pointSize: store.t.fontBody
        font.weight: it.selected ? Font.DemiBold : Font.Medium
        color: it.selected ? it.tk.accentText : it.tk.text
    }
    Rectangle {
        id: badge
        visible: it.count > 0
        anchors.right: parent.right
        anchors.rightMargin: 10
        anchors.verticalCenter: parent.verticalCenter
        width: Math.max(height, n.implicitWidth + 16)
        height: 20
        radius: store.t.radiusBadge
        color: it.tk.accentSoft
        Text { id: n; anchors.centerIn: parent; text: it.count; color: it.tk.accentText
               font.pointSize: store.t.fontLabel; font.weight: Font.DemiBold }
    }
    Rectangle {
        anchors.fill: parent; radius: store.t.radiusItem; color: "transparent"
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
