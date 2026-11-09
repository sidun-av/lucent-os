// A soft drop shadow drawn as stacked translucent rounded rectangles, so it
// looks the same with every Qt Quick renderer (also software / llvmpipe).
// CSS equivalent: box-shadow: 0 <dy> <blur> <spread> rgba(<color>, <strength>).
import QtQuick

Item {
    id: s
    property real radius: 10
    property real dy: 2
    property real blur: 8
    property real spread: 0
    property real strength: 0.1
    property color color: store.t.shadow
    property int steps: 6
    anchors.fill: parent
    Repeater {
        model: s.steps
        Rectangle {
            required property int index
            readonly property real grow: s.spread + s.blur * (index + 0.5) / s.steps - s.blur / 2
            x: -grow
            y: -grow + s.dy
            width: s.width + 2 * grow
            height: s.height + 2 * grow
            radius: Math.max(0, s.radius + grow)
            color: Qt.rgba(s.color.r, s.color.g, s.color.b, s.strength / s.steps * 1.6)
        }
    }
}
