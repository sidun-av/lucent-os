// An ArtCraft alpha app (.cc in 06-store.html).
import QtQuick
import QtQuick.Layouts

Rectangle {
    id: c
    property var app
    readonly property var tk: store.t
    radius: store.t.radiusRow
    color: tk.card
    border.width: 1
    border.color: area.containsMouse ? tk.lineStrong : tk.line
    implicitHeight: 92
    MouseArea { id: area; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                onClicked: win.openApp(c.app.id) }
    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 18
        anchors.rightMargin: 18
        spacing: 16
        AppIcon { src: c.app.icon; size: store.t.iconCraft; Layout.alignment: Qt.AlignVCenter }
        Column {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignVCenter
            spacing: 3
            Row {
                spacing: 10
                Text { text: c.app.name; font.pointSize: store.t.fontName; font.weight: Font.DemiBold; color: c.tk.text
                       anchors.verticalCenter: parent.verticalCenter }
                AlphaBadge { anchors.verticalCenter: parent.verticalCenter }
            }
            Text { width: parent.width; text: c.app.summary; font.pointSize: store.t.fontSmall; color: c.tk.text2; elide: Text.ElideRight }
        }
        ActionButton {
            Layout.alignment: Qt.AlignVCenter
            state_: c.app.supported ? c.app.state : "unsupported"
            progress: c.app.progress
            installText: l10n.text("Try")
            installKind: "plain"
            openWhenInstalled: true
            onInstall: store.install([c.app.id], c.app.name)
            onOpen: store.launch(c.app.id)
        }
    }
}
