import QtQuick
import QtQuick.Controls.Basic as C
import QtQuick.Layouts
import QtQuick.Window
import Lucent
import "pages"

// docs/mockups/03-settings: 340 px sidebar (account, search, sections,
// "About" in the footer) and the page on the right.
C.ApplicationWindow {
    id: win
    title: System.tr("Settings")
    visible: true
    width: Math.min(1900, Screen.desktopAvailableWidth * 0.86)
    height: Math.min(1016, Screen.desktopAvailableHeight * 0.86)
    minimumWidth: 980
    minimumHeight: 620
    color: Theme.winBg
    font.family: Theme.font
    font.pixelSize: Theme.fontBody

    property string page: System.startPage
    property string query: ""

    readonly property var sectionList: [
        { id: "network", icon: "wifi", title: System.tr("Wi-Fi & Network"),
          keys: "wifi wi-fi wlan internet network ethernet cable lan " + System.tr("internet network cable password") },
        { id: "bluetooth", icon: "bluetooth", title: System.tr("Bluetooth"),
          keys: "bluetooth headphones mouse keyboard speaker pair " + System.tr("headphones mouse speaker pair") },
        { id: "display", icon: "display", title: System.tr("Display"),
          keys: "screen monitor resolution scale size night light hdmi " + System.tr("screen resolution scale night light") },
        { id: "sound", icon: "volume", title: System.tr("Sound"),
          keys: "sound volume audio speakers microphone headphones " + System.tr("volume speakers microphone") },
        { id: "appearance", icon: "palette", title: System.tr("Appearance"),
          keys: "theme dark light mode colour color accent wallpaper background animations text size font " + System.tr("theme dark light accent wallpaper text size") },
        { id: "habits", icon: "keyboard", title: System.tr("Like Windows"),
          keys: "windows shortcuts keyboard layout language double click buttons win key " + System.tr("shortcuts keyboard layout language double-click") },
        { id: "users", icon: "users", title: System.tr("Users"),
          keys: "user account name password picture avatar " + System.tr("account name password picture") },
        { id: "updates", icon: "refresh", title: System.tr("Updates"),
          keys: "update upgrade version rollback restore apps " + System.tr("update version roll back apps") },
        { id: "winapps", icon: "winapp", title: System.tr("Windows Programs"),
          keys: "windows programs exe wine apps remove uninstall " + System.tr("programs exe remove uninstall") }
    ]

    function matches(s) {
        if (query.trim() === "") return true
        var q = query.trim().toLowerCase()
        return (s.title + " " + s.keys).toLowerCase().indexOf(q) >= 0
    }
    function open(id) {
        page = id
        query = ""
        search.text = ""
    }

    Component.onCompleted: {
        UsersPage.refresh(); NetworkPage.refresh(); UpdatesPage.refresh(); AboutPage.refresh()
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // ---------------- sidebar ----------------
        Rectangle {
            Layout.preferredWidth: Theme.sidebarWidth
            Layout.fillHeight: true
            color: Theme.winSide
            Rectangle { anchors.right: parent.right; width: 1; height: parent.height; color: Theme.line }

            ColumnLayout {
                anchors { fill: parent; topMargin: Theme.sidebarPadV; bottomMargin: Theme.sidebarPadV; leftMargin: Theme.sidebarPadH; rightMargin: Theme.sidebarPadH + 1 }
                spacing: 3

                // account
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: me.implicitHeight + 24
                    color: meMouse.containsMouse ? Theme.hover : "transparent"
                    radius: Theme.radiusControl
                    RowLayout {
                        id: me
                        anchors { left: parent.left; right: parent.right; top: parent.top; leftMargin: 10; topMargin: 8 }
                        spacing: 14
                        Avatar { size: Theme.avatarSide; source: UsersPage.s.icon || ""; initials: UsersPage.s.initials || "?" }
                        ColumnLayout {
                            spacing: 1
                            Layout.fillWidth: true
                            LText { text: UsersPage.s.name || ""; px: Theme.fontName; weight: Theme.weightH1; Layout.fillWidth: true }
                            LText {
                                text: UsersPage.s.loaded ? (UsersPage.s.admin ? System.tr("Administrator") : System.tr("Standard user")) : ""
                                px: Theme.fontSub; color: Theme.text2
                            }
                        }
                    }
                    MouseArea { id: meMouse; anchors.fill: parent; hoverEnabled: true; onClicked: win.open("users") }
                }

                // search (.search: 40 px, field, 10 px corners)
                Rectangle {
                    Layout.fillWidth: true
                    Layout.leftMargin: 2
                    Layout.rightMargin: 2
                    Layout.topMargin: 4
                    Layout.bottomMargin: 14
                    implicitHeight: Theme.controlHeight
                    radius: Theme.radiusControl
                    color: Theme.field
                    border.width: search.activeFocus ? 2 : 0
                    border.color: Theme.accent
                    RowLayout {
                        anchors { fill: parent; leftMargin: 12; rightMargin: 8 }
                        spacing: 8
                        Sym { name: "search"; size: 18; color: Theme.text3 }
                        C.TextField {
                            id: search
                            Layout.fillWidth: true
                            placeholderText: System.tr("Find a setting")
                            placeholderTextColor: Theme.text3
                            color: Theme.text
                            font.family: Theme.font
                            font.pixelSize: Theme.fontBody
                            background: null
                            leftPadding: 0
                            onTextChanged: win.query = text
                            onAccepted: {
                                for (var i = 0; i < win.sectionList.length; i++)
                                    if (win.matches(win.sectionList[i])) { win.open(win.sectionList[i].id); return }
                            }
                            Keys.onEscapePressed: text = ""
                        }
                    }
                }

                Repeater {
                    model: win.sectionList
                    SideItem {
                        required property var modelData
                        visible: win.matches(modelData)
                        icon: modelData.icon
                        tint: Theme.sq[modelData.id]
                        text: modelData.title
                        selected: win.page === modelData.id
                        value: modelData.id === "network" ? (NetworkPage.s.sideValue || "") : ""
                        count: modelData.id === "updates" ? (UpdatesPage.s.count || 0) : 0
                        onClicked: win.open(modelData.id)
                    }
                }
                LText {
                    visible: {
                        for (var i = 0; i < win.sectionList.length; i++) if (win.matches(win.sectionList[i])) return false
                        return true
                    }
                    text: System.tr("Nothing found. More settings are in Advanced settings (About).")
                    px: Theme.fontSub; color: Theme.text2; wrapMode: Text.WordWrap; elide: Text.ElideNone
                    Layout.fillWidth: true; Layout.margins: 10
                }

                Item { Layout.fillHeight: true }

                // footer: "Lucent OS 0.1 · About"
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 38
                    radius: Theme.radiusItem
                    color: win.page === "about" ? Theme.sel : (footMouse.containsMouse ? Theme.hover : "transparent")
                    RowLayout {
                        anchors { fill: parent; leftMargin: 10; rightMargin: 10 }
                        spacing: 10
                        Sym { name: "info"; size: 18; color: Theme.text2 }
                        LText {
                            text: (AboutPage.s.osName || "Lucent OS") + " · " + System.tr("About")
                            px: Theme.fontSub; color: Theme.text2; Layout.fillWidth: true
                        }
                    }
                    MouseArea { id: footMouse; anchors.fill: parent; hoverEnabled: true; onClicked: win.open("about") }
                }
            }
        }

        // ---------------- page ----------------
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Repeater {
                model: ["network", "bluetooth", "display", "sound", "appearance", "habits", "users", "updates", "winapps", "about"]
                Loader {
                    required property string modelData
                    anchors.fill: parent
                    active: win.page === modelData
                    visible: active
                    source: "pages/" + modelData + ".qml"
                }
            }
        }
    }

    // a short confirmation at the bottom ("Password changed.")
    Rectangle {
        id: toast
        property alias text: tt.text
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.horizontalCenterOffset: Theme.sidebarWidth / 2
        y: parent.height - (visible ? 76 : 0)
        visible: opacity > 0
        opacity: 0
        implicitWidth: tt.implicitWidth + 40
        implicitHeight: 44
        radius: Theme.radiusBanner
        color: Theme.toastBg
        LText { id: tt; anchors.centerIn: parent; px: Theme.fontBody; weight: 500; color: Theme.toastText }
        Behavior on opacity { NumberAnimation { duration: 180 } }
        Timer { id: toastTimer; interval: 2600; onTriggered: toast.opacity = 0 }
        function show(t) { text = t; opacity = 1; toastTimer.restart() }
    }
    Connections { target: UsersPage; function onToast(t) { toast.show(t) } }
    Connections { target: UpdatesPage; function onToast(t) { toast.show(t) } }
    Connections { target: NetworkPage; function onToast(t) { toast.show(t) } }
}
