import QtQuick
import QtQuick.Layouts
import Lucent

Page {
    id: page
    readonly property var st: NetworkPage.s
    readonly property string busy: NetworkPage.busy
    property string asking: ""          // network whose password field is open
    title: System.tr("Wi-Fi & Network")
    lead: System.tr("Connect to Wi-Fi or a network cable. Networks you have joined are remembered.")
    Component.onCompleted: { NetworkPage.refresh(); scanTimer.start() }
    Timer { interval: 4000; repeat: true; running: true; onTriggered: NetworkPage.refresh() }
    Timer { id: scanTimer; interval: 300; onTriggered: NetworkPage.scan() }
    Timer { interval: 20000; repeat: true; running: page.st.wifiEnabled === true; onTriggered: NetworkPage.scan() }

    Banner { text: NetworkPage.error; onDismissed: NetworkPage.clearError() }

    GroupHeader { text: System.tr("Wi-Fi"); Layout.topMargin: Theme.sectionTop }
    Card {
        SettingRow {
            label: System.tr("Wi-Fi")
            sub: !page.st.loaded ? "" : !page.st.wifiHardware ? System.tr("This computer has no Wi-Fi adapter.")
                 : !page.st.wifiEnabled ? System.tr("Off") : page.st.wifiCurrent ? System.tr("Connected to “{name}”").replace("{name}", page.st.wifiCurrent) : System.tr("Not connected")
            leading: IconTile { icon: "wifi"; tint: Theme.sq.network }
            LSwitch {
                visible: page.st.wifiHardware === true
                checked: page.st.wifiEnabled === true
                onToggled: (on) => NetworkPage.setWifi(on)
            }
        }
        Repeater {
            model: page.st.wifiHardware && page.st.wifiEnabled ? (page.st.networks || []) : []
            ColumnLayout {
                required property var modelData
                Layout.fillWidth: true
                spacing: 0
                SettingRow {
                    label: modelData.ssid
                    labelWeight: modelData.active ? 600 : 400
                    minHeight: 56
                    sub: modelData.enterprise ? System.tr("Work or school network: set it up in Advanced network settings") : ""
                    leading: Item {
                        width: Theme.iconTile; height: 24
                        Sym { anchors.centerIn: parent; name: "wifi"; size: 22; color: Theme.text; opacity: 0.35 + 0.65 * modelData.bars / 4 }
                    }
                    Sym { visible: modelData.secure; name: "lock"; size: 16; color: Theme.text3 }
                    Pill { visible: modelData.active; text: System.tr("Connected"); kind: "ok" }
                    LButton {
                        visible: !modelData.active && !modelData.enterprise && page.asking !== modelData.ssid
                        text: System.tr("Connect")
                        busy: page.busy === "connect:" + modelData.ssid
                        onClicked: {
                            if (modelData.secure && !modelData.known) { page.asking = modelData.ssid; pw.text = ""; pw.forceActiveFocus() }
                            else NetworkPage.connectTo(modelData.ssid, "", modelData.known)
                        }
                    }
                    LButton {
                        visible: modelData.active
                        text: System.tr("Disconnect")
                        onClicked: NetworkPage.disconnectDevice(page.st.wifiDevice)
                    }
                }
                RowLayout {   // password, under the network it belongs to
                    visible: page.asking === modelData.ssid
                    Layout.fillWidth: true
                    Layout.leftMargin: 70
                    Layout.rightMargin: 20
                    Layout.bottomMargin: 16
                    spacing: 10
                    LTextField {
                        id: pw
                        Layout.fillWidth: true
                        echoMode: TextInput.Password
                        placeholderText: System.tr("Wi-Fi password")
                        onAccepted: go.clicked()
                    }
                    LButton { text: System.tr("Cancel"); onClicked: page.asking = "" }
                    LButton {
                        id: go
                        primary: true
                        text: System.tr("Connect")
                        enabled: pw.text.length >= 8
                        onClicked: { NetworkPage.connectTo(modelData.ssid, pw.text, false); page.asking = "" }
                    }
                }
            }
        }
        SettingRow {
            visible: page.st.wifiHardware && page.st.wifiEnabled && (page.st.networks || []).length === 0
            label: page.busy === "scan" || !page.st.scanned ? System.tr("Looking for networks…") : System.tr("No networks found")
            labelWeight: 400
            minHeight: 56
            Spinner { visible: page.busy === "scan" || !page.st.scanned }
        }
    }

    GroupHeader { text: System.tr("Network cable"); visible: (page.st.wired || []).length > 0 }
    Card {
        visible: (page.st.wired || []).length > 0
        Repeater {
            model: page.st.wired || []
            SettingRow {
                required property var modelData
                label: modelData.connected ? (modelData.connection || System.tr("Wired connection")) : System.tr("Wired connection")
                sub: modelData.connected ? "" : modelData.unplugged ? System.tr("No cable plugged in") : System.tr("Not connected")
                leading: IconTile { icon: "cable" }
                Pill { visible: modelData.connected; text: System.tr("Connected"); kind: "ok" }
                LButton {
                    visible: !modelData.unplugged
                    text: modelData.connected ? System.tr("Disconnect") : System.tr("Connect")
                    busy: page.busy === (modelData.connected ? "disconnect:" : "connect:") + modelData.name
                    onClicked: modelData.connected ? NetworkPage.disconnectDevice(modelData.name) : NetworkPage.connectDevice(modelData.name)
                }
            }
        }
    }

    GroupHeader { text: System.tr("More") }
    Card {
        SettingRow {
            label: System.tr("Advanced network settings")
            sub: System.tr("VPN, proxy, work and school networks, IP addresses")
            clickable: true
            onClicked: NetworkPage.openAdvanced()
            Sym { name: "right"; size: 18; color: Theme.text3 }
        }
    }
}
