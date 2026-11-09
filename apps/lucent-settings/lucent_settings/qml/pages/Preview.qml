import QtQuick
import Lucent

// The mode tile's miniature desktop: the person's own wallpaper (day or
// night image), a window with a sidebar and an accent line, a taskbar.
// These are pictures of light and dark, so their colours are fixed per mode.
Item {
    id: p
    property bool dark: false
    property string wallpaper
    Rectangle { anchors.fill: parent; color: p.dark ? "#141829" : "#e4ebff" }
    Image {
        anchors.fill: parent
        source: p.wallpaper
        sourceSize: Qt.size(640, 360)
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
    }
    Repeater {   // the window's soft shadow
        model: 5
        Rectangle {
            required property int index
            readonly property real s: 1 + index * 2
            x: w.x - s; y: w.y + 6 - s
            width: w.width + 2 * s; height: w.height + 2 * s
            radius: w.radius + s
            color: Qt.rgba(0.08, 0.1, 0.3, (p.dark ? 0.14 : 0.06) * (5 - index) / 5)
        }
    }
    Rectangle {
        id: w
        x: p.width * 0.14; y: p.height * 0.12
        width: p.width * 0.62; height: p.height * 0.58
        radius: 8
        color: p.dark ? "#262a39" : "#fbfcff"
        Rectangle {
            x: 6; y: parent.height * 0.16
            width: parent.width * 0.28 - 6; height: parent.height * 0.84 - 6
            radius: 5
            color: p.dark ? Qt.rgba(0, 0, 0, 0.25) : Qt.rgba(60 / 255, 80 / 255, 140 / 255, 0.08)
        }
        Repeater {
            model: [[0.40, true], [0.55, false], [0.38, false]]
            Rectangle {
                required property var modelData
                required property int index
                x: w.width * 0.28 + 10; y: w.height * 0.16 + 6 + index * 12
                width: (w.width * 0.72 - 18) * modelData[0]; height: 6; radius: 3
                color: modelData[1] ? Theme.accent : (p.dark ? "#454a5e" : "#dde3f0")
            }
        }
    }
    Rectangle {
        anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
        height: parent.height * 0.11
        color: p.dark ? Qt.rgba(27 / 255, 30 / 255, 43 / 255, 0.92) : Qt.rgba(246 / 255, 248 / 255, 253 / 255, 0.9)
    }
}
