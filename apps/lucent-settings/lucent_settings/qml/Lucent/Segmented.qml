import QtQuick
import QtQuick.Layouts

// .seg: a light glass strip, the chosen segment an --accent-soft pill in accent text.
Item {
    id: seg
    property var options: []     // [{value, label}]
    property string current
    signal picked(string value)
    implicitHeight: Theme.segHeight
    implicitWidth: row.implicitWidth + 6
    Well { anchors.fill: parent; radius: Theme.radiusSegTrack; tint: Theme.glassField }
    RowLayout {
        id: row
        x: 3; y: 3
        height: seg.height - 6
        spacing: 2
        Repeater {
            model: seg.options
            Item {
                required property var modelData
                readonly property bool on: modelData.value === seg.current
                implicitWidth: lbl.implicitWidth + 32
                implicitHeight: seg.height - 6
                Rectangle { anchors.fill: parent; visible: parent.on; radius: Theme.radiusSegment; color: Theme.accentSoft }
                Rectangle { anchors.fill: parent; radius: Theme.radiusSegment; color: Theme.hover; visible: !parent.on && m.containsMouse }
                LText {
                    id: lbl
                    anchors.centerIn: parent
                    text: modelData.label
                    px: Theme.fontBody
                    weight: parent.on ? Theme.weightStrong : Theme.weightButton
                    color: parent.on ? Theme.accentText : Theme.text2
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
