import QtQuick
import org.lucent.chrome

// The buttons of one side of the header row in kwinrc's order
// ([org.kde.kdecoration2] ButtonsOnLeft / ButtonsOnRight, followed live):
//   M  the app icon (click: KWin's window menu)  I minimise  A maximise
//   X  close  _ a gap. Other KWin buttons (on all desktops, keep above, ...)
//   have no place in Lucent's header and are skipped.
Row {
    id: row
    required property WindowFrame frame
    property string side: "right"
    property string appIcon: ""          // icon-theme name for M
    readonly property string order: side === "left" ? frame.buttonsLeft : frame.buttonsRight
    readonly property bool empty: {
        for (var i = 0; i < order.length; i++) if ("MIAX".indexOf(order[i]) >= 0) return false
        return true
    }
    spacing: 2

    Repeater {
        model: row.order.split("")
        delegate: Loader {
            required property string modelData
            anchors.verticalCenter: parent ? parent.verticalCenter : undefined
            sourceComponent: modelData === "I" || modelData === "A" || modelData === "X" ? button
                           : modelData === "M" ? menuButton
                           : modelData === "_" ? gap : null
            property string kind: modelData === "I" ? "minimize" : modelData === "A" ? "maximize" : "close"
        }
    }
    Component {
        id: button
        WindowButton { frame: row.frame; kind: parent.kind }
    }
    Component { id: gap; Item { width: 10; height: 36 } }
    Component {
        id: menuButton
        Item {
            implicitWidth: 36
            implicitHeight: 36
            Rectangle {
                anchors.fill: parent; radius: 10
                visible: m.containsMouse
                color: row.frame.dark ? Qt.rgba(220/255, 228/255, 1, .07) : Qt.rgba(48/255, 58/255, 120/255, .065)
            }
            Image {
                anchors.centerIn: parent
                width: 28; height: 28
                sourceSize: Qt.size(28 * Screen.devicePixelRatio, 28 * Screen.devicePixelRatio)
                source: row.appIcon ? "image://lucent-chrome-icon/" + row.appIcon : ""
                smooth: true
            }
            MouseArea {
                id: m
                anchors.fill: parent
                hoverEnabled: true
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                onClicked: row.frame.showWindowMenu()
                onDoubleClicked: row.frame.close()       // as KWin's menu button
            }
        }
    }
}
