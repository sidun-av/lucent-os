import QtQuick
import QtQuick.Layouts

// .si: 38 px row, line glyph; selected = a soft --accent-soft pill, accent text.
Item {
    id: si
    property string icon
    property string text
    property string value
    property int count: 0
    property bool selected: false
    signal clicked()
    Layout.fillWidth: true
    implicitHeight: Theme.sideItemHeight
    Rectangle { anchors.fill: parent; visible: si.selected; radius: Theme.radiusItem; color: Theme.accentSoft }
    Rectangle { anchors.fill: parent; radius: Theme.radiusItem; color: Theme.hover; visible: !si.selected && m.containsMouse }
    RowLayout {
        anchors { fill: parent; leftMargin: 12; rightMargin: 10 }
        spacing: 12
        Sym { name: si.icon; size: Theme.sideGlyph; color: si.selected ? Theme.accent : Theme.text2 }
        LText {
            text: si.text
            px: Theme.fontSide
            weight: si.selected ? Theme.weightHeading : Theme.weightSide
            color: si.selected ? Theme.accentText : Theme.text
            Layout.fillWidth: true
        }
        LText { text: si.value; visible: si.value !== ""; px: Theme.fontSub; color: Theme.text3; Layout.maximumWidth: 100 }
        Pill { visible: si.count > 0; text: si.count; kind: "accent"; Layout.minimumWidth: 26 }
    }
    MouseArea { id: m; anchors.fill: parent; hoverEnabled: true; onClicked: si.clicked() }
}
