import QtQuick
import org.lucent.chrome

// Resize at the window's edges and corners with KWin's own interactive
// resize (startSystemResize). Thin strips inside the window: Lucent windows
// have no border, the decoration's resize area is also inside its shadow.
Item {
    id: h
    required property WindowFrame frame
    property int border: 6
    property int corner: 18
    anchors.fill: parent
    visible: !frame.maximized
    z: 1000

    component Edge: MouseArea {
        property int edges: 0
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton
        onPressed: h.frame.startResize(edges)
    }
    Edge { edges: Qt.TopEdge; cursorShape: Qt.SizeVerCursor
           x: h.corner; width: h.width - 2 * h.corner; height: h.border }
    Edge { edges: Qt.BottomEdge; cursorShape: Qt.SizeVerCursor
           x: h.corner; y: h.height - h.border; width: h.width - 2 * h.corner; height: h.border }
    Edge { edges: Qt.LeftEdge; cursorShape: Qt.SizeHorCursor
           y: h.corner; width: h.border; height: h.height - 2 * h.corner }
    Edge { edges: Qt.RightEdge; cursorShape: Qt.SizeHorCursor
           x: h.width - h.border; y: h.corner; width: h.border; height: h.height - 2 * h.corner }
    // corners: an L of `corner` px along both edges
    Edge { edges: Qt.TopEdge | Qt.LeftEdge; cursorShape: Qt.SizeFDiagCursor; width: h.corner; height: h.border }
    Edge { edges: Qt.TopEdge | Qt.LeftEdge; cursorShape: Qt.SizeFDiagCursor; y: h.border; width: h.border; height: h.corner - h.border }
    Edge { edges: Qt.TopEdge | Qt.RightEdge; cursorShape: Qt.SizeBDiagCursor; x: h.width - h.corner; width: h.corner; height: h.border }
    Edge { edges: Qt.TopEdge | Qt.RightEdge; cursorShape: Qt.SizeBDiagCursor; x: h.width - h.border; y: h.border; width: h.border; height: h.corner - h.border }
    Edge { edges: Qt.BottomEdge | Qt.LeftEdge; cursorShape: Qt.SizeBDiagCursor; y: h.height - h.border; width: h.corner; height: h.border }
    Edge { edges: Qt.BottomEdge | Qt.LeftEdge; cursorShape: Qt.SizeBDiagCursor; y: h.height - h.corner; width: h.border; height: h.corner - h.border }
    Edge { edges: Qt.BottomEdge | Qt.RightEdge; cursorShape: Qt.SizeFDiagCursor; x: h.width - h.corner; y: h.height - h.border; width: h.corner; height: h.border }
    Edge { edges: Qt.BottomEdge | Qt.RightEdge; cursorShape: Qt.SizeFDiagCursor; x: h.width - h.border; y: h.height - h.corner; width: h.border; height: h.corner - h.border }
}
