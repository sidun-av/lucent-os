import QtQuick
import QtQuick.Layouts

// An inline message under the page title: error (red) or info (accent).
Rectangle {
    id: bn
    property alias text: t.text
    property string kind: "error"
    signal dismissed()
    Layout.fillWidth: true
    Layout.topMargin: Theme.groupTop - 6
    implicitHeight: t.implicitHeight + 28
    visible: text !== ""
    radius: Theme.radiusBanner
    color: kind === "error" ? Theme.dangerSoft : Theme.accentSoft
    border.color: kind === "error" ? Qt.rgba(210 / 255, 59 / 255, 59 / 255, 0.3) : Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.25)
    RowLayout {
        anchors { fill: parent; leftMargin: 16; rightMargin: 10 }
        spacing: 12
        Sym { name: bn.kind === "error" ? "info" : "info"; color: bn.kind === "error" ? Theme.danger : Theme.accent; size: 20 }
        LText { id: t; Layout.fillWidth: true; wrapMode: Text.WordWrap; elide: Text.ElideNone; px: Theme.fontBody }
        LButton { flat: true; icon: "x"; text: ""; h: 32; implicitWidth: 32; onClicked: bn.dismissed() }
    }
}
