// Install / Installed / progress button for one app or a set of apps.
import QtQuick

Item {
    id: a
    property string state_: "available"   // available installed system queued installing removing updating
    property real progress: 0
    property string installText: l10n.text("Install")
    property string installKind: "primary"
    property bool openWhenInstalled: false
    property bool small: true
    signal install()
    signal open()
    readonly property var tk: store.t
    readonly property bool busy: state_ === "installing" || state_ === "removing" || state_ === "updating"
    implicitWidth: busy || state_ === "queued" ? 150 : btn.implicitWidth
    implicitHeight: small ? tk.buttonSmallHeight : tk.buttonHeight

    LButton {
        id: btn
        visible: !a.busy
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        small: a.small
        kind: a.state_ === "available" ? a.installKind
            : (a.state_ === "installed" && a.openWhenInstalled) ? "plain"
            : (a.state_ === "queued" || a.state_ === "unsupported") ? "plain" : "done"
        icon: (kind === "done") ? "check" : ""
        enabledLook: a.state_ !== "queued" && a.state_ !== "unsupported"
        text: a.state_ === "available" ? a.installText
            : a.state_ === "queued" ? l10n.text("Waiting…")
            : a.state_ === "unsupported" ? l10n.text("Not for this computer")
            : a.state_ === "system" ? l10n.text("Built in")
            : a.openWhenInstalled ? l10n.text("Open") : l10n.text("Installed")
        onClicked: {
            if (a.state_ === "available") a.install()
            else if (a.state_ === "installed" || a.state_ === "system") a.open()
        }
    }
    Column {                 // "Installing 45%" over a recessed progress track (pebble .prog)
        id: bar
        visible: a.busy
        anchors.verticalCenter: parent.verticalCenter
        width: parent.width
        spacing: 6
        Text {
            font.pointSize: store.t.fontMeta
            font.weight: Font.DemiBold
            color: a.tk.accentText
            text: (a.state_ === "removing" ? l10n.text("Removing…")
                 : a.state_ === "updating" ? l10n.text("Updating…") : l10n.text("Installing…"))
                  + (a.progress > 0 && a.state_ !== "removing" ? "  " + Math.round(a.progress * 100) + "%" : "")
        }
        Well {
            width: parent.width
            height: 10
            radius: 6
            strong: true
            Rectangle {
                width: Math.max(10, parent.width * (a.state_ === "removing" ? 1 : a.progress))
                height: parent.height
                radius: parent.radius
                color: a.tk.accent
                opacity: a.state_ === "removing" ? 0.45 : 1
                Behavior on width { NumberAnimation { duration: 180 } }
            }
        }
    }
}
