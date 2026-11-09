import QtQuick

// Soft shadow under a rounded rectangle, as stacked translucent rings
// (cheap, and it renders the same on the software renderer).
// layers: [[alpha, yOffset, spread], ...] from Theme.shRaised / shLift.
Item {
    id: sh
    property real radius: Theme.radiusCard
    property var layers: Theme.shRaised
    Repeater {
        model: sh.layers
        Item {
            required property var modelData
            anchors.fill: parent
            Repeater {
                model: 4
                Rectangle {
                    required property int index
                    readonly property real s: modelData[2] * (index + 1) / 4
                    x: -s; y: -s + modelData[1]
                    width: sh.width + 2 * s; height: sh.height + 2 * s
                    radius: sh.radius + s
                    color: Qt.rgba(Theme.shadowColor.r, Theme.shadowColor.g, Theme.shadowColor.b,
                                   modelData[0] * (4 - index) / 10)
                }
            }
        }
    }
}
