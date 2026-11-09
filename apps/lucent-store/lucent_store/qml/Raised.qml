// A raised "pillow" surface (pebble.css .card / .pb.raised): a light vertical
// gradient, a hairline ring, a near and a mid soft shadow, a top highlight.
// `lifted` (hover) adds the long shadow of --sh-lift.
import QtQuick

Item {
    id: r
    property real radius: store.t.radiusCard
    property bool lifted: false
    property bool flat: false               // no shadows (inside other raised things)
    property color fillTop: store.t.raised
    property color fillBottom: store.t.raised2
    default property alias content: body.data
    readonly property var tk: store.t

    Shadow { visible: !r.flat; radius: r.radius; dy: 4; blur: 10; spread: -2; strength: r.tk.shadowMid }
    Shadow { visible: !r.flat && r.lifted; radius: r.radius; dy: 14; blur: 28; spread: -8; strength: r.tk.shadowLift }
    Shadow { visible: !r.flat; radius: r.radius; dy: 1; blur: 2; strength: r.tk.shadowNear; steps: 2 }
    Rectangle {
        id: body
        anchors.fill: parent
        radius: r.radius
        border.width: 1
        border.color: r.tk.shadowRing
        gradient: Gradient {
            GradientStop { position: 0; color: r.fillTop }
            GradientStop { position: 1; color: r.fillBottom }
        }
        Rectangle {          // inset 0 1px 0 top light
            x: r.radius * 0.6; y: 1
            width: parent.width - 2 * x; height: 1
            color: r.tk.topLight
        }
    }
}
