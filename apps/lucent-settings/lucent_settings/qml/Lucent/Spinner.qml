import QtQuick
import QtQuick.Shapes

Item {
    id: sp
    property int size: 18
    property color color: Theme.text2
    width: size; height: size
    Shape {
        anchors.fill: parent
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            strokeColor: sp.color
            strokeWidth: Math.max(1.6, sp.size / 10)
            fillColor: "transparent"
            capStyle: ShapePath.RoundCap
            PathAngleArc {
                centerX: sp.size / 2; centerY: sp.size / 2
                radiusX: sp.size / 2 - 1.5; radiusY: sp.size / 2 - 1.5
                startAngle: 0; sweepAngle: 270
            }
        }
        RotationAnimator on rotation { from: 0; to: 360; duration: 900; loops: Animation.Infinite; running: sp.visible }
    }
}
