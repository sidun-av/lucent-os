import QtQuick
import QtQuick.Layouts

// A message under the page title: error (red) or info (accent).
Rectangle {
    id: bn
    property alias text: t.text
    property string kind: "error"
    signal dismissed()
    Layout.fillWidth: true
    implicitHeight: t.implicitHeight + 28
    visible: text !== ""
    radius: Theme.radiusBanner
    color: kind === "error" ? Theme.dangerSoft : Theme.accentSoft
    RowLayout {
        anchors { fill: parent; leftMargin: 16; rightMargin: 8 }
        spacing: 12
        Sym { name: "info"; color: bn.kind === "error" ? Theme.danger : Theme.accentText; size: 20 }
        LText { id: t; Layout.fillWidth: true; wrapMode: Text.WordWrap; elide: Text.ElideNone; px: Theme.fontBody }
        LButton { flat: true; icon: "x"; text: ""; h: 32; onClicked: bn.dismissed() }
    }
}
