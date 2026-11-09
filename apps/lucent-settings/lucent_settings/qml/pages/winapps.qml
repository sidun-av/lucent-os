import QtQuick
import QtQuick.Layouts
import Lucent

Page {
    id: page
    readonly property var st: WinappsPage.s
    readonly property string busy: WinappsPage.busy
    property var removing: ({})
    title: System.tr("Windows apps")
    lead: System.tr("Programs for Windows that you installed by double-clicking their installer. They run in Lucent Bridge, each in its own folder.")
    Component.onCompleted: WinappsPage.refresh()

    Banner { text: WinappsPage.error; onDismissed: WinappsPage.clearError() }

    Card {
        SettingRow {
            label: page.st.mode === "native" ? System.tr("Runs directly on this processor")
                 : page.st.mode === "translated" ? System.tr("Translated for this ARM processor") : System.tr("Not available on this processor")
            sub: page.st.mode === "native" ? System.tr("This computer has an Intel or AMD (x86-64) processor, like most Windows PCs, so Windows programs run at full speed.")
               : page.st.mode === "translated" ? System.tr("This computer has an ARM processor. Programs made for Intel/AMD PCs are translated while they run, so heavy programs and games can be slower.")
               : System.tr("Windows programs need an Intel/AMD or ARM processor.")
            leading: IconTile { icon: "chip"; glyph: Theme.accent }
        }
    }

    Card {
        title: System.tr("Installed programs")
        visible: (page.st.apps || []).length > 0
        Repeater {
            model: page.st.apps || []
            SettingRow {
                required property var modelData
                label: modelData.name
                sub: modelData.sub
                leading: Item {
                    width: Theme.iconTile; height: Theme.iconTile
                    Image { anchors.fill: parent; source: modelData.icon; sourceSize: Qt.size(72, 72); visible: status === Image.Ready }
                    IconTile { anchors.fill: parent; visible: modelData.icon === ""; icon: "winapp" }
                }
                Pill {
                    visible: modelData.status === "works" || modelData.status === "broken"
                    text: modelData.status === "works" ? System.tr("Works") : System.tr("Doesn't work")
                    kind: modelData.status === "works" ? "ok" : "warn"
                }
                LButton { text: System.tr("Open folder"); icon: "folder"; visible: modelData.folder !== ""; onClicked: WinappsPage.openFolder(modelData.folder) }
                LButton {
                    text: System.tr("Remove")
                    danger: true
                    busy: page.busy === "remove:" + modelData.id
                    onClicked: { confirm.app = modelData; confirm.open() }
                }
            }
        }
    }

    EmptyState {
        visible: page.st.loaded === true && (page.st.apps || []).length === 0
        Layout.topMargin: Theme.groupTop
        icon: "winapp"
        title: System.tr("No Windows programs yet")
        text: System.tr("Double-click a Windows installer (.exe or .msi) in Files to install a program. It then appears in the Start menu and here.")
    }

    LDialog {
        id: confirm
        property var app: ({})
        title: System.tr("Remove “{name}”?").replace("{name}", app.name || "")
        text: System.tr("The program, its settings and the files it keeps in its own folder are deleted. Documents you saved in your Documents folder stay.")
        acceptText: System.tr("Remove")
        destructive: true
        onAccepted: { close(); WinappsPage.remove(app.id) }
    }
}
