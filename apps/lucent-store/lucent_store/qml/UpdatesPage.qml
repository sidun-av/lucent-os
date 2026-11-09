import QtQuick
import QtQuick.Layouts

ScrollPage {
    id: page
    readonly property var ups: store.updates(win.rev)
    readonly property int shared: store.sharedUpdates(win.rev)
    readonly property var tk: store.t

    Item { width: 1; height: 10 }
    Rectangle {
        width: parent.width
        height: 84
        radius: store.t.radiusRow
        color: page.tk.card
        border.width: 1
        border.color: page.tk.line
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 22
            anchors.rightMargin: 22
            spacing: 16
            Rectangle {
                width: 44; height: 44; radius: height / 2
                color: page.ups.length > 0 ? page.tk.accentSoft : page.tk.okSoft
                Sym { anchors.centerIn: parent; size: 22
                      name: page.ups.length > 0 ? "refresh" : "check"
                      tint: page.ups.length > 0 ? page.tk.accent : page.tk.ok }
            }
            Column {
                Layout.fillWidth: true
                spacing: 3
                Text {
                    font.pointSize: store.t.fontTitle; font.weight: Font.DemiBold; color: page.tk.text
                    text: store.updatesState === "checking" ? l10n.text("Checking for updates…")
                        : page.ups.length > 0 ? l10n.plural("{n} app update", "{n} app updates", page.ups.length)
                        : page.shared > 0 ? l10n.text("Shared app components can be updated")
                        : store.updatesState === "failed" ? l10n.text("Couldn't check for updates")
                        : l10n.text("All apps are up to date")
                }
                Text {
                    font.pointSize: store.t.fontSmall; color: page.tk.text2
                    text: store.updatesState === "failed" ? l10n.text("Check the internet connection and try again.")
                        : page.shared > 0 ? l10n.plural("Also {n} shared component that apps use.", "Also {n} shared components that apps use.", page.shared)
                        : l10n.text("Apps from Flathub update here.")
                }
            }
            LButton {
                visible: page.ups.length > 0 || page.shared > 0
                kind: "primary"
                text: l10n.text("Update all")
                onClicked: store.updateAll()
            }
            LButton {
                visible: page.ups.length === 0 && page.shared === 0
                text: l10n.text("Check again")
                enabledLook: store.updatesState !== "checking"
                onClicked: store.checkUpdates()
            }
        }
    }
    Item { width: 1; height: 16 }
    AppGrid {
        width: parent.width
        apps: page.ups
        showUpdate: true
        metaFor: function (a) {
            return [a.version ? l10n.text("Version {v}").replace("{v}", a.version) : "", a.download]
                .filter(function (x) { return x }).join("  ·  ")
        }
    }
    Item { width: 1; height: 28 }
    Rectangle {
        width: parent.width
        height: 76
        radius: store.t.radiusRow
        color: page.tk.card2
        border.width: 1
        border.color: page.tk.line
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 22
            anchors.rightMargin: 22
            spacing: 16
            Sym { name: "shield"; size: 24; tint: page.tk.accent }
            Column {
                Layout.fillWidth: true
                spacing: 3
                Text { font.pointSize: store.t.fontLead; font.weight: Font.DemiBold; color: page.tk.text
                       text: l10n.text("Lucent itself updates in Settings") }
                Text { width: parent.width; font.pointSize: store.t.fontSmall; color: page.tk.text2; wrapMode: Text.WordWrap
                       text: l10n.text("System updates install in the background and apply at the next restart.") }
            }
            LButton { text: l10n.text("Open Settings"); onClicked: store.openSystemUpdates() }
        }
    }
}
