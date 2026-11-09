// Windows programs: how Lucent Bridge works, in plain words.
import QtQuick
import QtQuick.Layouts

ScrollPage {
    id: page
    readonly property var tk: store.t
    Text {
        x: 2
        width: parent.width
        topPadding: 10
        bottomPadding: 24
        wrapMode: Text.WordWrap
        font.pointSize: store.t.fontLead
        color: page.tk.text2
        text: l10n.text("Most Windows programs install and run here with a double-click.")
    }
    BridgeHint { width: parent.width; large: true }
    Item { width: 1; height: 26 }
    Repeater {
        model: [
            { n: "1", title: l10n.text("Download the installer"),
              text: l10n.text("Get the program's installer (.exe or .msi) from its website, as you would on Windows.") },
            { n: "2", title: l10n.text("Double-click it"),
              text: l10n.text("Open your Downloads folder and double-click the file. The installer looks just like on Windows.") },
            { n: "3", title: l10n.text("Find it in the launcher"),
              text: l10n.text("The program appears in the app launcher with a small Windows badge, and opens its files on double-click.") },
        ]
        Item {
            required property var modelData
            width: parent.width
            height: stepCol.implicitHeight + 22
            Rectangle {
                id: dot
                width: 30; height: 30; radius: height / 2
                color: page.tk.accent
                Text { anchors.centerIn: parent; text: modelData.n; color: "white"; font.pointSize: store.t.fontCaption; font.weight: Font.Bold }
            }
            Column {
                id: stepCol
                anchors.left: dot.right
                anchors.leftMargin: 16
                anchors.right: parent.right
                y: 3
                spacing: 4
                Text { text: modelData.title; font.pointSize: store.t.fontName; font.weight: Font.DemiBold; color: page.tk.text }
                Text { width: parent.width; text: modelData.text; wrapMode: Text.WordWrap; font.pointSize: store.t.fontText; color: page.tk.text2 }
            }
        }
    }
    Rectangle {
        width: parent.width
        height: caveat.implicitHeight + 28
        radius: store.t.radiusField
        color: page.tk.warnSoft
        Text {
            id: caveat
            x: 16; width: parent.width - 32
            anchors.verticalCenter: parent.verticalCenter
            wrapMode: Text.WordWrap
            font.pointSize: store.t.fontSmall
            color: page.tk.text
            text: l10n.text("Not everything works: games with anti-cheat, programs that install drivers, and some copy-protected software usually don't. For those, look for an app here first.")
        }
    }
}
