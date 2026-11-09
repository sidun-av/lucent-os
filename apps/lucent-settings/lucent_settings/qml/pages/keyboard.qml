import QtQuick
import QtQuick.Layouts
import Lucent

Page {
    id: page
    readonly property var st: HabitsPage.s
    title: System.tr("Keyboard & language")
    lead: System.tr("The keyboard layouts you type with and how to switch between them.")
    Component.onCompleted: HabitsPage.refresh()

    Card {
        title: System.tr("Keyboard layouts")
        Repeater {
            model: page.st.layouts || []
            SettingRow {
                required property var modelData
                label: modelData.name
                leading: IconTile { icon: "keyboard" }
                Pill { text: modelData.code.toUpperCase() }
            }
        }
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
            label: System.tr("Add or remove layouts")
            sub: System.tr("In Advanced settings, Keyboard")
            clickable: true
            onClicked: HabitsPage.openKeyboard()
            Sym { name: "right"; size: 18; color: Theme.text3 }
        }
    }
    Card {
        title: System.tr("Language")
        SettingRow {
            label: page.st.language || ""
            sub: System.tr("The language of menus and apps. Chosen when Lucent was installed.")
            LButton { text: System.tr("Change…"); onClicked: HabitsPage.openLanguage() }
        }
    }
}
