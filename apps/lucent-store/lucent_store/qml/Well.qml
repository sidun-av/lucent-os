import QtQuick

// Glass Card (glass.css .card): a light card that sits ON the surface: the
// --elev-1 ring + 1 px contact drop (one Rectangle behind), an opaque light
// fill, the --glass-highlight top line and inner rim. strong: a flat --track
// tint with nothing around it (progress tracks).
Rectangle {
    id: w
    property bool strong: false
    property color tint: strong ? tk.wellStrong : tk.well
    readonly property var tk: store.t
    radius: tk.radiusCard
    color: tint
    border.width: strong ? 0 : 1
    border.color: tk.glassRim
    Rectangle {          // ring + contact drop, under the card
        z: -1
        visible: !w.strong
        x: -1; y: -1
        width: w.width + 2; height: w.height + 3
        radius: w.radius + 1
        color: w.tk.wellRing
    }
    Rectangle {          // the top light
        visible: !w.strong && w.height > 8
        x: Math.min(w.radius, w.width / 2) * 0.7; y: 0
        width: w.width - 2 * x; height: 1
        color: w.tk.wellShade
    }
}
