import QtQuick
import org.lucent.chrome

// The empty part of the header row behaves like a title bar: drag moves the
// window (KWin's own move, so Aero-snap, drag-to-top maximise and screen
// edges all work), double-click runs kwinrc's TitlebarDoubleClickCommand,
// right-click opens KWin's window menu. Put it under the header's controls.
Item {
    id: area
    required property WindowFrame frame

    DragHandler {
        target: null
        grabPermissions: PointerHandler.CanTakeOverFromAnything
        onActiveChanged: if (active) area.frame.startMove()
    }
    TapHandler {
        acceptedButtons: Qt.LeftButton
        gesturePolicy: TapHandler.DragThreshold
        onDoubleTapped: area.frame.titleDoubleClicked()
    }
    TapHandler {
        acceptedButtons: Qt.RightButton
        onTapped: area.frame.showWindowMenu()
    }
}
