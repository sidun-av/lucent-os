import QtQuick
import QtQuick.Controls.Basic as C
import QtQuick.Dialogs
import QtQuick.Layouts
import Lucent

Page {
    id: page
    readonly property var st: AppearancePage.s
    title: System.tr("Appearance")
    lead: System.tr("Light or dark theme, accent colour and wallpaper. Changes apply right away, no restart needed.")
    Component.onCompleted: AppearancePage.refresh()

    Banner { text: AppearancePage.error; onDismissed: AppearancePage.clearError() }

    GridLayout {
        Layout.fillWidth: true
        Layout.topMargin: Theme.sectionTop
        columns: 3
        columnSpacing: Theme.choiceGap
        ThemeCard {
            mode: "light"; title: System.tr("Light"); icon: "sun"
            checked: page.st.mode === "light"
            onPicked: AppearancePage.setMode("light")
        }
        ThemeCard {
            mode: "dark"; title: System.tr("Dark"); icon: "moon"
            checked: page.st.mode === "dark"
            onPicked: AppearancePage.setMode("dark")
        }
        ThemeCard {
            mode: "auto"; title: System.tr("Auto"); hint: System.tr("light by day, dark after sunset")
            checked: page.st.mode === "auto"
            onPicked: AppearancePage.setMode("auto")
        }
    }

    GroupHeader { text: System.tr("Colour and style") }
    Card {
        SettingRow {
            label: System.tr("Accent colour")
            sub: System.tr("Buttons, selection, switches")
            Row {
                spacing: Theme.swatchGap
                Repeater {
                    model: page.st.accents || []
                    Item {
                        required property string modelData
                        readonly property bool on: (page.st.accent || "").toLowerCase() === modelData
                        width: Theme.swatch; height: Theme.swatch
                        Rectangle {  // ring: 0 0 0 3px win-bg, 0 0 0 5.5px colour
                            visible: parent.on
                            anchors.centerIn: parent
                            width: Theme.swatch + 11; height: width; radius: width / 2
                            color: modelData
                            Rectangle { anchors.centerIn: parent; width: Theme.swatch + 6; height: width; radius: width / 2; color: Theme.card }
                        }
                        Rectangle { anchors.fill: parent; radius: width / 2; color: modelData }
                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: AppearancePage.setAccent(modelData) }
                    }
                }
            }
        }
        SettingRow {
            label: System.tr("Wallpaper")
            sub: page.st.wallpaperOurs ? System.tr("“{name}”, comes with Lucent").replace("{name}", page.st.wallpaperName || "")
                                      : (page.st.wallpaperName || "")
            minHeight: 78
            Rectangle {
                width: 120; height: 68; radius: Theme.radiusThumb
                color: Theme.field
                border.color: Theme.line
                clip: true
                Image {
                    anchors.fill: parent
                    anchors.margins: 1
                    source: (Theme.dark && page.st.wallpaperThumbDark ? page.st.wallpaperThumbDark : page.st.wallpaperThumb) || ""
                    sourceSize: Qt.size(240, 136)
                    fillMode: Image.PreserveAspectCrop
                    asynchronous: true
                    layer.enabled: true
                }
            }
            LButton { text: System.tr("Choose…"); busy: AppearancePage.busy === "wallpaper"; onClicked: walls.open() }
        }
        SettingRow {
            label: System.tr("Transparency and blur")
            sub: System.tr("Taskbar, menus and pop-ups")
            LSwitch { checked: page.st.transparency !== false; onToggled: (on) => AppearancePage.setTransparency(on) }
        }
    }

    GroupHeader { text: System.tr("Text and motion") }
    Card {
        SettingRow {
            label: System.tr("Text size")
            sub: System.tr("Now: {size}").replace("{size}", textSizeName(page.st.textSize || 11))
            function textSizeName(p) {
                return p <= 10 ? System.tr("small") : p === 11 ? System.tr("standard") : p === 12 ? System.tr("large") : System.tr("larger")
            }
            LText { text: "A"; px: Theme.fontSmall; color: Theme.text2 }
            LSlider {
                from: 10; to: 13; stepSize: 1
                value: page.st.textSize || 11
                onMoved: AppearancePage.setTextSize(value)
            }
            LText { text: "A"; px: Theme.fontLabel + 4; color: Theme.text2 }
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

    LDialog {
        id: walls
        title: System.tr("Wallpaper")
        width: 820
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
                contentItem: Rectangle { implicitWidth: 6; radius: 3; color: Theme.lineStrong }
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
                    width: 176; height: 99 + 30
                    radius: Theme.radiusPreview
                    color: m.containsMouse ? Theme.hover : "transparent"
                    Rectangle {
                        x: 4; y: 4; width: 168; height: 95; radius: Theme.radiusThumb
                        color: Theme.field
                        border.width: parent.on ? 3 : 1
                        border.color: parent.on ? Theme.accent : Theme.line
                        Image {
                            anchors.fill: parent; anchors.margins: parent.border.width
                            source: modelData.thumb; sourceSize: Qt.size(336, 190)
                            fillMode: Image.PreserveAspectCrop; asynchronous: true
                        }
                    }
                    LText { x: 6; y: 103; width: 164; text: modelData.name; px: Theme.fontSmall; color: Theme.text2 }
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
