import QtQuick
import QtQuick.Layouts
import Lucent

Page {
    id: page
    readonly property var st: AboutPage.s
    title: System.tr("About this PC")
    lead: ""
    Component.onCompleted: AboutPage.refresh()

    Banner { text: AboutPage.error; onDismissed: AboutPage.clearError() }

    Card {
        SettingRow {
            minHeight: 112
            label: page.st.osName || "Lucent OS"
            labelPx: Theme.fontH2
            labelWeight: Theme.weightHeading
            sub: System.tr("A calm, fast desktop. No ads, no AI, no telemetry.")
            leading: Image { source: "../lucent-logo.svg"; sourceSize: Qt.size(128, 128); Layout.preferredWidth: Theme.logo; Layout.preferredHeight: Theme.logo }
        }
    }

    Card {
        title: System.tr("This computer")
        SettingRow { label: System.tr("Model"); minHeight: 56; LText { text: page.st.model || ""; color: Theme.text2; px: Theme.fontBody } }
        SettingRow { label: System.tr("Processor"); minHeight: 56; LText { text: page.st.cpu || ""; color: Theme.text2; px: Theme.fontBody } }
        SettingRow { label: System.tr("Memory"); minHeight: 56; LText { text: page.st.memory || ""; color: Theme.text2; px: Theme.fontBody } }
        SettingRow { label: System.tr("Storage"); minHeight: 56; LText { text: page.st.storage || ""; color: Theme.text2; px: Theme.fontBody } }
        SettingRow {
            label: System.tr("Computer name")
            minHeight: 56
            LText { text: page.st.hostname || ""; color: Theme.text2; px: Theme.fontBody }
            LButton {
                text: AboutPage.busy === "rename" ? System.tr("Renaming…") : System.tr("Rename this PC")
                enabled: AboutPage.busy === "" && page.st.loaded === true
                onClicked: { nameField.text = page.st.hostname || ""; renameDialog.open(); nameField.forceActiveFocus(); nameField.selectAll() }
            }
        }
        SettingRow {
            label: System.tr("System build")
            minHeight: 56
            LText { text: (page.st.build || "") + " · " + (page.st.arch || "") + " · Linux " + (page.st.kernel || ""); color: Theme.text2; px: Theme.fontBody }
            LButton { flat: true; icon: "copy"; text: ""; implicitWidth: 40; onClicked: AboutPage.copy(page.st.osDetail + "\n" + page.st.build + " " + page.st.arch + " Linux " + page.st.kernel) }
        }
    }

    Card {
        title: System.tr("More settings")
        SettingRow {
            label: System.tr("Advanced settings…")
            sub: System.tr("KDE System Settings: everything Lucent's Settings leaves out (printers, power, mouse and touchpad, date and time, languages…)")
            clickable: true
            onClicked: AboutPage.openAdvanced()
            Sym { name: "right"; size: 18; color: Theme.text3 }
        }
        SettingRow {
            label: System.tr("Hardware details")
            sub: System.tr("Everything the system knows about this computer's parts")
            clickable: true
            onClicked: AboutPage.openHardware()
            Sym { name: "right"; size: 18; color: Theme.text3 }
        }
    }

    LDialog {
        id: renameDialog
        title: System.tr("Rename this PC")
        acceptText: System.tr("Rename")
        acceptEnabled: AboutPage.networkName(nameField.text) !== "" && nameField.text.trim() !== (page.st.hostname || "")
        onAccepted: { AboutPage.rename(nameField.text); close() }
        LText {
            text: System.tr("The name you see in Lucent and other computers see on your network.")
            px: Theme.fontSub; color: Theme.text2; wrapMode: Text.WordWrap; elide: Text.ElideNone; Layout.fillWidth: true
        }
        LTextField { id: nameField; Layout.fillWidth: true; maximumLength: 64; placeholderText: System.tr("Computer name"); onAccepted: if (renameDialog.acceptEnabled) renameDialog.accepted() }
        LText {
            readonly property string net: AboutPage.networkName(nameField.text)
            text: net === "" ? System.tr("Use at least one letter or digit.")
                             : System.tr("On the network: {name}").replace("{name}", net)
            color: net === "" ? Theme.danger : Theme.text3
            px: Theme.fontSub; Layout.fillWidth: true; elide: Text.ElideRight
        }
    }
}
