// Lucent button (lucent.css .btn): primary, plain, done (green text), danger.
import QtQuick

Rectangle {
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
    radius: store.t.radiusButton
    color: kind === "primary" ? (area.containsMouse ? tk.accentHover : tk.accent)
         : kind === "plain" || kind === "danger" ? (area.containsMouse ? Qt.darker(tk.field, store.dark ? 0.85 : 1.04) : tk.field)
         : kind === "ghost" && area.containsMouse ? tk.hover : "transparent"
    border.width: kind === "plain" || kind === "danger" ? 1 : 0
    border.color: area.containsMouse ? tk.lineStrong : tk.line
    opacity: enabledLook ? 1 : 0.55
    activeFocusOnTab: enabledLook
    Keys.onSpacePressed: if (enabledLook) b.clicked()
    Keys.onReturnPressed: if (enabledLook) b.clicked()

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
            color: b.kind === "primary" ? b.tk.accentText : b.kind === "done" ? b.tk.ok
                 : b.kind === "danger" ? b.tk.danger : b.kind === "ghost" ? b.tk.accent : b.tk.text
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
