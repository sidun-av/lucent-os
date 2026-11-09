import QtQuick

// Glass Card (glass.css .card / .field): a light card that sits ON the
// surface: --elev-1 hairline ring + 1 px contact drop (one Rectangle behind),
// an opaque light fill, the 1 px --glass-highlight top line and inner rim.
// flat: a plain tint with nothing around it (tracks, icon tiles).
Rectangle {
    id: w
    property color tint: Theme.well
    property bool flat: false
    default property alias content: inner.data
    radius: Theme.radiusControl
    color: tint
    border.width: flat ? 0 : 1
    border.color: Theme.glassRim
    Rectangle {          // ring + contact drop, drawn under the card
        z: -1
        visible: !w.flat
        x: -1; y: -1
        width: w.width + 2; height: w.height + 3
        radius: w.radius + 1
        color: Theme.elevRing
    }
    Rectangle {          // the top light
        visible: !w.flat && w.height > 8
        x: Math.min(w.radius, w.width / 2) * 0.7; y: 0
        width: w.width - 2 * x; height: 1
        color: Theme.glassTop
    }
    Item { id: inner; anchors.fill: parent }
}
