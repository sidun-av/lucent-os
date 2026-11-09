/*
    Full-screen launcher, laid out after docs/mockups/02-launcher.html
    (2560x1440 reference; geometry scales down on smaller screens, text
    sizes don't). KWin blurs what's behind the window; a light veil on top
    gives the frosted look of the mockup.

    SPDX-License-Identifier: GPL-2.0-or-later
*/
pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Effects
import QtQuick.Layouts

import org.kde.coreaddons as KCoreAddons
import org.kde.kirigami as Kirigami
import org.kde.plasma.private.kicker as Kicker

Kicker.DashboardWindow {
    id: root

    required property Kicker.RootModel rootModel
    required property Kicker.RunnerModel runnerModel
    property var pinned: []
    property bool dark: false

    // 1.0 at 1440 px tall, never below 0.72 (1080p and small laptops).
    readonly property real s: Math.max(0.72, Math.min(1.0, height / 1440, width / 2400))
    // Lucent app icons keep their tile on an 80 % grid: 128 px = the mockup's 102 px tile.
    readonly property int iconSize: Math.round(128 * s)
    readonly property int cellW: Math.round(260 * s)
    readonly property int cellH: Math.round(229 * s)
    readonly property int columns: Math.max(3, Math.min(6, Math.floor((width - 160) / cellW)))
    readonly property bool searching: search.text.length > 0
    property int category: 0          // row in rootModel; 0 = all apps

    readonly property color accent: Kirigami.Theme.highlightColor
    readonly property color textColor: dark ? "#eef0f5" : "#1b1f27"
    readonly property color text2: dark ? "#b4bac6" : "#4c5463"
    readonly property color text3: dark ? "#959cab" : "#6a7282"

    backgroundColor: "transparent"
    keyEventProxy: search

    onKeyEscapePressed: {
        if (searching) {
            search.text = ""
        } else {
            root.toggle()
        }
    }
    onActiveChanged: {
        if (!active && visible) {
            root.toggle()
        }
    }
    onVisibleChanged: {
        search.text = ""
        category = 0
        modelGeneration++
        grid.currentIndex = -1
        powerMenu.visible = false
        if (visible) {
            search.forceActiveFocus()
        }
    }

    // ---- data: kicker models -> a plain array the grid shows --------------
    onSourceModelChanged: rebuild.restart()
    // modelForRow() is a plain call: re-evaluate when the app list is rebuilt
    // (e.g. apps installed after login) and every time the launcher opens.
    property int modelGeneration: 0
    readonly property var sourceModel: {
        modelGeneration
        return searching ? (runnerModel.count > 0 ? runnerModel.modelForRow(0) : null)
                         : rootModel.modelForRow(category)
    }
    property var entries: []

    // Apps whose icons come from the Lucent icon theme: drawn on an 80 % grid.
    // Other themes' icons are full-bleed, so they're shown at 80 % to match.
    readonly property var lucentTiles: ["org.kde.dolphin.desktop", "org.mozilla.firefox.desktop",
        "org.onlyoffice.desktopeditors.desktop", "org.kde.okular.desktop",
        "com.github.jeromerobert.pdfarranger.desktop", "org.gimp.GIMP.desktop", "org.kde.krita.desktop",
        "org.inkscape.Inkscape.desktop", "org.darktable.Darktable.desktop", "org.kde.kdenlive.desktop",
        "org.lucent.Settings.desktop", "org.lucent.Store.desktop", "org.kde.konsole.desktop",
        "org.lucent.Migrate.desktop", "org.kde.ark.desktop", "org.kde.filelight.desktop",
        "org.kde.kdeconnect.app.desktop", "org.kde.kwrite.desktop", "org.kde.spectacle.desktop",
        "org.kde.plasma-systemmonitor.desktop", "net.scribus.Scribus.desktop", "org.lucent.NextGen.desktop"]

    // Plain names for the apps a newcomer looks for (the mockups' wording);
    // everything else keeps the app's own name.
    readonly property var friendlyNames: ({
        "org.kde.dolphin.desktop": i18n("Files"),
        "org.gimp.GIMP.desktop": "GIMP",
        "org.kde.konsole.desktop": i18n("Terminal"),
        "org.lucent.Store.desktop": i18n("Store"),
        "org.lucent.Settings.desktop": i18n("Settings"),
        "org.lucent.Migrate.desktop": i18n("Move from Windows"),
        "org.kde.ark.desktop": i18n("Archives"),
        "org.kde.filelight.desktop": i18n("Disk Usage"),
        "org.kde.kwrite.desktop": i18n("Text Editor"),
        "org.kde.spectacle.desktop": i18n("Screenshot"),
    })

    function launch(i) {
        const e = entries[i]
        if (e && sourceModel) {
            sourceModel.trigger(e.row, "", null)
            root.toggle()
        }
    }

    mainItem: MouseArea {
        id: rootItem
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        Instantiator {
            id: collector
            model: root.visible ? root.sourceModel : null
            delegate: QtObject {
                required property int index
                required property var model
                readonly property string name: model.display ?? ""
                readonly property var icon: model.decoration
                readonly property string id: String(model.favoriteId ?? "").replace("applications:", "")
            }
            onObjectAdded: rebuild.restart()
            onObjectRemoved: rebuild.restart()
        }
        Timer {
            id: rebuild
            interval: 0
            onTriggered: {
                const out = []
                for (let i = 0; i < collector.count; ++i) {
                    const o = collector.objectAt(i)
                    if (o && o.name.length > 0) {
                        out.push({ name: root.friendlyNames[o.id] || o.name, icon: o.icon, id: o.id, row: o.index })
                    }
                }
                if (!root.searching && root.category === 0) {
                    const rank = id => { const i = root.pinned.indexOf(id); return i < 0 ? 1000 : i }
                    out.sort((a, b) => (rank(a.id) - rank(b.id)) || a.name.localeCompare(b.name))
                }
                root.entries = out
                grid.currentIndex = root.searching && out.length > 0 ? 0 : -1
            }
        }

        Connections {
            target: root.rootModel
            function onRefreshed() { root.modelGeneration++ }
            function onCountChanged() { root.modelGeneration++ }
        }
        KCoreAddons.KUser { id: kuser }

        onClicked: mouse => {
            if (powerMenu.visible) {
                powerMenu.visible = false
            } else {
                root.toggle()
            }
        }

        Rectangle {
            anchors.fill: parent
            color: root.dark ? Qt.rgba(16 / 255, 18 / 255, 26 / 255, 0.62) : Qt.rgba(246 / 255, 248 / 255, 252 / 255, 0.58)
        }

        // ---- user + power, top right ----------------------------------------
        RowLayout {
            anchors.top: parent.top
            anchors.right: parent.right
            anchors.topMargin: 40
            anchors.rightMargin: 48
            spacing: 14

            Rectangle {
                Layout.preferredWidth: 42
                Layout.preferredHeight: 42
                radius: 21
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0; color: "#ffb37a" }
                    GradientStop { position: 1; color: "#f2668b" }
                }
                Text {
                    anchors.centerIn: parent
                    visible: face.status !== Image.Ready
                    text: (kuser.fullName || kuser.loginName).charAt(0).toUpperCase()
                    color: "white"
                    font.pixelSize: 17
                    font.weight: Font.Bold
                }
                Image {
                    id: face
                    anchors.fill: parent
                    source: kuser.faceIconUrl
                    visible: false
                    sourceSize: Qt.size(84, 84)
                    fillMode: Image.PreserveAspectCrop
                }
                MultiEffect {
                    anchors.fill: parent
                    source: face
                    visible: face.status === Image.Ready
                    maskEnabled: true
                    maskSource: faceMask
                }
                Rectangle { id: faceMask; anchors.fill: parent; radius: 21; visible: false; layer.enabled: true }
            }
            Text {
                text: kuser.fullName || kuser.loginName
                color: root.textColor
                font.pixelSize: 16
                font.weight: Font.DemiBold
            }
            MouseArea {
                id: powerButton
                Layout.preferredWidth: 42
                Layout.preferredHeight: 42
                hoverEnabled: true
                Accessible.role: Accessible.Button
                Accessible.name: i18n("Power")
                onClicked: powerMenu.visible = !powerMenu.visible
                Rectangle {
                    anchors.fill: parent
                    radius: 21
                    color: root.dark ? Qt.rgba(1, 1, 1, powerButton.containsMouse ? 0.16 : 0.08)
                                     : Qt.rgba(1, 1, 1, powerButton.containsMouse ? 0.85 : 0.55)
                    border.width: 1
                    border.color: root.dark ? Qt.rgba(1, 1, 1, 0.12) : Qt.rgba(1, 1, 1, 0.8)
                }
                Kirigami.Icon {
                    anchors.centerIn: parent
                    width: 20
                    height: 20
                    source: "system-shutdown-symbolic"
                    isMask: true
                    color: root.textColor
                }
            }
        }

        // power menu
        Rectangle {
            id: powerMenu
            visible: false
            z: 10
            anchors.top: parent.top
            anchors.right: parent.right
            anchors.topMargin: 92
            anchors.rightMargin: 48
            width: 220
            height: powerColumn.implicitHeight + 16
            radius: 14
            color: root.dark ? "#22252d" : "#fafbfd"
            border.width: 1
            border.color: root.dark ? Qt.rgba(1, 1, 1, 0.12) : Qt.rgba(20 / 255, 28 / 255, 45 / 255, 0.10)
            layer.enabled: true
            layer.effect: MultiEffect {
                shadowEnabled: true
                shadowColor: Qt.rgba(10 / 255, 15 / 255, 30 / 255, 0.25)
                shadowBlur: 0.8
                shadowVerticalOffset: 10
            }
            MouseArea { anchors.fill: parent }      // swallow clicks
            ColumnLayout {
                id: powerColumn
                anchors.fill: parent
                anchors.margins: 8
                spacing: 2
                Repeater {
                    model: root.rootModel.systemFavoritesModel
                    delegate: MouseArea {
                        id: pItem
                        required property int index
                        required property var model
                        Layout.fillWidth: true
                        Layout.preferredHeight: 40
                        hoverEnabled: true
                        onClicked: {
                            powerMenu.visible = false
                            root.rootModel.systemFavoritesModel.trigger(index, "", null)
                            root.toggle()
                        }
                        Rectangle {
                            anchors.fill: parent
                            radius: 9
                            color: pItem.containsMouse ? (root.dark ? Qt.rgba(1, 1, 1, 0.07) : Qt.rgba(20 / 255, 28 / 255, 45 / 255, 0.06)) : "transparent"
                        }
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 10
                            spacing: 12
                            Kirigami.Icon {
                                Layout.preferredWidth: 20
                                Layout.preferredHeight: 20
                                source: pItem.model.decoration
                            }
                            Text {
                                Layout.fillWidth: true
                                text: pItem.model.display ?? ""
                                color: root.textColor
                                font.pixelSize: 15
                            }
                        }
                    }
                }
            }
        }

        // ---- search field ----------------------------------------------------
        Item {
            id: searchBox
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: Math.round(150 * root.s)
            width: Math.min(760, parent.width - 96)
            height: 64

            Rectangle {      // focus ring: 0 0 0 3px accent/.35
                anchors.fill: parent
                anchors.margins: -3
                radius: 23
                color: "transparent"
                border.width: 3
                border.color: Qt.rgba(root.accent.r, root.accent.g, root.accent.b, 0.35)
            }
            Rectangle {
                anchors.fill: parent
                radius: 20
                color: root.dark ? Qt.rgba(40 / 255, 44 / 255, 54 / 255, 0.92) : Qt.rgba(1, 1, 1, 0.9)
                border.width: 1
                border.color: root.accent
                layer.enabled: true
                layer.effect: MultiEffect {
                    shadowEnabled: true
                    shadowColor: Qt.rgba(20 / 255, 30 / 255, 60 / 255, 0.12)
                    shadowBlur: 0.7
                    shadowVerticalOffset: 10
                }
            }
            Kirigami.Icon {
                id: searchIcon
                anchors.left: parent.left
                anchors.leftMargin: 22
                anchors.verticalCenter: parent.verticalCenter
                width: 24
                height: 24
                source: "search-symbolic"
                isMask: true
                color: root.accent
            }
            TextInput {
                id: search
                anchors.left: searchIcon.right
                anchors.leftMargin: 14
                anchors.right: parent.right
                anchors.rightMargin: 22
                anchors.verticalCenter: parent.verticalCenter
                font.pixelSize: 19
                color: root.textColor
                selectionColor: root.accent
                cursorDelegate: Rectangle { width: 2; color: root.accent; radius: 1 }
                focus: true
                clip: true
                onTextChanged: root.runnerModel.query = text
                Keys.onDownPressed: grid.focusGrid()
                Keys.onTabPressed: grid.focusGrid()
                Keys.onReturnPressed: root.launch(Math.max(grid.currentIndex, 0))
                Keys.onEnterPressed: root.launch(Math.max(grid.currentIndex, 0))
                Text {
                    anchors.fill: parent
                    verticalAlignment: Text.AlignVCenter
                    visible: search.text.length === 0
                    text: i18n("Search apps, files and settings")
                    color: root.text3
                    font.pixelSize: 19
                    elide: Text.ElideRight
                }
            }
        }

        // ---- category chips --------------------------------------------------
        Row {
            id: chips
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: searchBox.bottom
            anchors.topMargin: 30
            spacing: 10
            opacity: root.searching ? 0 : 1
            visible: opacity > 0
            Behavior on opacity { NumberAnimation { duration: Kirigami.Units.shortDuration } }

            Repeater {
                model: root.rootModel
                delegate: MouseArea {
                    id: chip
                    required property int index
                    required property var model
                    readonly property bool on: root.category === index
                    readonly property string label: index === 0 ? i18n("All apps") : (model.display ?? "")
                    width: visible ? chipRow.implicitWidth + 36 : 0
                    height: 40
                    hoverEnabled: true
                    // Categories with one or two apps (Help...) aren't worth a chip.
                    visible: label.length > 0 && (index === 0 || (root.rootModel.modelForRow(index)?.count ?? 0) > 2)
                    onClicked: { root.category = index; search.forceActiveFocus() }

                    Rectangle {
                        anchors.fill: parent
                        radius: 20
                        color: chip.on ? root.textColor
                                       : (root.dark ? Qt.rgba(1, 1, 1, chip.containsMouse ? 0.14 : 0.08)
                                                    : Qt.rgba(1, 1, 1, chip.containsMouse ? 0.75 : 0.45))
                        border.width: chip.on ? 0 : 1
                        border.color: root.dark ? Qt.rgba(1, 1, 1, 0.12) : Qt.rgba(1, 1, 1, 0.7)
                    }
                    Row {
                        id: chipRow
                        anchors.centerIn: parent
                        spacing: 8
                        Kirigami.Icon {
                            anchors.verticalCenter: parent.verticalCenter
                            width: 18
                            height: 18
                            source: chip.index === 0 ? "view-app-grid-symbolic" : chip.model.decoration
                            isMask: true    // one-colour glyphs, readable in light and dark
                            color: chip.on ? (root.dark ? "#1b1f27" : "white") : root.text2
                        }
                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            text: chip.label
                            color: chip.on ? (root.dark ? "#1b1f27" : "white") : root.textColor
                            font.pointSize: 11.625
                            font.weight: Font.Medium
                        }
                    }
                }
            }
        }

        // ---- app grid ----------------------------------------------------------
        GridView {
            id: grid
            anchors.top: chips.bottom
            anchors.topMargin: Math.round(110 * root.s) - Math.round(root.cellH - root.iconSize - 70 * root.s) / 2
            // whole rows only, so no half-cut icons peek in at the bottom
            height: Math.max(1, Math.floor((hints.y - 24 - y) / root.cellH)) * root.cellH
            anchors.horizontalCenter: parent.horizontalCenter
            width: root.cellW * root.columns
            cellWidth: root.cellW
            cellHeight: root.cellH
            clip: true
            model: root.entries
            keyNavigationWraps: false
            highlightFollowsCurrentItem: false
            boundsBehavior: Flickable.StopAtBounds
            focus: false

            function focusGrid() {
                if (count > 0) {
                    if (currentIndex < 0) currentIndex = 0
                    forceActiveFocus()
                }
            }
            Keys.onReturnPressed: root.launch(currentIndex)
            Keys.onEnterPressed: root.launch(currentIndex)
            Keys.onUpPressed: event => {
                if (currentIndex < root.columns) { search.forceActiveFocus() } else { moveCurrentIndexUp() }
            }
            Keys.onPressed: event => {
                if (event.text.length > 0 && event.modifiers === Qt.NoModifier && event.key !== Qt.Key_Return) {
                    search.forceActiveFocus()
                    search.text += event.text
                    event.accepted = true
                }
            }

            delegate: MouseArea {
                id: cell
                required property int index
                required property var modelData
                width: root.cellW
                height: root.cellH
                hoverEnabled: true
                acceptedButtons: Qt.LeftButton
                readonly property bool lit: containsMouse || (grid.currentIndex === index && (grid.activeFocus || root.searching))
                onClicked: root.launch(index)

                Rectangle {     // hover/focus: rgba(255,255,255,.55), radius 30, -10 px around the icon
                    x: (parent.width - width) / 2
                    y: 6 + root.iconSize * 0.1 - 10
                    width: root.iconSize * 0.8 + 20
                    height: root.iconSize * 0.8 + 20
                    radius: 30
                    color: root.dark ? Qt.rgba(1, 1, 1, 0.10) : Qt.rgba(1, 1, 1, 0.55)
                    border.width: 1
                    border.color: root.dark ? Qt.rgba(1, 1, 1, 0.16) : Qt.rgba(1, 1, 1, 0.9)
                    opacity: cell.lit ? 1 : 0
                    Behavior on opacity { NumberAnimation { duration: Kirigami.Units.shortDuration } }
                }
                Kirigami.Icon {
                    id: appIcon
                    readonly property real k: root.lucentTiles.indexOf(cell.modelData.id) >= 0 ? 1.0 : 0.8
                    x: (parent.width - width) / 2
                    y: 6 + root.iconSize * (1 - k) / 2
                    width: Math.round(root.iconSize * k)
                    height: Math.round(root.iconSize * k)
                    source: cell.modelData.icon
                    roundToIconSize: false
                    visible: false
                }
                MultiEffect {   // drop-shadow(0 8px 16px rgba(20,30,60,.16))
                    anchors.fill: appIcon
                    source: appIcon
                    shadowEnabled: true
                    shadowColor: Qt.rgba(20 / 255, 30 / 255, 60 / 255, root.dark ? 0.45 : 0.18)
                    shadowBlur: 0.6
                    shadowVerticalOffset: 8
                    autoPaddingEnabled: true
                }
                // Windows program (a launcher entry lucent-bridge wrote after
                // an installer): the mockup's badge, bottom-right on the tile
                // (.badge: 36 px, -6 px out, radius 11, #2a303c, 3 px ring).
                Rectangle {
                    readonly property real u: root.iconSize / 128      // mockup px
                    readonly property real tile: root.iconSize * 0.8
                    visible: /(^|[:\/])lucent-bridge-[^\/]*\.desktop$/.test(cell.modelData.id)
                    width: Math.round(42 * u)
                    height: width
                    x: (cell.width + tile) / 2 + 9 * u - width
                    y: 6 + root.iconSize * 0.1 + tile + 9 * u - height
                    radius: 14 * u
                    color: root.dark ? "#1b1f27" : Qt.rgba(1, 1, 1, 0.95)
                    Rectangle {
                        anchors.centerIn: parent
                        width: parent.width - 6 * parent.u
                        height: width
                        radius: 11 * parent.u
                        color: "#2a303c"
                        Item {  // lucent.js "winapp": 24-unit glyph drawn at 20 px
                            readonly property real v: 20 * parent.parent.u / 24
                            anchors.centerIn: parent
                            width: 24 * v
                            height: 24 * v
                            Rectangle {
                                x: 3.5 * parent.v - border.width / 2
                                y: 4.5 * parent.v - border.width / 2
                                width: 17 * parent.v + border.width
                                height: 15 * parent.v + border.width
                                radius: 2.5 * parent.v
                                color: "transparent"
                                border.color: "white"
                                border.width: Math.max(1, 1.7 * parent.v)
                            }
                            Rectangle {
                                x: 3.5 * parent.v
                                y: 9 * parent.v - height / 2
                                width: 17 * parent.v
                                height: Math.max(1, 1.7 * parent.v)
                                color: "white"
                            }
                            Repeater {
                                model: [6.6, 8.8]
                                Rectangle {
                                    required property real modelData
                                    x: (modelData - 0.75) * parent.v
                                    y: (6.8 - 0.75) * parent.v
                                    width: 1.5 * parent.v
                                    height: width
                                    radius: width / 2
                                    color: "white"
                                }
                            }
                        }
                    }
                }
                Text {
                    y: 6 + root.iconSize * 0.9 + 16
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: Math.round(220 * root.s)
                    horizontalAlignment: Text.AlignHCenter
                    text: cell.modelData.name
                    color: root.textColor
                    font.pointSize: 12.375
                    font.weight: Font.Medium
                    lineHeight: 1.3
                    wrapMode: Text.Wrap
                    maximumLineCount: 2
                    elide: Text.ElideRight
                }
            }
        }

        Text {
            anchors.centerIn: grid
            visible: root.searching && grid.count === 0 && !root.runnerModel.querying
            text: i18n("Nothing found")
            color: root.text2
            font.pixelSize: 17
        }

        // ---- key hints ---------------------------------------------------------
        Row {
            id: hints
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: Math.round(64 * root.s)
            spacing: 34

            component Kbd: Rectangle {
                property alias label: kbdText.text
                width: kbdText.implicitWidth + 18
                height: kbdText.implicitHeight + 8
                radius: 7
                color: root.dark ? Qt.rgba(1, 1, 1, 0.10) : Qt.rgba(1, 1, 1, 0.8)
                border.width: 1
                border.color: root.dark ? Qt.rgba(1, 1, 1, 0.15) : Qt.rgba(20 / 255, 28 / 255, 45 / 255, 0.16)
                Rectangle {   // border-bottom 2.5px
                    anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom
                    anchors.leftMargin: 3; anchors.rightMargin: 3
                    height: 1.5
                    color: parent.border.color
                }
                Text {
                    id: kbdText
                    anchors.centerIn: parent
                    anchors.verticalCenterOffset: -1
                    color: root.textColor
                    font.pixelSize: 14
                    font.weight: Font.DemiBold
                }
            }
            component Hint: Text {
                anchors.verticalCenter: parent.verticalCenter
                color: root.text2
                font.pointSize: 11.625
            }

            Row {
                spacing: 10
                Kbd { label: "⊞ Win" }
                Hint { text: i18n("open or close this menu") }
            }
            Hint { text: i18n("Just start typing — search is ready") }
            Row {
                spacing: 10
                Kbd { label: "Esc" }
                Hint { text: i18n("close") }
            }
        }
    }
}
