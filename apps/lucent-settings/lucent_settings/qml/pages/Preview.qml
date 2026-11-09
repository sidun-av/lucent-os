import QtQuick
import QtQuick.Shapes
import Lucent

// The mockup's miniature desktop (.pv.light / .pv.dark): wallpaper
// gradient, a window with a sidebar and three text bars, a taskbar.
Item {
    id: p
    property bool dark: false
    Shape {
        anchors.fill: parent
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            strokeWidth: -1
            fillGradient: LinearGradient {
                x1: 0; y1: 0; x2: p.width; y2: p.height
                GradientStop { position: 0; color: p.dark ? "#1b2350" : "#bcd0ff" }
                GradientStop { position: 0.6; color: p.dark ? "#3b1d5e" : "#ffd3e4" }
                GradientStop { position: 1; color: p.dark ? "#0d2a40" : "#cfeaff" }
            }
            PathRectangle { x: 0; y: 0; width: p.width; height: p.height }
        }
    }
    // box-shadow: 0 6px 16px rgba(0,0,0,.18), drawn as soft rings (this
    // picture is itself a layer, where a nested blur effect doesn't render)
    Repeater {
        model: 6
        Rectangle {
            required property int index
            readonly property real spread: 1 + index * 1.6
            x: w.x - spread; y: w.y + 5 - spread
            width: w.width + 2 * spread; height: w.height + 2 * spread
            radius: w.radius + spread
            color: Qt.rgba(0, 0, 0, (p.dark ? 0.06 : 0.035) * (6 - index) / 6)
        }
    }
    Rectangle {
        id: w
        x: 24; y: 22
        width: p.width - 24 - 60
        height: p.height - 22 - 44
        radius: 8
        color: p.dark ? "#23262e" : "#ffffff"
        Rectangle {
            width: parent.width * 0.3; height: parent.height
            radius: 8
            color: p.dark ? "#1a1c22" : "#f1f3f7"
            Rectangle { anchors.right: parent.right; width: 8; height: parent.height; color: parent.color }
        }
        Repeater {
            model: [[18, 0.40], [36, 0.50], [54, 0.30]]
            Rectangle {
                required property var modelData
                x: w.width * 0.36; y: modelData[0]
                width: w.width * modelData[1]; height: 8; radius: 4
                color: p.dark ? "#3a3f4a" : "#dfe3ea"
            }
        }
    }
    Rectangle {
        x: 10; width: p.width - 20; height: 22
        y: p.height - 8 - height
        radius: 8
        color: p.dark ? Qt.rgba(40 / 255, 44 / 255, 54 / 255, 0.75) : Qt.rgba(1, 1, 1, 0.7)
    }
}
