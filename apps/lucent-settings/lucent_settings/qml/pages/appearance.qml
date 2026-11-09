import QtQuick
import QtQuick.Controls.Basic as C
import QtQuick.Dialogs
import QtQuick.Effects
import QtQuick.Layouts
import Lucent

// docs/mockups/concepts-2026/pebble/03-settings: Mode, Accent color and
// Comfort side by side, Wallpaper.
Page {
    id: page
    readonly property var st: AppearancePage.s
    title: System.tr("Appearance")
    lead: System.tr("Choose how Lucent looks. Changes apply right away to every app.")
    Component.onCompleted: AppearancePage.refresh()

    Banner { text: AppearancePage.error; onDismissed: AppearancePage.clearError() }

    Card {
        title: System.tr("Mode")
        subtitle: System.tr("Light and dark change windows, the taskbar and menus together.")
        GridLayout {
            Layout.fillWidth: true
            Layout.topMargin: 12
            columns: 3
            columnSpacing: Theme.choiceGap
            ThemeCard {
                mode: "light"; title: System.tr("Light")
                dayWallpaper: page.st.wallpaperThumb || ""; nightWallpaper: page.st.wallpaperThumbDark || page.st.wallpaperThumb || ""
                checked: page.st.mode === "light"
                onPicked: AppearancePage.setMode("light")
            }
            ThemeCard {
                mode: "dark"; title: System.tr("Dark")
                dayWallpaper: page.st.wallpaperThumb || ""; nightWallpaper: page.st.wallpaperThumbDark || page.st.wallpaperThumb || ""
                checked: page.st.mode === "dark"
                onPicked: AppearancePage.setMode("dark")
            }
            ThemeCard {
                mode: "auto"; title: System.tr("Auto"); hint: System.tr("Dark from sunset to sunrise")
                dayWallpaper: page.st.wallpaperThumb || ""; nightWallpaper: page.st.wallpaperThumbDark || page.st.wallpaperThumb || ""
                checked: page.st.mode === "auto"
                onPicked: AppearancePage.setMode("auto")
            }
        }
    }

    GridLayout {
        Layout.fillWidth: true
        columns: 2
        columnSpacing: Theme.cardGap
        uniformCellWidths: true
        Card {
            Layout.alignment: Qt.AlignTop
            Layout.fillHeight: true
            title: System.tr("Accent color")
            subtitle: System.tr("Used for selection, switches, progress and focus.")
            opacity: 1
            GridLayout {
                id: sws
                Layout.fillWidth: true
                Layout.topMargin: 12
                columns: Theme.accents.length
                columnSpacing: Theme.swatchGap
                uniformCellWidths: true
                rowSpacing: 10
                Repeater {
                    model: Theme.accents
                    Item {
                        required property var modelData
                        readonly property bool on: (page.st.accent || "").toLowerCase() === modelData.color
                        Layout.fillWidth: true
                        implicitHeight: Theme.swatchHeight
                        Rectangle {  // 0 0 0 3px raised, 0 0 0 5.5px text
                            visible: parent.on
                            anchors.fill: parent; anchors.margins: -5.5
                            radius: Theme.radiusSwatch + 5.5
                            color: Theme.text
                            Rectangle { anchors.fill: parent; anchors.margins: 2.5; radius: Theme.radiusSwatch + 3; color: Theme.raised }
                        }
                        Shadow { anchors.fill: parent; radius: Theme.radiusSwatch }
                        Rectangle { anchors.fill: parent; radius: Theme.radiusSwatch; color: modelData.color }
                        Rectangle {  // inset top light
                            x: Theme.radiusSwatch / 2; y: 1; width: parent.width - Theme.radiusSwatch; height: 1
                            color: Qt.rgba(1, 1, 1, 0.3)
                        }
                        Sym { anchors.centerIn: parent; visible: parent.on; name: "check"; size: 22; color: "#ffffff" }
                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: AppearancePage.setAccent(modelData.color) }
                    }
                }
                Repeater {
                    model: Theme.accents
                    LText {
                        required property var modelData
                        readonly property bool on: (page.st.accent || "").toLowerCase() === modelData.color
                        Layout.fillWidth: true
                        horizontalAlignment: Text.AlignHCenter
                        text: modelData.name
                        px: Theme.fontSmall
                        weight: on ? Theme.weightCardTitle : 400
                        color: on ? Theme.text : Theme.text2
                    }
                }
            }
            SettingRow {
                Layout.topMargin: 14
                separator: true
                label: System.tr("Match wallpaper")
                sub: System.tr("Pick the accent from the current wallpaper")
                LSwitch { checked: page.st.accentFromWallpaper === true; onToggled: (on) => AppearancePage.setAccentFromWallpaper(on) }
            }
        }
        Card {
            Layout.alignment: Qt.AlignTop
            Layout.fillHeight: true
            title: System.tr("Comfort")
            SettingRow {
                label: System.tr("Text size")
                sub: System.tr("Applies to apps and the taskbar")
                LText { text: "A"; px: Theme.fontSmall; weight: 700; color: Theme.text2 }
                LSlider {
                    implicitWidth: 240
                    from: 10; to: 13; stepSize: 1
                    value: page.st.textSize || 11
                    onMoved: AppearancePage.setTextSize(value)
                }
                LText { text: "A"; px: Theme.fontLabel + 3; weight: 700; color: Theme.text2 }
            }
            SettingRow {
                label: System.tr("Reduce motion")
                sub: System.tr("Windows open and close without animation")
                LSwitch {
                    checked: page.st.animations === "off"
                    onToggled: (on) => AppearancePage.setAnimations(on ? "off" : "fast")
                }
            }
        }
    }

    Card {
        title: System.tr("Wallpaper")
        subtitle: System.tr("Lucent's wallpapers switch to their night version in dark mode.")
        headerItems: LButton { text: System.tr("Browse…"); onClicked: walls.open() }
        GridLayout {
            Layout.fillWidth: true
            Layout.topMargin: 12
            columns: 5
            columnSpacing: 16
            rowSpacing: 10
            uniformCellWidths: true
            Repeater {
                model: (page.st.wallTiles || []).slice(0, 4)
                WallTile { required property var modelData; tile: modelData; current: page.st.wallpaper || ""
                           onPicked: (p) => AppearancePage.setWallpaper(p) }
            }
            AddPictureTile { onClicked: pick.open() }
        }
    }

    LDialog {
        id: walls
        title: System.tr("Wallpaper")
        width: 860
        acceptText: System.tr("Done")
        rejectText: System.tr("Add a picture…")
        onAccepted: close()
        onRejected: pick.open()
        Flickable {
            Layout.fillWidth: true
            Layout.preferredHeight: Math.min(grid.implicitHeight, 470)
            contentHeight: grid.implicitHeight
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            C.ScrollBar.vertical: C.ScrollBar {
                contentItem: Rectangle { implicitWidth: 6; radius: 3; color: Theme.line2 }
            }
            Flow {
                id: grid
                width: parent.width
                spacing: 12
                Repeater {
                    model: page.st.wallpapers || []
                    Rectangle {
                        required property var modelData
                        readonly property bool on: modelData.path === page.st.wallpaper
                        width: 184; height: 104 + 30
                        radius: Theme.radiusPreview
                        color: m.containsMouse ? Theme.hover : "transparent"
                        Rectangle {
                            x: 4; y: 4; width: 176; height: 99; radius: Theme.radiusPreview
                            color: Theme.wellStrong
                            border.width: parent.on ? 3 : 0
                            border.color: Theme.accent
                            Image {
                                anchors.fill: parent; anchors.margins: parent.border.width
                                source: modelData.thumb; sourceSize: Qt.size(352, 198)
                                fillMode: Image.PreserveAspectCrop; asynchronous: true
                            }
                        }
                        LText { x: 6; y: 108; width: 172; text: modelData.name; px: Theme.fontSmall; color: Theme.text2 }
                        MouseArea { id: m; anchors.fill: parent; hoverEnabled: true; onClicked: AppearancePage.setWallpaper(modelData.path) }
                    }
                }
            }
        }
    }
    FileDialog {
        id: pick
        title: System.tr("Choose a picture")
        nameFilters: [System.tr("Pictures") + " (*.jpg *.jpeg *.png *.webp *.avif *.jxl)"]
        onAccepted: AppearancePage.setWallpaper(selectedFile.toString())
    }
}
