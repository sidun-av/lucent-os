import QtQuick
import QtQuick.Layouts

// .row: label + optional sub line on the left, controls on the right.
Item {
    id: row
    property string label
    property string sub
    property alias leading: lead.data
    default property alias trailing: trail.data
    property bool separator: y > 0
    property int minHeight: Theme.rowMin
    property bool clickable: false
    property real labelWeight: Theme.weightLabel
    property int labelPx: Theme.fontLabel
    signal clicked()
    Layout.fillWidth: true
    implicitHeight: Math.max(minHeight, content.implicitHeight + 2 * Theme.rowPadV)

    Rectangle {
        visible: row.separator
        anchors { left: parent.left; right: parent.right; top: parent.top }
        height: 1
        color: Theme.line
    }
    Rectangle {
        anchors.fill: parent
        anchors.topMargin: row.separator ? 1 : 0
        color: Theme.hover
        visible: row.clickable && mouse.containsMouse
    }
    MouseArea {
        id: mouse
        anchors.fill: parent
        enabled: row.clickable
        hoverEnabled: row.clickable
        cursorShape: row.clickable ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: row.clicked()
    }
    RowLayout {
        id: content
        anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter
                  leftMargin: Theme.rowPadH; rightMargin: Theme.rowPadH }
        spacing: Theme.rowGap
        RowLayout {
            id: lead
            spacing: 14
            visible: children.length > 0
        }
        ColumnLayout {
            spacing: 3
            Layout.fillWidth: true
            Layout.minimumWidth: 120
            LText {
                text: row.label
                px: row.labelPx
                weight: row.labelWeight
                Layout.fillWidth: true
                visible: text !== ""
            }
            LText {
                text: row.sub
                px: Theme.fontSub
                color: Theme.text2
                wrapMode: Text.WordWrap
                elide: Text.ElideNone
                lineHeight: 1.15
                Layout.fillWidth: true
                visible: text !== ""
            }
        }
        RowLayout {
            id: trail
            spacing: 10
            Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
        }
    }
}
