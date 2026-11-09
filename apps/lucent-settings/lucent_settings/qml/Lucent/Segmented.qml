import QtQuick
import QtQuick.Layouts

// .seg: field-coloured track, 3 px padding; the chosen segment is a white
// chip with a soft shadow.
Rectangle {
    id: seg
    property var options: []     // [{value, label}]
    property string current
    signal picked(string value)
    implicitHeight: Theme.segHeight
    implicitWidth: row.implicitWidth + 6
    radius: Theme.radiusControl
    color: Theme.field
    RowLayout {
        id: row
        x: 3; y: 3
        height: Theme.segHeight - 6
        spacing: 2
        Repeater {
            model: seg.options
            Rectangle {
                required property var modelData
                readonly property bool on: modelData.value === seg.current
                implicitWidth: lbl.implicitWidth + 28
                implicitHeight: Theme.segHeight - 6
                radius: Theme.radiusSegment
                color: on ? Theme.winBg : (m.containsMouse ? Theme.hover : "transparent")
                border.color: on && Theme.dark ? Theme.line : "transparent"
                Rectangle {  // shadow: 0 1px 3px rgba(0,0,0,.12)
                    visible: parent.on && !Theme.dark
                    z: -1
                    anchors.fill: parent
                    anchors.topMargin: 1
                    anchors.bottomMargin: -1
                    radius: Theme.radiusSegment
                    color: Theme.shadow
                }
                LText {
                    id: lbl
                    anchors.centerIn: parent
                    text: modelData.label
                    px: Theme.fontBody
                    weight: parent.on ? 500 : 400
                    color: parent.on ? Theme.text : Theme.text2
                }
                MouseArea {
                    id: m
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: seg.picked(modelData.value)
                }
            }
        }
    }
}
