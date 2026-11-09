// "Instead of Adobe Photoshop -> GIMP" card (.rc in 06-store.html).
import QtQuick
import QtQuick.Layouts

Raised {
    id: c
    property var card
    readonly property var tk: store.t
    radius: store.t.radiusCard
    lifted: area.containsMouse
    implicitHeight: col.implicitHeight + 2 * tk.cardPadY
    implicitWidth: 400

    MouseArea {
        id: area
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: win.openApp(c.card.appIds[0])
    }
    Column {
        id: col
        x: c.tk.cardPadX
        y: c.tk.cardPadY
        width: parent.width - 2 * c.tk.cardPadX
        spacing: 16
        Row {
            spacing: 10
            Text { text: l10n.text("Instead of"); font.pointSize: store.t.fontSmall; color: c.tk.text2; anchors.verticalCenter: parent.verticalCenter }
            Rectangle {
                anchors.verticalCenter: parent.verticalCenter
                radius: store.t.radiusChip
                color: c.tk.wellStrong
                width: wn.implicitWidth + 20
                height: wn.implicitHeight + 6
                Text { id: wn; anchors.centerIn: parent; text: c.card.windows; font.pointSize: store.t.fontSmall
                       font.weight: Font.DemiBold; color: c.tk.text }
            }
            Sym { name: "arrowr"; size: 16; tint: c.tk.text3; anchors.verticalCenter: parent.verticalCenter }
        }
        RowLayout {
            width: parent.width
            spacing: 16
            Row {
                spacing: 8
                Layout.alignment: Qt.AlignVCenter
                Repeater {
                    model: c.card.icons
                    AppIcon { required property var modelData; src: modelData; size: store.t.iconCard }
                }
            }
            Column {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter
                spacing: 3
                Text { width: parent.width; text: c.card.name; font.pointSize: store.t.fontTitle; font.weight: Font.DemiBold
                       color: c.tk.text; elide: Text.ElideRight }
                Text { width: parent.width; text: c.card.description; font.pointSize: store.t.fontSmall; color: c.tk.text2
                       wrapMode: Text.WordWrap; lineHeight: 1.12; maximumLineCount: 3; elide: Text.ElideRight }
                Text { visible: c.card.note !== ""; width: parent.width; text: c.card.note; font.pointSize: store.t.fontMeta
                       color: c.tk.text3; wrapMode: Text.WordWrap; topPadding: 2 }
            }
            ActionButton {
                Layout.alignment: Qt.AlignVCenter
                state_: c.card.state
                progress: c.card.progress
                onInstall: store.install(c.card.appIds, c.card.name)
                onOpen: win.openApp(c.card.appIds[0])
            }
        }
    }
}
