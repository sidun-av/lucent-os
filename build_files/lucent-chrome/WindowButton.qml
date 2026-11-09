import QtQuick
import org.lucent.chrome

// One 44 x 36 header button, as the Lucent Aurorae decoration draws it
// (pebble-drift.css .wb i): secondary glyph, state-hover on hover, the close
// button turns status-danger with a white glyph; dimmer when the window is
// inactive.
Item {
    id: b
    required property WindowFrame frame
    property string kind: "close"                  // minimize, maximize, close
    readonly property bool dark: frame.dark
    // Pebble Drift tokens (light / dark)
    property color glyphColor: dark ? "#bcc1d6" : "#474d66"         // --text-secondary
    property color glyphInactive: dark ? "#656b84" : "#9095a8"      // --text-disabled
    property color glyphHover: dark ? "#eef0fa" : "#171a2b"         // --text-primary
    property color hoverColor: dark ? Qt.rgba(220/255, 228/255, 1, .07) : Qt.rgba(48/255, 58/255, 120/255, .065)
    property color pressedColor: dark ? Qt.rgba(220/255, 228/255, 1, .11) : Qt.rgba(48/255, 58/255, 120/255, .11)
    property color dangerColor: dark ? "#ef5f6b" : "#cf3a48"        // --status-danger
    property int radius: 10                                          // --radius-control
    signal activated()

    implicitWidth: 44
    implicitHeight: 36
    Accessible.role: Accessible.Button
    Accessible.name: kind === "minimize" ? qsTr("Minimize") : kind === "close" ? qsTr("Close")
                     : frame.maximized ? qsTr("Restore") : qsTr("Maximize")

    Rectangle {
        anchors.fill: parent
        radius: b.radius
        visible: mouse.containsMouse || mouse.pressed
        color: b.kind === "close" ? b.dangerColor : mouse.pressed ? b.pressedColor : b.hoverColor
        opacity: b.kind === "close" && mouse.pressed ? 0.85 : 1
    }
    WindowGlyph {
        anchors.centerIn: parent
        width: 17; height: 17
        kind: b.kind === "maximize" && b.frame.maximized ? "restore" : b.kind
        color: b.kind === "close" && (mouse.containsMouse || mouse.pressed) ? "#ffffff"
             : (mouse.containsMouse || mouse.pressed) ? b.glyphHover
             : b.frame.active ? b.glyphColor : b.glyphInactive
    }
    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        onClicked: {
            b.activated()
            if (b.kind === "minimize") b.frame.minimize()
            else if (b.kind === "maximize") b.frame.toggleMaximize()
            else if (b.kind === "close") b.frame.close()
        }
    }
}
