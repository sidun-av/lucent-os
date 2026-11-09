import QtQuick
import QtQuick.Layouts
import Lucent

Page {
    id: page
    readonly property var st: BluetoothPage.s
    readonly property string busy: BluetoothPage.busy
    title: System.tr("Bluetooth")
    lead: System.tr("Headphones, speakers, mice and keyboards. Put a new device in pairing mode, then choose it below.")
    Component.onCompleted: BluetoothPage.refresh()
    Component.onDestruction: BluetoothPage.setDiscovering(false)
    Timer { interval: 3000; repeat: true; running: true; onTriggered: BluetoothPage.refresh() }
    // Look for new devices while the page is open (once per power-on).
    property bool asked: false
    readonly property bool powered: page.st.powered === true
    onPoweredChanged: if (!powered) asked = false
    Timer {
        interval: 500; running: page.powered && !page.asked
        onTriggered: { page.asked = true; BluetoothPage.setDiscovering(true) }
    }

    function kindIcon(k) {
        return k === "headphones" ? "headphones" : k === "mouse" ? "mouse" : k === "keyboard" ? "keyboard"
             : k === "speaker" ? "speaker" : k === "phone" ? "phone" : k === "gamepad" ? "gamepad" : "bluetooth"
    }

    Banner { text: BluetoothPage.error; onDismissed: BluetoothPage.clearError() }

    EmptyState {
        visible: page.st.loaded === true && !page.st.available
        icon: "bluetooth"
        title: System.tr("No Bluetooth adapter found")
        text: System.tr("This computer has no Bluetooth, or it is switched off in the firmware (BIOS) or with a key on the keyboard. A USB Bluetooth adapter works too.")
    }

    Card {
        visible: page.st.available === true
        SettingRow {
            label: System.tr("Bluetooth")
            sub: page.st.powered ? System.tr("On. Other devices can find this computer while this page is open.") : System.tr("Off")
            leading: IconTile { icon: "bluetooth"; glyph: Theme.accent }
            LSwitch { checked: page.st.powered === true; onToggled: (on) => BluetoothPage.setPowered(on) }
        }
    }

    Card {
        title: System.tr("My devices")
        visible: page.st.powered === true && (page.st.paired || []).length > 0
        Repeater {
            model: page.st.paired || []
            SettingRow {
                required property var modelData
                label: modelData.name
                sub: (modelData.connected ? System.tr("Connected") : System.tr("Not connected"))
                     + (modelData.battery >= 0 ? " · " + System.tr("battery {n}%").replace("{n}", modelData.battery) : "")
                leading: IconTile { icon: page.kindIcon(modelData.kind) }
                LButton {
                    text: modelData.connected ? System.tr("Disconnect") : System.tr("Connect")
                    busy: page.busy === "connect:" + modelData.path || page.busy === "disconnect:" + modelData.path
                    onClicked: modelData.connected ? BluetoothPage.disconnectDevice(modelData.path) : BluetoothPage.connectDevice(modelData.path)
                }
                LButton { text: System.tr("Forget"); flat: true; onClicked: BluetoothPage.forget(modelData.path) }
            }
        }
    }

    Card {
        title: System.tr("Devices nearby")
        visible: page.st.powered === true
        headerItems: Spinner { size: 16; visible: page.st.discovering === true }
        Repeater {
            model: page.st.nearby || []
            SettingRow {
                required property var modelData
                label: modelData.name
                leading: IconTile { icon: page.kindIcon(modelData.kind) }
                LButton { text: System.tr("Pair"); busy: page.busy === "pair:" + modelData.path; onClicked: BluetoothPage.pair(modelData.path) }
            }
        }
        SettingRow {
            visible: (page.st.nearby || []).length === 0
            label: System.tr("Looking for devices…")
            labelWeight: 400
            sub: System.tr("Make sure the device is switched on and in pairing mode.")
        }
    }
}
