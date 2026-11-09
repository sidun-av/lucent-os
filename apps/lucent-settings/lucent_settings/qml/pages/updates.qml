import QtQuick
import QtQuick.Layouts
import Lucent

// docs/mockups/03b-settings-updates
Page {
    id: page
    readonly property var st: UpdatesPage.s
    readonly property string busy: UpdatesPage.busy
    title: System.tr("Updates")
    lead: System.tr("Lucent updates as a whole, like a phone: the new version is prepared next to the current one and starts when you restart. If something goes wrong, you can go back to the previous version in one step.")
    Component.onCompleted: { UpdatesPage.refresh(); if (!page.st.appsChecked) UpdatesPage.checkApps() }

    Banner { text: UpdatesPage.error; onDismissed: UpdatesPage.clearError() }

    // .hero
    Rectangle {
        id: hero
        Layout.fillWidth: true
        Layout.topMargin: Theme.sectionTop
        implicitHeight: heroRow.implicitHeight + 56
        radius: Theme.radiusHero
        readonly property bool good: page.st.state === "uptodate" || page.st.state === "unknown" || page.st.state === "error"
        color: Theme.accentSoft
        border.color: Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.25)
        RowLayout {
            id: heroRow
            anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; leftMargin: 30; rightMargin: 30 }
            spacing: 26
            Rectangle {
                width: Theme.heroIcon; height: Theme.heroIcon; radius: Theme.radiusHeroIcon
                color: Theme.accent
                Spinner { anchors.centerIn: parent; size: 30; color: "#ffffff"; visible: page.busy === "download" || page.busy === "check" }
                Sym {
                    anchors.centerIn: parent; size: 34; color: "#ffffff"
                    visible: page.busy !== "download" && page.busy !== "check"
                    name: page.st.state === "rollback" ? "undo" : (page.st.state === "uptodate" ? "check" : (page.st.state === "unknown" || page.st.state === "error" ? "refresh" : "download"))
                }
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6
                LText {
                    Layout.fillWidth: true
                    px: Theme.fontH2; weight: Theme.weightHeading
                    text: page.busy === "download" ? System.tr("Downloading the new version…")
                        : page.busy === "check" ? System.tr("Checking for updates…")
                        : page.st.state === "staged" ? System.tr("A new version of Lucent is ready to install")
                        : page.st.state === "available" ? System.tr("A new version of Lucent is available")
                        : page.st.state === "rollback" ? System.tr("Lucent will go back to the previous version")
                        : page.st.state === "uptodate" ? System.tr("Lucent is up to date")
                        : System.tr("Check for a new version of Lucent")
                }
                LText {
                    Layout.fillWidth: true
                    px: Theme.fontBody; color: Theme.text2; wrapMode: Text.WordWrap; elide: Text.ElideNone; lineHeight: 1.2
                    text: page.busy === "download" ? System.tr("You can keep working. It's installed when you restart.")
                        : page.st.state === "staged" ? System.tr("Already downloaded · takes less than a minute when you restart · your files and apps aren't touched")
                        : page.st.state === "available" ? System.tr("Download it now; it's installed when you restart. Your files and apps aren't touched.")
                        : page.st.state === "rollback" ? System.tr("At the next restart this computer starts the version you used before. Your files and apps stay as they are.")
                        : page.st.state === "uptodate" ? System.tr("You have the newest version. Last check: {when}").replace("{when}", page.st.lastCheck || "")
                        : System.tr("Last check: {when}").replace("{when}", page.st.lastCheck || "")
                }
            }
            RowLayout {
                spacing: 12
                LButton {
                    visible: page.st.state === "staged" || page.st.state === "rollback"
                    text: System.tr("Later")
                    onClicked: UpdatesPage.toast(System.tr("It starts the next time you restart or turn on the computer."))
                }
                LButton {
                    visible: page.st.state === "staged" || page.st.state === "rollback"
                    primary: true
                    text: System.tr("Restart now")
                    onClicked: UpdatesPage.restart()
                }
                LButton {
                    visible: page.st.state === "available"
                    primary: true
                    text: System.tr("Download")
                    busy: page.busy === "download"
                    onClicked: UpdatesPage.download()
                }
                LButton {
                    visible: page.st.state === "uptodate" || page.st.state === "unknown" || page.st.state === "error"
                    primary: page.st.state !== "uptodate"
                    text: System.tr("Check now")
                    busy: page.busy === "check"
                    onClicked: UpdatesPage.check()
                }
            }
        }
    }

    GroupHeader { text: System.tr("System versions on this computer") }
    Card {
        Repeater {
            model: page.st.versions || []
            SettingRow {
                required property var modelData
                leading: Rectangle {
                    Layout.alignment: Qt.AlignTop
                    Layout.topMargin: 6
                    width: Theme.dot; height: Theme.dot; radius: Theme.dot / 2
                    color: modelData.role === "current" ? Theme.ok : (modelData.role === "previous" ? Theme.text3 : Theme.accent)
                }
                label: modelData.title
                sub: modelData.sub
                Pill {
                    visible: modelData.pill !== ""
                    text: modelData.pill
                    kind: modelData.role === "current" ? "ok" : "accent"
                }
                LButton {
                    visible: modelData.role === "previous" && page.st.canRollBack
                    icon: "undo"
                    text: System.tr("Roll back to previous version")
                    busy: page.busy === "rollback"
                    onClicked: confirmRollback.open()
                }
                LButton {
                    visible: modelData.role === "rollback"
                    text: System.tr("Cancel")
                    busy: page.busy === "rollback"
                    onClicked: UpdatesPage.rollBack()
                }
            }
        }
    }

    GroupHeader { text: System.tr("Apps") }
    Card {
        SettingRow {
            label: System.tr("App updates")
            sub: page.busy === "apps-check" ? System.tr("Checking…") : (page.st.appsText || "")
            LButton {
                visible: (page.st.apps || []).length > 0
                text: System.tr("Update apps")
                busy: page.busy === "apps"
                onClicked: UpdatesPage.updateApps()
            }
        }
    }

    GroupHeader { text: System.tr("Options") }
    Card {
        SettingRow {
            label: System.tr("Download updates automatically")
            sub: System.tr("In the background, once a day. A new version starts when you restart.")
            LSwitch { checked: page.st.autoUpdates || false; onToggled: (on) => UpdatesPage.setAuto(on) }
        }
        SettingRow {
            label: System.tr("Last check")
            LText { text: page.st.lastCheck || ""; px: Theme.fontBody; color: Theme.text2 }
            LButton { text: System.tr("Check"); busy: page.busy === "check"; onClicked: UpdatesPage.check() }
        }
    }

    LDialog {
        id: confirmRollback
        title: System.tr("Go back to the previous version?")
        text: System.tr("After a restart, this computer starts the version of Lucent you used before the last update. Your files, settings and apps are not touched. You can switch back to the newer version the same way.")
        acceptText: System.tr("Roll back")
        onAccepted: { close(); UpdatesPage.rollBack() }
    }
}
