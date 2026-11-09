// Button: primary (accent), plain/danger (raised pillow, pebble.css .pb.raised),
// done (green text), ghost (accent text only).
import QtQuick

Item {
    id: b
    property string text
    property string kind: "plain"        // primary | plain | done | danger | ghost
    property bool small: false
    property string icon: ""
    property bool enabledLook: true
    signal clicked()
    readonly property var tk: store.t
    implicitHeight: small ? tk.buttonSmallHeight : tk.buttonHeight
    implicitWidth: row.implicitWidth + (kind === "done" ? 12 : (small ? 32 : 36))
    readonly property real radius: store.t.radiusButton
    opacity: enabledLook ? 1 : 0.55
    activeFocusOnTab: enabledLook
    Keys.onSpacePressed: if (enabledLook) b.clicked()
    Keys.onReturnPressed: if (enabledLook) b.clicked()

    Raised {
        anchors.fill: parent
        visible: b.kind === "plain" || b.kind === "danger"
        radius: b.radius
        lifted: area.containsMouse && b.enabledLook
    }
    Item {
        anchors.fill: parent
        visible: b.kind === "primary"
        Shadow { radius: b.radius; dy: 1; blur: 3; strength: b.tk.shadowNear * 2.5; steps: 3; color: b.tk.accent }
        Rectangle {
            anchors.fill: parent
            radius: b.radius
            gradient: Gradient {
                GradientStop { position: 0; color: area.containsMouse ? b.tk.accentHover : Qt.lighter(b.tk.accent, 1.06) }
                GradientStop { position: 1; color: area.containsMouse ? Qt.darker(b.tk.accentHover, 1.04) : b.tk.accent }
            }
        }
    }
    Rectangle {
        anchors.fill: parent
        radius: b.radius
        visible: b.kind === "ghost" && area.containsMouse
        color: b.tk.hover
    }
    Row {
        id: row
        anchors.centerIn: parent
        spacing: 8
        Sym {
            visible: b.icon !== ""
            name: b.icon
            size: 18
            anchors.verticalCenter: parent.verticalCenter
            tint: label.color
        }
        Text {
            id: label
            text: b.text
            anchors.verticalCenter: parent.verticalCenter
            font.pointSize: b.small ? b.tk.fontSmall : b.tk.fontText
            font.weight: Font.DemiBold
            color: b.kind === "primary" ? b.tk.onAccent : b.kind === "done" ? b.tk.ok
                 : b.kind === "danger" ? b.tk.danger : b.kind === "ghost" ? b.tk.accentText : b.tk.text
        }
    }
    Rectangle {      // keyboard focus ring
        anchors.fill: parent
        anchors.margins: -3
        radius: parent.radius + 3
        color: "transparent"
        border.width: 2
        border.color: b.tk.accent
        visible: b.activeFocus
        opacity: 0.6
    }
    MouseArea {
        id: area
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: b.enabledLook && b.kind !== "done" ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: if (b.enabledLook) b.clicked()
    }
}
