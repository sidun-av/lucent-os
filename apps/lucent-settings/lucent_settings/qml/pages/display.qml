import QtQuick
import QtQuick.Layouts
import Lucent

Page {
    id: page
    readonly property var st: DisplayPage.s
    title: System.tr("Display")
    lead: System.tr("Screen resolution, the size of everything on screen, and night light.")
    Component.onCompleted: DisplayPage.refresh()

    Banner { text: DisplayPage.error; onDismissed: DisplayPage.clearError() }
    Banner {
        kind: "info"
        text: page.st.confirm > 0 ? System.tr("Keep this resolution? Going back in {n} s.").replace("{n}", page.st.confirm) : ""
        onDismissed: DisplayPage.keep()
    }
    RowLayout {
        visible: page.st.confirm > 0
        Layout.topMargin: 10
        spacing: 12
        LButton { primary: true; text: System.tr("Keep"); onClicked: DisplayPage.keep() }
        LButton { text: System.tr("Go back"); onClicked: DisplayPage.revert() }
    }

    Repeater {
        model: page.st.outputs || []
        ColumnLayout {
            required property var modelData
            required property int index
            Layout.fillWidth: true
            spacing: Theme.cardGap
            Card {
                title: (page.st.outputs || []).length > 1 ? modelData.name : System.tr("Screen")
                SettingRow {
                    label: System.tr("Resolution")
                    sub: System.tr("Now: {w} × {h}").replace("{w}", modelData.width).replace("{h}", modelData.height)
                    LCombo {
                        model: modelData.modes.map(m => ({ value: m.id, label: m.label }))
                        current: modelData.currentMode
                        onPicked: (v) => DisplayPage.setMode(modelData.name, v)
                    }
                }
                SettingRow {
                    label: System.tr("Size of text and apps")
                    sub: System.tr("Recommended for this screen: {n}").replace("{n}", Math.round(modelData.recommendedScale * 100) + "%")
                    Segmented {
                        current: String(modelData.scale)
                        options: [1, 1.25, 1.5, 1.75, 2].map(s => ({ value: String(s), label: Math.round(s * 100) + "%" }))
                        onPicked: (v) => DisplayPage.setScale(modelData.name, Number(v))
                    }
                }
            }
        }
    }

    Card {
        title: System.tr("Night light")
        SettingRow {
            label: System.tr("Night light")
            sub: System.tr("Warmer colors in the evening, easier on the eyes. Follows sunset and sunrise.")
            leading: IconTile { icon: "moon"; glyph: Theme.accent }
            LSwitch { checked: page.st.night === true; onToggled: (on) => DisplayPage.setNight(on) }
        }
    }
}
