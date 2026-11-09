// "Have a Windows installer? Just double-click it" (Lucent Bridge, no jargon).
// Compact one-liner on Home; the full text on the Windows programs page.
import QtQuick
import QtQuick.Layouts

Rectangle {
    id: h
    property bool large: false
    readonly property var tk: store.t
    radius: large ? tk.radiusCard : tk.radiusRow
    color: tk.card2
    border.width: 1
    border.color: tk.line
    implicitHeight: lay.implicitHeight + (large ? 36 : 20)
    RowLayout {
        id: lay
        x: h.large ? 22 : 16
        anchors.verticalCenter: parent.verticalCenter
        width: parent.width - 2 * x
        spacing: h.large ? 16 : 14
        Rectangle {
            width: h.large ? 52 : 36; height: width; radius: h.large ? 14 : 10
            color: h.tk.accentSoft
            Sym { anchors.centerIn: parent; name: "winapp"; size: h.large ? 28 : 20; tint: h.tk.accent }
        }
        Column {
            Layout.fillWidth: true
            spacing: 4
            Text { width: parent.width; text: l10n.text("Have a Windows installer? Just double-click it.")
                   font.pointSize: h.large ? store.t.fontName : store.t.fontText; font.weight: Font.DemiBold
                   color: h.tk.text; elide: Text.ElideRight }
            Text { width: parent.width; font.pointSize: store.t.fontSmall; color: h.tk.text2
                   wrapMode: h.large ? Text.WordWrap : Text.NoWrap; elide: Text.ElideRight
                   text: l10n.text("Most Windows programs (.exe and .msi), like Notepad++ or 7-Zip, install and run here with no extra setup. Lucent Bridge takes care of it.") }
        }
        LButton {
            visible: !h.large
            small: true
            kind: "ghost"
            text: l10n.text("How it works")
            onClicked: win.go("category:windows")
        }
    }
}
