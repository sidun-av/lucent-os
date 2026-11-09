import QtQuick
import QtQuick.Effects
import org.lucent.chrome
import Lucent

// Frameless window (System.frameless): the surface, grain, shadow, window
// buttons and title-bar behaviour of the header row, from the shared
// org.lucent.chrome module (build_files/lucent-chrome). Main.qml loads it
// under everything else; the buttons and the resize edges go into the slots
// it passes (leftSlot / rightSlot in the header row, overlay on top).
Item {
    id: f
    property var win
    property Item leftSlot
    property Item rightSlot
    property Item overlay
    property int headerHeight: Theme.headerHeightFrameless
    readonly property alias frame: wf
    anchors.fill: parent

    WindowFrame { id: wf; window: f.win; dark: Theme.dark }
    WindowBackground { id: bg; frame: wf; color: Theme.surface }
    // fine grain over the matte surface, inside the rounded corners
    Image {
        id: grain
        anchors.fill: parent
        source: "../Lucent/grain.png"
        fillMode: Image.Tile
        smooth: false
        visible: false
    }
    Rectangle { id: mask; anchors.fill: parent; radius: bg.radius; visible: false; layer.enabled: true }
    MultiEffect {
        anchors.fill: parent
        source: grain
        maskEnabled: true
        maskSource: mask
        opacity: Theme.grainOpacity
    }
    HeaderDragArea { frame: wf; width: parent.width; height: f.headerHeight }

    WindowButtons { parent: f.leftSlot; frame: wf; side: "left"; appIcon: "systemsettings"
                    anchors.verticalCenter: parent ? parent.verticalCenter : undefined }
    WindowButtons { parent: f.rightSlot; frame: wf; side: "right"; appIcon: "systemsettings"
                    anchors.verticalCenter: parent ? parent.verticalCenter : undefined }
    ResizeHandles { parent: f.overlay; frame: wf }
}
