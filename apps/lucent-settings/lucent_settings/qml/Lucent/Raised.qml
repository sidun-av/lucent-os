import QtQuick

// Pebble's raised "pillow": top-lit gradient, hairline ring, soft shadow.
Item {
    id: r
    property real radius: Theme.radiusControl
    property bool lifted: false
    property color topColor: Theme.raised
    property color bottomColor: Theme.raised2
    property color ring: Theme.ringRaised
    default property alias content: inner.data
    Shadow { anchors.fill: parent; radius: r.radius; layers: r.lifted ? Theme.shLift : Theme.shRaised }
    Rectangle {
        anchors.fill: parent
        anchors.margins: -1
        radius: r.radius + 1
        color: r.ring
    }
    Rectangle {
        anchors.fill: parent
        radius: r.radius
        gradient: Gradient {
            GradientStop { position: 0; color: r.topColor }
            GradientStop { position: 1; color: r.bottomColor }
        }
    }
    Rectangle {  // inset 0 1px 0 top light
        x: r.radius / 2; y: 0.5; width: parent.width - r.radius; height: 1
        color: Theme.topLight
    }
    Item { id: inner; anchors.fill: parent }
}
