import QtQuick
import QtQuick.Layouts

// .settings .si: 46 px row, 30 px coloured square with a white glyph.
Rectangle {
    id: si
    property string icon
    property color tint
    property string text
    property string value
    property int count: 0
    property bool selected: false
    signal clicked()
    Layout.fillWidth: true
    implicitHeight: Theme.sideItemHeight
    radius: Theme.radiusItem
    color: selected ? Theme.sel : (m.containsMouse ? Theme.hover : "transparent")
    RowLayout {
        anchors { fill: parent; leftMargin: 10; rightMargin: 10 }
        spacing: 13
        Rectangle {
            width: Theme.sideIcon; height: Theme.sideIcon; radius: Theme.radiusItem
            color: si.tint
            Sym { anchors.centerIn: parent; name: si.icon; size: 18; color: "#ffffff" }
        }
        LText { text: si.text; px: Theme.fontBody; weight: si.selected ? Theme.weightStrong : 400; Layout.fillWidth: true }
        LText { text: si.value; visible: si.value !== ""; px: Theme.fontSub; color: Theme.text2; Layout.maximumWidth: 110 }
        Rectangle {
            visible: si.count > 0
            implicitWidth: Math.max(22, c.implicitWidth + 16)
            implicitHeight: 20
            radius: Theme.radiusTile
            color: Theme.accent
            LText { id: c; anchors.centerIn: parent; text: si.count; px: Theme.fontSmall; weight: Theme.weightHeading; color: "#ffffff" }
        }
    }
    MouseArea { id: m; anchors.fill: parent; hoverEnabled: true; onClicked: si.clicked() }
}
