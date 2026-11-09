import QtQuick

Rectangle {
    readonly property var tk: store.t
    height: 24
    width: t.implicitWidth + 16
    radius: store.t.radiusBadge
    color: tk.alphaBg
    border.width: 1
    border.color: tk.alphaLine
    Text {
        id: t
        anchors.centerIn: parent
        text: l10n.text("alpha").toUpperCase()
        font.pointSize: store.t.fontBadge
        font.weight: Font.Bold
        font.letterSpacing: 0.5
        color: parent.tk.alphaText
    }
}
