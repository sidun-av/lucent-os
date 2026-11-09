// One app in a list (category, search, installed, updates).
import QtQuick
import QtQuick.Layouts

Rectangle {
    id: r
    property var app
    property string meta: ""              // extra line (size, version, ...)
    property bool showRemove: false
    property bool showUpdate: false
    readonly property var tk: store.t
    radius: store.t.radiusRow
    color: tk.card
    border.width: 1
    border.color: area.containsMouse ? tk.lineStrong : tk.line
    implicitHeight: Math.max(92, lay.implicitHeight + 32)

    MouseArea { id: area; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                onClicked: win.openApp(r.app.id) }
    RowLayout {
        id: lay
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: 18
        anchors.rightMargin: 18
        spacing: 16
        AppIcon { appId: r.app.id; size: store.t.iconRow; Layout.alignment: Qt.AlignVCenter }
        Column {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignVCenter
            spacing: 3
            Row {
                spacing: 8
                width: parent.width
                Text { id: nm; text: r.app.name; font.pointSize: store.t.fontName; font.weight: Font.DemiBold; color: r.tk.text
                       elide: Text.ElideRight; width: Math.min(implicitWidth, parent.width - (vb.visible ? 30 : 0)) }
                Sym { id: vb; visible: r.app.verified; name: "shield"; size: 17; tint: r.tk.accent
                      anchors.verticalCenter: nm.verticalCenter }
            }
            Text { width: parent.width; text: r.app.summary; font.pointSize: store.t.fontSmall; color: r.tk.text2
                   elide: Text.ElideRight; visible: text !== "" }
            Text { width: parent.width; font.pointSize: store.t.fontMeta; color: r.tk.text3; elide: Text.ElideRight
                   text: [r.meta, r.app.license].filter(function (x) { return x }).join("  ·  ")
                   visible: text !== "" }
        }
        LButton {
            visible: r.showRemove && r.app.state === "installed"
            Layout.alignment: Qt.AlignVCenter
            small: true
            text: l10n.text("Remove")
            onClicked: confirmRemove.ask(r.app.id, r.app.name)
        }
        LButton {
            visible: r.showUpdate && r.app.state === "installed"
            Layout.alignment: Qt.AlignVCenter
            small: true
            kind: "primary"
            text: l10n.text("Update")
            onClicked: store.update(r.app.id)
        }
        ActionButton {
            visible: !(r.showUpdate && r.app.state === "installed")
            Layout.alignment: Qt.AlignVCenter
            state_: r.app.state
            progress: r.app.progress
            openWhenInstalled: r.showRemove
            onInstall: store.install([r.app.id], r.app.name)
            onOpen: store.launch(r.app.id)
        }
    }
}
