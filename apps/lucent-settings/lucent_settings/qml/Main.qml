import QtQuick
import QtQuick.Controls.Basic as C
import QtQuick.Layouts
import QtQuick.Window
import Lucent
import "pages"

// Pebble Drift structure (docs/mockups/concepts-2026/pebble-drift/04-settings):
// one header row (app icon, title, back / forward, centred search, window
// buttons), then a floating glass sidebar card (account, sections) and the page of
// cards. The window is frameless and draws that row itself with the shared
// org.lucent.chrome module (chrome/Frame.qml); without the module
// (System.frameless false) KWin's title bar sits above a row without them.
C.ApplicationWindow {
    id: win
    title: System.tr("Settings")
    visible: true
    width: Math.min(1840, Screen.desktopAvailableWidth * 0.86)
    height: Math.min(1116, Screen.desktopAvailableHeight * 0.88)
    minimumWidth: 1000
    minimumHeight: 640
    flags: System.frameless ? (Qt.Window | Qt.FramelessWindowHint) : Qt.Window
    color: System.frameless ? "transparent" : Theme.surface
    font.family: Theme.font
    font.pixelSize: Theme.fontBody

    property string page: System.startPage
    property string query: ""
    property var back: []
    property var forward: []

    readonly property var sectionList: [
        { id: "network", icon: "wifi", title: System.tr("Network & internet"),
          keys: "wifi wi-fi wlan internet network ethernet cable lan " + System.tr("internet network cable password") },
        { id: "bluetooth", icon: "bluetooth", title: System.tr("Bluetooth & devices"),
          keys: "bluetooth headphones mouse keyboard speaker pair " + System.tr("headphones mouse speaker pair") },
        { id: "display", icon: "display", title: System.tr("Display"),
          keys: "screen monitor resolution scale size night light hdmi " + System.tr("screen resolution scale night light") },
        { id: "sound", icon: "volume", title: System.tr("Sound"),
          keys: "sound volume audio speakers microphone headphones " + System.tr("volume speakers microphone") },
        { id: "appearance", icon: "palette", title: System.tr("Appearance"),
          keys: "theme dark light mode colour color accent wallpaper background animations text size font " + System.tr("theme dark light accent wallpaper text size") },
        { id: "wallpaper", icon: "image", title: System.tr("Wallpaper"),
          keys: "wallpaper background picture desktop " + System.tr("wallpaper background picture") },
        { id: "habits", icon: "winapp", title: System.tr("Like Windows"),
          keys: "windows shortcuts double click buttons win key alt tab " + System.tr("shortcuts double-click window buttons") },
        { id: "keyboard", icon: "keyboard", title: System.tr("Keyboard & language"),
          keys: "keyboard layout language russian english switch alt shift " + System.tr("keyboard layout language") },
        { id: "winapps", icon: "apps", title: System.tr("Windows apps"),
          keys: "windows programs exe wine apps remove uninstall " + System.tr("programs exe remove uninstall") },
        { id: "updates", icon: "refresh", title: System.tr("Updates"),
          keys: "update upgrade version rollback restore apps " + System.tr("update version roll back apps") },
        { id: "users", icon: "users", title: System.tr("Users"),
          keys: "user account name password picture avatar " + System.tr("account name password picture") },
        { id: "about", icon: "info", title: System.tr("About this PC"),
          keys: "about version computer hardware memory processor advanced kde system settings " + System.tr("version computer hardware advanced") }
    ]

    function matches(s) {
        if (query.trim() === "") return true
        var q = query.trim().toLowerCase()
        return (s.title + " " + s.keys).toLowerCase().indexOf(q) >= 0
    }
    function open(id) {
        if (id !== page) {
            back = back.concat([page])
            forward = []
        }
        page = id
        search.text = ""
    }
    function goBack() {
        if (!back.length) return
        forward = forward.concat([page])
        page = back[back.length - 1]
        back = back.slice(0, -1)
    }
    function goForward() {
        if (!forward.length) return
        back = back.concat([page])
        page = forward[forward.length - 1]
        forward = forward.slice(0, -1)
    }

    Component.onCompleted: {
        if (System.frameless)
            chrome.setSource("chrome/Frame.qml", { win: win, leftSlot: leftSlot, rightSlot: rightSlot, overlay: overlay })
        UsersPage.refresh(); NetworkPage.refresh(); UpdatesPage.refresh(); AboutPage.refresh(); AppearancePage.refresh()
    }
    Shortcut { sequences: [StandardKey.Back]; onActivated: win.goBack() }
    Shortcut { sequences: [StandardKey.Forward]; onActivated: win.goForward() }
    Shortcut { sequences: [StandardKey.Find]; onActivated: search.forceActiveFocus() }

    // frameless: surface, shadow, window buttons, title-bar behaviour
    Loader { id: chrome; anchors.fill: parent }

    // fine grain over the matte surface
    Image {
        visible: !System.frameless
        anchors.fill: parent
        source: "Lucent/grain.png"
        fillMode: Image.Tile
        opacity: Theme.grainOpacity
        smooth: false
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // ---------------- header row ----------------
        Item {
            id: header
            Layout.fillWidth: true
            Layout.preferredHeight: System.frameless ? Theme.headerHeightFrameless : Theme.headerHeight
            RowLayout {
                id: leftRow
                anchors { left: parent.left; verticalCenter: parent.verticalCenter
                          leftMargin: System.frameless ? 12 : Theme.bodyPad + 4 }
                spacing: 2
                Item {      // window buttons kwinrc puts on the left (Lucent: the app icon = window menu)
                    id: leftSlot
                    visible: System.frameless && children.length > 0 && !children[0].empty
                    implicitWidth: children.length ? children[0].implicitWidth : 0
                    implicitHeight: 36
                    Layout.rightMargin: 4
                }
                LText {
                    visible: System.frameless
                    text: win.title
                    px: Theme.fontWindowTitle; weight: 700
                    Layout.leftMargin: leftSlot.visible ? 2 : 4
                }
                Rectangle {
                    visible: System.frameless
                    implicitWidth: 1; implicitHeight: 26; color: Theme.lineStrong
                    Layout.leftMargin: 14; Layout.rightMargin: 14
                }
                LButton { flat: true; icon: "left"; text: ""; enabled: win.back.length > 0; onClicked: win.goBack() }
                LButton { flat: true; icon: "right"; text: ""; enabled: win.forward.length > 0; onClicked: win.goForward() }
            }
            C.TextField {
                id: search
                anchors.centerIn: parent
                width: Math.min(Theme.searchWidth, parent.width - 2 * Math.max(leftRow.width + 12, rightSlot.width + 12) - 48)
                height: Theme.fieldHeight
                leftPadding: 42
                rightPadding: 14
                placeholderText: System.tr("Find a setting")
                placeholderTextColor: Theme.text3
                color: Theme.text
                font.family: Theme.font
                font.pixelSize: Theme.fontBody
                onTextChanged: win.query = text
                onAccepted: {
                    for (var i = 0; i < win.sectionList.length; i++)
                        if (win.matches(win.sectionList[i])) { win.open(win.sectionList[i].id); return }
                }
                Keys.onEscapePressed: text = ""
                background: Item {
                    Rectangle {
                        anchors.fill: parent; anchors.margins: -6
                        radius: Theme.radiusControl + 6; color: Theme.accentSoft; visible: search.activeFocus
                    }
                    Rectangle {
                        anchors.fill: parent; anchors.margins: -2
                        radius: Theme.radiusControl + 2; color: Theme.accent; visible: search.activeFocus
                    }
                    Rectangle { anchors.fill: parent; radius: Theme.radiusControl; color: Theme.raised; visible: search.activeFocus }
                    Well { anchors.fill: parent; visible: !search.activeFocus; tint: Theme.glassField }
                    Sym { x: 14; anchors.verticalCenter: parent.verticalCenter; name: "search"; size: 18; color: Theme.text2 }
                }
            }
            Item {          // minimise / maximise / close (kwinrc order)
                id: rightSlot
                visible: System.frameless
                anchors { right: parent.right; verticalCenter: parent.verticalCenter; rightMargin: 12 }
                width: children.length ? children[0].implicitWidth : 0
                height: 36
            }
        }

        // ---------------- body ----------------
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.leftMargin: Theme.bodyPad
            Layout.rightMargin: Theme.bodyPad
            Layout.bottomMargin: Theme.bodyPad
            spacing: Theme.bodyPad

            // the sidebar: a floating glass card (tier 1: painted over the
            // window's own surface, no wallpaper blur behind it)
            Well {
                tint: Theme.glassSidebar
                Layout.preferredWidth: Theme.sidebarWidth
                Layout.fillHeight: true
                radius: Theme.radiusCard

                ColumnLayout {
                    anchors { fill: parent; topMargin: Theme.sidebarPadV; bottomMargin: Theme.sidebarPadV
                              leftMargin: Theme.sidebarPadH; rightMargin: Theme.sidebarPadH }
                    spacing: 1

                    // account (.me), a hairline under it
                    Item {
                        Layout.fillWidth: true
                        implicitHeight: me.implicitHeight + 20
                        Layout.bottomMargin: 6
                        Rectangle { anchors.fill: parent; anchors.bottomMargin: 1; radius: Theme.radiusItem; color: Theme.hover; visible: meMouse.containsMouse }
                        RowLayout {
                            id: me
                            anchors { left: parent.left; right: parent.right; top: parent.top; leftMargin: 8; topMargin: 6 }
                            spacing: 12
                            Avatar { size: Theme.avatarSide; source: UsersPage.s.icon || ""; initials: UsersPage.s.initials || "?" }
                            ColumnLayout {
                                spacing: 1
                                Layout.fillWidth: true
                                LText { text: UsersPage.s.name || ""; px: Theme.fontName; weight: Theme.weightCardTitle; Layout.fillWidth: true }
                                LText {
                                    text: UsersPage.s.loaded ? (UsersPage.s.admin ? System.tr("Administrator") : System.tr("Standard user")) : ""
                                    px: Theme.fontSub; color: Theme.text2
                                }
                            }
                        }
                        Rectangle { anchors { left: parent.left; right: parent.right; bottom: parent.bottom } height: 1; color: Theme.line }
                        MouseArea { id: meMouse; anchors.fill: parent; hoverEnabled: true; onClicked: win.open("users") }
                    }

                    Repeater {
                        model: win.sectionList
                        SideItem {
                            required property var modelData
                            visible: win.matches(modelData)
                            icon: modelData.icon
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
                        text: System.tr("Nothing found. More settings are in Advanced settings (About this PC).")
                        px: Theme.fontSub; color: Theme.text2; wrapMode: Text.WordWrap; elide: Text.ElideNone
                        Layout.fillWidth: true; Layout.margins: 10
                    }
                    Item { Layout.fillHeight: true }
                }
            }

            // page
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Repeater {
                    model: ["network", "bluetooth", "display", "sound", "appearance", "wallpaper", "habits", "keyboard",
                            "winapps", "updates", "users", "about"]
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
    // frameless: the resize edges, over everything
    Item { id: overlay; anchors.fill: parent; z: 1000 }

    Connections { target: UsersPage; function onToast(t) { toast.show(t) } }
    Connections { target: UpdatesPage; function onToast(t) { toast.show(t) } }
    Connections { target: NetworkPage; function onToast(t) { toast.show(t) } }
    Connections { target: AboutPage; function onToast(t) { toast.show(t) } }
}
