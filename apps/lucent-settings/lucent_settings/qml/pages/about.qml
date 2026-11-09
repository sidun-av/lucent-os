import QtQuick
import QtQuick.Layouts
import Lucent

Page {
    id: page
    readonly property var st: AboutPage.s
    title: System.tr("About this PC")
    lead: ""
    Component.onCompleted: AboutPage.refresh()

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
        SettingRow { label: System.tr("Computer name"); minHeight: 56; LText { text: page.st.hostname || ""; color: Theme.text2; px: Theme.fontBody } }
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
}
