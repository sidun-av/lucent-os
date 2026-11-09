// A recessed well (pebble.css --well + --sh-well): sidebar, fields, tracks.
import QtQuick

Rectangle {
    id: w
    property bool strong: false
    readonly property var tk: store.t
    radius: tk.radiusCard
    color: strong ? tk.wellStrong : tk.well
    border.width: 1
    border.color: tk.wellRing
    Rectangle {          // inset 0 1px 2px: a soft shade under the top edge
        x: Math.min(w.radius, w.width / 2) * 0.7
        y: 1
        width: w.width - 2 * x
        height: Math.min(3, w.height / 3)
        gradient: Gradient {
            GradientStop { position: 0; color: w.tk.wellShade }
            GradientStop { position: 1; color: "transparent" }
        }
    }
}
