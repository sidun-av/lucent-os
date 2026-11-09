import QtQuick

// Pebble's sunken well: tinted, with an inner top shadow and a faint ring.
Rectangle {
    id: w
    property color tint: Theme.well
    default property alias content: inner.data
    radius: Theme.radiusControl
    color: tint
    border.width: 1
    border.color: Qt.rgba(Theme.wellTop.r, Theme.wellTop.g, Theme.wellTop.b, Theme.wellTop.a * 0.35)
    Rectangle {  // inset 0 1px 2px
        x: w.radius / 2; y: 1; width: parent.width - w.radius; height: 1.5
        color: Theme.wellTop
        opacity: 0.8
    }
    Item { id: inner; anchors.fill: parent }
}
