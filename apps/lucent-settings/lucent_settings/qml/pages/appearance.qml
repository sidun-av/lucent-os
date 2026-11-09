import QtQuick
import QtQuick.Controls.Basic as C
import QtQuick.Dialogs
import QtQuick.Effects
import QtQuick.Layouts
import Lucent

// docs/mockups/concepts-2026/pebble/03-settings: Mode, Accent colour and
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
            title: System.tr("Accent colour")
            subtitle: System.tr("Used for selection, switches, progress and focus.")
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
                        text: System.tr(modelData.name)
                        px: Theme.fontSmall
                        weight: on ? Theme.weightCardTitle : 400
                        color: on ? Theme.text : Theme.text2
                    }
                }
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
                label: System.tr("Animations")
                sub: System.tr("Windows opening, closing and minimising")
                Segmented {
                    current: page.st.animations || "fast"
                    options: [{ value: "off", label: System.tr("Off") }, { value: "fast", label: System.tr("Fast") },
                              { value: "normal", label: System.tr("Normal") }]
                    onPicked: (v) => AppearancePage.setAnimations(v)
                }
            }
        }
    }

    Card {
        title: System.tr("Wallpaper")
        subtitle: System.tr("Lucent's wallpapers have a day and a night version that follow the mode.")
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
                ColumnLayout {
                    required property var modelData
                    // a day/night pair shares one wallpaper: mark the half that shows now
                    readonly property bool on: modelData.path === page.st.wallpaper
                        && (modelData.variant === "" || modelData.variant === "picture"
                            || modelData.variant === (Theme.dark ? "night" : "day"))
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignTop
                    spacing: 10
                    Item {
                        Layout.fillWidth: true
                        implicitHeight: 138
                        Rectangle {  // 0 0 0 3px raised, 0 0 0 5.5px accent
                            visible: parent.parent.on
                            anchors.fill: parent; anchors.margins: -5.5
                            radius: Theme.radiusThumb + 5.5
                            color: Theme.accent
                            Rectangle { anchors.fill: parent; anchors.margins: 2.5; radius: Theme.radiusThumb + 3; color: Theme.raised }
                        }
                        Shadow { anchors.fill: parent; radius: Theme.radiusThumb }
                        Image {
                            id: thumb
                            anchors.fill: parent
                            source: modelData.thumb
                            sourceSize: Qt.size(560, 320)
                            fillMode: Image.PreserveAspectCrop
                            asynchronous: true
                            visible: false
                        }
                        Item { id: thumbMask; anchors.fill: parent; visible: false; layer.enabled: true
                               Rectangle { anchors.fill: parent; radius: Theme.radiusThumb; color: "black" } }
                        MultiEffect { anchors.fill: parent; source: thumb; maskEnabled: true; maskSource: thumbMask
                                      maskThresholdMin: 0.5; maskSpreadAtMin: 1.0 }
                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: AppearancePage.setWallpaper(modelData.path) }
                    }
                    ColumnLayout {
                        spacing: 1
                        LText { text: modelData.name; px: Theme.fontSub; weight: Theme.weightStrong }
                        LText {
                            readonly property string kind: modelData.variant === "day" ? System.tr("Day")
                                : modelData.variant === "night" ? System.tr("Night")
                                : modelData.variant === "picture" ? System.tr("Your picture") : System.tr("Included")
                            text: kind + (parent.parent.on ? " · " + System.tr("in use") : "")
                            px: Theme.fontSmall; color: Theme.text2
                        }
                    }
                }
            }
            Item {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignTop
                implicitHeight: 138
                Well {
                    anchors.fill: parent
                    radius: Theme.radiusThumb
                    Column {
                        anchors.centerIn: parent
                        spacing: 8
                        Sym { anchors.horizontalCenter: parent.horizontalCenter; name: "plus"; size: 26; color: Theme.text2 }
                        LText { text: System.tr("Add a picture"); px: Theme.fontBody; weight: Theme.weightStrong; color: Theme.text2 }
                    }
                }
                MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: pick.open() }
            }
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
