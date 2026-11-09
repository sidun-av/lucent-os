// A short message at the bottom: an app finished installing, or what went wrong.
import QtQuick

Rectangle {
    id: t
    property string kind: "done"
    property string title
    property string detail
    readonly property var tk: store.t
    function show(k, ti, de) { kind = k; title = ti; detail = de; opacity = 1; hide.restart() }
    anchors.horizontalCenter: parent.horizontalCenter
    anchors.horizontalCenterOffset: 145
    y: parent.height - height - 28
    width: Math.min(620, Math.max(360, col.implicitWidth + 90))
    height: col.implicitHeight + 28
    radius: store.t.radiusShot
    color: tk.card
    border.width: 1
    border.color: tk.lineStrong
    opacity: 0
    visible: opacity > 0
    Behavior on opacity { NumberAnimation { duration: 200 } }
    Sym { id: ic; x: 18; y: 16; size: 22; name: t.kind === "error" ? "info" : "check"
          tint: t.kind === "error" ? t.tk.danger : t.tk.ok }
    Column {
        id: col
        anchors.left: ic.right
        anchors.leftMargin: 12
        anchors.right: close.left
        anchors.rightMargin: 10
        y: 14
        spacing: 2
        Text { width: parent.width; text: t.title; font.pointSize: store.t.fontText; font.weight: Font.DemiBold; color: t.tk.text; wrapMode: Text.WordWrap }
        Text { width: parent.width; text: t.detail; font.pointSize: store.t.fontCaption; color: t.tk.text2; wrapMode: Text.WordWrap; visible: text !== "" }
    }
    Sym { id: close; name: "x"; size: 16; tint: t.tk.text3; anchors.right: parent.right; anchors.rightMargin: 16; y: 18
          MouseArea { anchors.fill: parent; anchors.margins: -8; onClicked: t.opacity = 0 } }
    Timer { id: hide; interval: t.kind === "error" ? 12000 : 5000; onTriggered: t.opacity = 0 }
}
