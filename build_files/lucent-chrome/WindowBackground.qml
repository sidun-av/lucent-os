import QtQuick
import org.lucent.chrome

// The window's own surface, as the Lucent decoration draws the decorated
// windows' (design/gen_aurorae.py): the 1 px top light of --highlight-top,
// and the corners: square when the KDE-Rounded-Corners effect is on (it
// clips and outlines this window exactly as it does the decorated ones),
// else rounded here with the 1 px ring of --shadow-window. Square when
// maximised.
Item {
    id: bg
    required property WindowFrame frame
    property color color: frame.dark ? "#1d1f2e" : "#f2f3fa"         // --surface-window-solid
    property color highlight: frame.dark ? Qt.rgba(220/255, 228/255, 1, .08) : Qt.rgba(1, 1, 1, .9)
    readonly property bool ring: !frame.compositorRounds
    readonly property int radius: frame.maximized || frame.compositorRounds ? 0 : frame.radius
    anchors.fill: parent

    Rectangle {                 // the top light: what the surface leaves of it 1 px lower
        anchors.fill: parent
        radius: bg.radius
        color: bg.highlight
        visible: !bg.frame.maximized
        antialiasing: bg.radius > 0
    }
    Rectangle {
        anchors.fill: parent
        anchors.topMargin: bg.frame.maximized ? 0 : 1
        radius: bg.radius
        color: bg.color
        antialiasing: true
    }
    Rectangle {
        anchors.fill: parent
        radius: bg.radius
        color: "transparent"
        visible: bg.ring && !bg.frame.maximized
        border.width: 1
        border.color: bg.frame.dark ? Qt.rgba(0, 0, 0, .55) : Qt.rgba(30/255, 40/255, 100/255, .10)
        antialiasing: true
    }
}
