import QtQuick
import QtQuick.Layouts
import Lucent

// docs/mockups/03c-settings-windows
Page {
    id: page
    readonly property var st: HabitsPage.s
    title: System.tr("Like Windows")
    lead: System.tr("The familiar buttons and keyboard shortcuts are already on. Check or change them here.")
    Component.onCompleted: HabitsPage.refresh()

    // A choice tile like the Mode tiles on Appearance: sunken, or (chosen)
    // a light card with an accent ring.
    component ButtonsCard: Item {
        id: wbo
        property string side
        property string caption
        property string hint
        readonly property bool on: page.st.buttons === side
        Layout.fillWidth: true
        implicitHeight: 16 + 46 + 14 + 22 + 16
        Well { anchors.fill: parent; radius: Theme.radiusChoice; visible: !wbo.on }
        Item {
            anchors.fill: parent
            visible: wbo.on
            Shadow { anchors.fill: parent; radius: Theme.radiusChoice }
            Rectangle { anchors.fill: parent; anchors.margins: -Theme.ringWidth; radius: Theme.radiusChoice + Theme.ringWidth; color: Theme.accent }
            Rectangle { anchors.fill: parent; radius: Theme.radiusChoice; color: Theme.selectedCard }
        }
        Raised {  // a miniature title bar
            x: 16; y: 16
            width: parent.width - 32; height: 46
            radius: Theme.radiusControl
            RowLayout {
                anchors { fill: parent; leftMargin: wbo.side === "left" ? 14 : 16; rightMargin: 6 }
                spacing: 0
                Row {
                    visible: wbo.side === "left"
                    spacing: 8
                    Repeater { model: 3; Rectangle { width: 13; height: 13; radius: 6.5; color: Theme.line2 } }
                }
                LText {
                    Layout.leftMargin: wbo.side === "left" ? 16 : 0
                    text: System.tr("Document — Files"); px: Theme.fontSub; weight: Theme.weightStrong; color: Theme.text2
                }
                Item { Layout.fillWidth: true }
                Row {
                    visible: wbo.side === "right"
                    Repeater {
                        model: ["min", "max", "x"]
                        Item { required property string modelData; width: 42; height: 34
                               Sym { anchors.centerIn: parent; name: modelData; size: 14; color: Theme.text2 } }
                    }
                }
            }
        }
        RowLayout {
            x: 18; y: 16 + 46 + 14
            spacing: 10
            Radio { checked: wbo.on }
            LText { text: wbo.caption; px: Theme.fontLabel; weight: Theme.weightHeading }
            LText { text: wbo.hint; px: Theme.fontSub; color: Theme.text2; visible: text !== "" }
        }
        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: HabitsPage.setButtons(wbo.side) }
    }

    Card {
        title: System.tr("Window buttons")
        GridLayout {
            Layout.fillWidth: true
            Layout.topMargin: 12
            columns: 2
            columnSpacing: Theme.choiceGap
            uniformCellWidths: true
            ButtonsCard { side: "right"; caption: System.tr("Window buttons on the right"); hint: System.tr("— like Windows") }
            ButtonsCard { side: "left"; caption: System.tr("Window buttons on the left") }
        }
    }

    Card {
        title: System.tr("Keyboard shortcuts")
        Item {
            Layout.fillWidth: true
            implicitHeight: grid.implicitHeight
            GridLayout {
                id: grid
                width: parent.width
                columns: 2
                columnSpacing: 0
                rowSpacing: 0
                uniformCellWidths: true
                Repeater {
                    model: page.st.shortcuts || []
                    SettingRow {
                        required property var modelData
                        required property int index
                        separator: index >= 2
                        label: modelData.action
                        Row {
                            spacing: 0
                            Repeater {
                                model: modelData.keys
                                Row {
                                    required property string modelData
                                    required property int index
                                    spacing: 0
                                    LText { visible: index > 0; text: "+"; px: Theme.fontBody; weight: Theme.weightStrong; color: Theme.text3; width: 34; horizontalAlignment: Text.AlignHCenter; height: 28 }
                                    Keycap { text: modelData === "Win" ? "⊞ Win" : modelData }
                                }
                            }
                        }
                    }
                }
            }
            Rectangle { x: Math.round(parent.width / 2); width: 1; height: parent.height; color: Theme.line }
        }
    }

    Card {
        title: System.tr("Keyboard and mouse")
        SettingRow {
            label: System.tr("Switch keyboard layout")
            sub: page.st.layoutCount > 1 ? System.tr("Win + Space always works too. The current layout shows on the taskbar.")
                                        : System.tr("Takes effect when you have two or more layouts. Win + Space always works too.")
            Segmented {
                current: page.st.layoutSwitch || "alt_shift"
                options: [{ value: "alt_shift", label: "Alt + Shift" }, { value: "ctrl_shift", label: "Ctrl + Shift" },
                          { value: "win_space", label: System.tr("Win + Space only") }]
                onPicked: (v) => HabitsPage.setLayoutSwitch(v)
            }
        }
        SettingRow {
            label: System.tr("Open files with a double-click")
            sub: page.st.doubleClick ? System.tr("A single click only selects") : System.tr("A single click opens files and folders")
            LSwitch { checked: page.st.doubleClick || false; onToggled: (on) => HabitsPage.setDoubleClick(on) }
        }
    }
}
