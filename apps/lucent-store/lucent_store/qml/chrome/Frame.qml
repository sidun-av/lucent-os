import QtQuick
import QtQuick.Effects
import org.lucent.chrome

// Frameless window (`frameless`, app.py): the surface, grain, shadow, window
// buttons and title-bar behaviour of the top row, from the shared
// org.lucent.chrome module (build_files/lucent-chrome; Settings uses the same).
// Main.qml loads it under everything else; the buttons and the resize edges
// go into the slots it passes (leftSlot above the sidebar, rightSlot at the
// end of the page header row, overlay on top).
Item {
    id: f
    property var win
    property Item leftSlot
    property Item rightSlot
    property Item overlay
    property int headerHeight: 64
    readonly property alias frame: wf
    readonly property var tk: store.t
    anchors.fill: parent

    WindowFrame { id: wf; window: f.win; dark: store.dark }
    WindowBackground { id: bg; frame: wf; color: f.tk.winBg }
    Image {
        id: grain
        anchors.fill: parent
        source: "../../icons/" + f.tk.grain
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
        opacity: f.tk.grainOpacity
    }
    HeaderDragArea { frame: wf; width: parent.width; height: f.headerHeight }

    WindowButtons { parent: f.leftSlot; frame: wf; side: "left"; appIcon: "system-software-install"
                    anchors.verticalCenter: parent ? parent.verticalCenter : undefined }
    WindowButtons { parent: f.rightSlot; frame: wf; side: "right"; appIcon: "system-software-install"
                    anchors.verticalCenter: parent ? parent.verticalCenter : undefined }
    ResizeHandles { parent: f.overlay; frame: wf }
}
