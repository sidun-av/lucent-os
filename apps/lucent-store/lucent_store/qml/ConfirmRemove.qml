// "Remove GIMP?" — the only question the store asks.
import QtQuick
import QtQuick.Controls

Popup {
    id: p
    property string appId
    property string appName
    readonly property var tk: store.t
    function ask(id, name) { appId = id; appName = name; open() }
    parent: Overlay.overlay
    anchors.centerIn: parent
    width: 460
    modal: true
    padding: 26
    Overlay.modal: Rectangle { color: p.tk.scrim }
    background: Raised { radius: store.t.radiusPanel; lifted: true; fillTop: p.tk.winBg; fillBottom: p.tk.winBg }
    contentItem: Column {
        spacing: 10
        Text { width: parent.width; text: l10n.text("Remove {name}?").replace("{name}", p.appName)
               font.pointSize: store.t.fontDialog; font.weight: Font.Bold; color: p.tk.text; wrapMode: Text.WordWrap }
        Text { width: parent.width; wrapMode: Text.WordWrap; font.pointSize: store.t.fontText; color: p.tk.text2
               text: l10n.text("Your documents and files stay where they are. You can install it again any time.") }
        Item { width: 1; height: 10 }
        Row {
            anchors.right: parent.right
            spacing: 10
            LButton { text: l10n.text("Cancel"); onClicked: p.close() }
            LButton { kind: "danger"; text: l10n.text("Remove"); onClicked: { store.remove(p.appId); p.close() } }
        }
    }
}
