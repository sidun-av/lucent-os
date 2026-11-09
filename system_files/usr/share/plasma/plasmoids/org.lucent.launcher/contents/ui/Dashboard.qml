/*
    Full-screen launcher in Pebble Drift
    (docs/mockups/concepts-2026/pebble-drift/03-launcher.html, 2560x1440
    reference; geometry scales down on smaller screens, text sizes don't):
    a near-opaque matte scrim (--surface-scrim, light blur only), the raised
    68 px query field with the focus ring, a sunken segmented track for the
    categories, raised "pillow" tiles on hover, and the account and power
    row at the bottom. Colours are pebble-drift.css tokens; the accent is
    the colour scheme's (it follows the one chosen in Settings).

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

    // ---- pebble-drift.css tokens -------------------------------------------
    readonly property color accent: Kirigami.Theme.highlightColor
    // --accent-text: the design's own for Indigo, else Settings' formula
    readonly property bool indigo: Qt.colorEqual(accent, dark ? "#7088ff" : "#4257e8")
    readonly property color accentText: indigo ? (dark ? "#9aabff" : "#3346cf")
                                               : (dark ? Qt.lighter(accent, 1.35) : Qt.darker(accent, 1.15))
    readonly property color inkOnAccent: indigo && dark ? "#0e1230" : "#ffffff"
    readonly property color textColor: dark ? "#eef0fa" : "#171a2b"          // --text-primary
    readonly property color text2: dark ? "#bcc1d6" : "#474d66"              // --text-secondary
    readonly property color text3: dark ? "#9ca2bb" : "#525972"              // --text-tertiary
    readonly property color raised: dark ? "#33364d" : "#fdfdff"            // --surface-raised
    readonly property color raised2: dark ? "#2c2f44" : "#f3f4fb"           // --surface-raised-2
    readonly property color sunken: dark ? Qt.rgba(0, 0, 10 / 255, 0.20) : Qt.rgba(48 / 255, 58 / 255, 120 / 255, 0.065)
    readonly property color sunkenStrong: dark ? Qt.rgba(0, 0, 10 / 255, 0.30) : Qt.rgba(48 / 255, 58 / 255, 120 / 255, 0.11)
    readonly property color hover: dark ? Qt.rgba(220 / 255, 228 / 255, 1, 0.07) : Qt.rgba(48 / 255, 58 / 255, 120 / 255, 0.065)
    readonly property color ring: dark ? Qt.rgba(0, 0, 0, 0.35) : Qt.rgba(30 / 255, 40 / 255, 100 / 255, 0.08)
    readonly property color drop: dark ? Qt.rgba(0, 0, 0, 0.30) : Qt.rgba(25 / 255, 35 / 255, 90 / 255, 0.10)
    readonly property color topLight: dark ? Qt.rgba(220 / 255, 228 / 255, 1, 0.08) : Qt.rgba(1, 1, 1, 0.9)
    readonly property color sheet: dark ? Qt.rgba(36 / 255, 38 / 255, 56 / 255, 0.92) : Qt.rgba(252 / 255, 252 / 255, 1, 0.92)
    readonly property color danger: dark ? "#ef5f6b" : "#cf3a48"            // --status-danger

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

    function systemRow(id, generation) {
        for (let i = 0; i < sysEntries.count; ++i) {
            const o = sysEntries.objectAt(i)
            if (o && o.favoriteId === id) {
                return o.index
            }
        }
        return -1
    }

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

        Rectangle {     // --surface-scrim: near-opaque, so the light blur behind it is enough
            anchors.fill: parent
            color: root.dark ? Qt.rgba(14 / 255, 16 / 255, 32 / 255, 0.84) : Qt.rgba(230 / 255, 233 / 255, 248 / 255, 0.78)
        }

        // A raised "pillow" (.btn / .tabs span.on / .app.hover): --surface-raised
        // gradient, --shadow-raised ring and drop, --highlight-top.
        component Pillow: Item {
            property real radius: 10
            Rectangle {     // 0 1px 2px drop
                anchors.fill: parent
                anchors.topMargin: 1
                anchors.bottomMargin: -1
                radius: parent.radius
                color: root.drop
            }
            Rectangle {
                anchors.fill: parent
                radius: parent.radius
                border.width: 1
                border.color: root.ring
                gradient: Gradient {
                    GradientStop { position: 0; color: root.raised }
                    GradientStop { position: 1; color: root.raised2 }
                }
            }
            Rectangle {     // top light
                x: parent.radius / 2; y: 1
                width: parent.width - parent.radius
                height: 1
                color: root.topLight
            }
        }
        // A pillow button with a glyph and a label (.foot .btn, .btn.danger)
        component PillButton: MouseArea {
            id: pb
            property alias text: pbLabel.text
            property string iconName
            property bool danger: false
            implicitWidth: pbRow.implicitWidth + 40
            implicitHeight: 42
            hoverEnabled: true
            activeFocusOnTab: true
            Accessible.role: Accessible.Button
            Accessible.name: text
            Pillow { anchors.fill: parent; radius: 11; visible: !pb.danger }
            Rectangle {
                anchors.fill: parent
                radius: 11
                visible: pb.danger
                color: pb.pressed ? Qt.darker(root.danger, 1.12) : root.danger
            }
            Rectangle {     // hover / press veil
                anchors.fill: parent
                radius: 11
                visible: !pb.danger
                color: root.hover
                opacity: pb.pressed ? 1.6 : (pb.containsMouse || pb.activeFocus ? 1 : 0)
            }
            Row {
                id: pbRow
                anchors.centerIn: parent
                spacing: 8
                Kirigami.Icon {
                    anchors.verticalCenter: parent.verticalCenter
                    width: 18; height: 18
                    source: pb.iconName
                    isMask: true
                    color: pb.danger ? "white" : root.textColor
                }
                Text {
                    id: pbLabel
                    anchors.verticalCenter: parent.verticalCenter
                    color: pb.danger ? "white" : root.textColor
                    font.pixelSize: 15
                    font.weight: Font.DemiBold
                }
            }
        }

        // power menu
        Rectangle {
            id: powerMenu
            visible: false
            z: 10
            anchors.bottom: foot.top
            anchors.left: foot.left
            anchors.bottomMargin: 12
            width: 240
            height: powerColumn.implicitHeight + 16
            radius: 16                                       // popover
            color: root.dark ? Qt.rgba(36 / 255, 38 / 255, 56 / 255, 0.97) : Qt.rgba(248 / 255, 249 / 255, 253 / 255, 0.96)
            border.width: 1
            border.color: root.ring
            layer.enabled: true
            layer.effect: MultiEffect {                      // --shadow-popover
                shadowEnabled: true
                shadowColor: root.dark ? Qt.rgba(0, 0, 0, 0.6) : Qt.rgba(25 / 255, 35 / 255, 90 / 255, 0.35)
                shadowBlur: 1.0
                shadowVerticalOffset: 14
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
                            radius: 10
                            color: pItem.containsMouse ? root.hover : "transparent"
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

        // ---- search field (.q): raised, focus ring, lifted ---------------------
        Item {
            id: searchBox
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: Math.round(230 * root.s)
            width: Math.min(Math.round(960 * Math.max(root.s, 0.8)), parent.width - 96)
            height: 68

            Rectangle {      // --focus-ring outer halo: 6 px --accent-soft
                anchors.fill: parent
                anchors.margins: -6
                radius: 24
                color: Qt.rgba(root.accent.r, root.accent.g, root.accent.b, root.dark ? 0.18 : 0.12)
            }
            Rectangle {
                anchors.fill: parent
                radius: 18
                color: root.raised
                border.width: 2                              // --focus-ring: 2 px --accent-ring
                border.color: root.accent
                layer.enabled: true
                layer.effect: MultiEffect {                  // --shadow-lift
                    shadowEnabled: true
                    shadowColor: root.dark ? Qt.rgba(0, 0, 0, 0.5) : Qt.rgba(25 / 255, 35 / 255, 90 / 255, 0.22)
                    shadowBlur: 0.7
                    shadowVerticalOffset: 10
                }
            }
            Canvas {        // lucent.js "search" glyph at 24 px (icon themes ship it at 16)
                id: searchIcon
                anchors.left: parent.left
                anchors.leftMargin: 24
                anchors.verticalCenter: parent.verticalCenter
                width: 24
                height: 24
                readonly property color ink: root.accentText
                onInkChanged: requestPaint()
                onPaint: {
                    const c = getContext("2d")
                    c.reset()
                    c.strokeStyle = ink
                    c.lineWidth = 2.2
                    c.lineCap = "round"
                    c.beginPath()
                    c.arc(10.5, 10.5, 6.5, 0, 2 * Math.PI)
                    c.moveTo(15.5, 15.5)
                    c.lineTo(20, 20)
                    c.stroke()
                }
            }
            TextInput {
                id: search
                anchors.left: searchIcon.right
                anchors.leftMargin: 14
                anchors.right: parent.right
                anchors.rightMargin: clearButton.visible ? 64 : 24
                anchors.verticalCenter: parent.verticalCenter
                font.pixelSize: 22                         // --type-title
                font.weight: Font.Medium
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
                    font.pixelSize: 22
                    font.weight: Font.Medium
                    elide: Text.ElideRight
                }
            }
            MouseArea {      // .clr: clear the query
                id: clearButton
                anchors.right: parent.right
                anchors.rightMargin: 16
                anchors.verticalCenter: parent.verticalCenter
                width: 36; height: 36
                visible: root.searching
                hoverEnabled: true
                Accessible.role: Accessible.Button
                Accessible.name: i18n("Clear")
                onClicked: { search.text = ""; search.forceActiveFocus() }
                Rectangle {
                    anchors.fill: parent
                    radius: 10
                    color: clearButton.containsMouse ? root.sunkenStrong : root.sunken
                }
                Kirigami.Icon {
                    anchors.centerIn: parent
                    width: 16; height: 16
                    source: "edit-clear-symbolic"
                    isMask: true
                    color: root.text2
                }
            }
        }

        // ---- category chips (.tabs): a sunken track with a raised "on" chip --
        Rectangle {
            anchors.fill: chips
            anchors.margins: -4
            radius: 14
            color: root.sunkenStrong
            opacity: chips.opacity
            visible: chips.visible
            Rectangle {      // --shadow-sunken: inner top shade
                x: 10; y: 1
                width: parent.width - 20
                height: 1
                color: root.dark ? Qt.rgba(0, 0, 0, 0.35) : Qt.rgba(25 / 255, 35 / 255, 90 / 255, 0.10)
            }
        }
        Row {
            id: chips
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: searchBox.bottom
            anchors.topMargin: 22
            spacing: 4
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
                    height: 38
                    hoverEnabled: true
                    // Categories with one or two apps (Help...) aren't worth a chip.
                    visible: label.length > 0 && (index === 0 || (root.rootModel.modelForRow(index)?.count ?? 0) > 2)
                    onClicked: { root.category = index; search.forceActiveFocus() }

                    Pillow {
                        anchors.fill: parent
                        radius: 10
                        visible: chip.on
                    }
                    Rectangle {
                        anchors.fill: parent
                        radius: 10
                        visible: !chip.on && chip.containsMouse
                        color: root.hover
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
                            color: chip.on ? root.accentText : root.text2
                        }
                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            text: chip.label
                            color: chip.on ? root.textColor : root.text2
                            font.pointSize: 11.625                // --type-body: 15.5 px
                            font.weight: Font.DemiBold
                        }
                    }
                }
            }
        }

        // ---- app grid ----------------------------------------------------------
        GridView {
            id: grid
            anchors.top: chips.bottom
            anchors.topMargin: Math.round(40 * root.s)
            // whole rows only, so no half-cut icons peek in at the bottom
            height: Math.max(1, Math.floor((foot.y - 24 - y) / root.cellH)) * root.cellH
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

                Pillow {        // hover/focus: .app.hover, a raised tile around icon and name
                    x: 10
                    y: 0
                    width: parent.width - 20
                    height: parent.height - 14
                    radius: 14                              // --radius-card
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
                    shadowColor: root.dark ? Qt.rgba(0, 0, 0, 0.45) : Qt.rgba(25 / 255, 35 / 255, 90 / 255, 0.22)
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
                    font.pointSize: 11.625                        // --type-body: 15.5 px
                    font.weight: Font.DemiBold
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

        // ---- account and power (.foot) --------------------------------------
        RowLayout {
            id: foot
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: Math.round(100 * root.s)
            width: Math.min(Math.round(1480 * root.s), parent.width - 96)
            spacing: 14

            MouseArea {      // the account; click: every session action (incl. Sign out)
                id: account
                Layout.preferredWidth: accountRow.implicitWidth + 16
                Layout.preferredHeight: 56
                hoverEnabled: true
                Accessible.role: Accessible.Button
                Accessible.name: kuser.fullName || kuser.loginName
                onClicked: powerMenu.visible = !powerMenu.visible
                Rectangle {
                    anchors.fill: parent
                    radius: 14
                    color: account.containsMouse || powerMenu.visible ? root.hover : "transparent"
                }
                RowLayout {
                    id: accountRow
                    anchors.left: parent.left
                    anchors.leftMargin: 8
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 14
                    Rectangle {      // .avatar: 44 px, radius 12
                        Layout.preferredWidth: 44
                        Layout.preferredHeight: 44
                        radius: 12
                        gradient: Gradient {
                            orientation: Gradient.Horizontal
                            GradientStop { position: 0; color: "#6a86ff" }
                            GradientStop { position: 0.6; color: "#9a62e0" }
                            GradientStop { position: 1; color: "#d0679c" }
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
                            sourceSize: Qt.size(88, 88)
                            fillMode: Image.PreserveAspectCrop
                        }
                        MultiEffect {
                            anchors.fill: parent
                            source: face
                            visible: face.status === Image.Ready
                            maskEnabled: true
                            maskSource: faceMask
                        }
                        Rectangle { id: faceMask; anchors.fill: parent; radius: 12; visible: false; layer.enabled: true }
                    }
                    ColumnLayout {
                        spacing: 0
                        Text {
                            text: kuser.fullName || kuser.loginName
                            color: root.textColor
                            font.pixelSize: 16
                            font.weight: Font.DemiBold
                        }
                        Text {
                            text: i18n("Local account")
                            color: root.text2
                            font.pixelSize: 14                  // --type-caption
                        }
                    }
                }
            }
            Item { Layout.fillWidth: true }
            Repeater {
                // Lock, Restart, Sleep, Shut down: Plasma's own session actions
                model: [["lock-screen", i18n("Lock"), "system-lock-screen-symbolic"],
                        ["reboot", i18n("Restart"), "system-reboot-symbolic"],
                        ["suspend", i18n("Sleep"), "system-suspend-symbolic"],
                        ["shutdown", i18n("Shut down"), "system-shutdown-symbolic"]]
                delegate: PillButton {
                    required property var modelData
                    readonly property int row: root.systemRow(modelData[0], rootItem.sysGen)
                    visible: row >= 0
                    text: modelData[1]
                    iconName: modelData[2]
                    danger: modelData[0] === "shutdown"
                    onClicked: {
                        root.rootModel.systemFavoritesModel.trigger(row, "", null)
                        root.toggle()
                    }
                }
            }
        }
        // the session actions' rows (an entry is missing when it isn't allowed)
        property int sysGen: 0
        Connections {
            target: root.rootModel.systemFavoritesModel
            function onCountChanged() { rootItem.sysGen++ }
        }
        Instantiator {
            id: sysEntries
            model: root.rootModel.systemFavoritesModel
            delegate: QtObject {
                required property int index
                required property var model
                readonly property string favoriteId: String(model.favoriteId ?? "")
            }
            onObjectAdded: rootItem.sysGen++
            onObjectRemoved: rootItem.sysGen++
        }
    }
}
