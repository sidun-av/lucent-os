// Section heading with an optional pill, an optional link at the right end,
// and a one-line explanation (.sh, .shp in 06-store.html).
import QtQuick

Column {
    id: s
    property string title
    property string subtitle
    property string pill: ""
    property string pillIcon: ""
    property string action: ""
    property string actionIcon: ""
    property int topGap: store.t.sectionGap
    signal actionClicked()
    readonly property var tk: store.t
    width: parent ? parent.width : 800
    topPadding: topGap
    spacing: 6
    Item {
        width: parent.width
        height: Math.max(head.implicitHeight, link.visible ? link.implicitHeight : 0)
        Row {
            id: head
            x: 2
            anchors.verticalCenter: parent.verticalCenter
            spacing: 14
            Text {
                text: s.title
                font.pointSize: store.t.fontH2
                font.weight: Font.Bold
                font.letterSpacing: -0.2
                color: s.tk.text
                anchors.verticalCenter: parent.verticalCenter
            }
            Rectangle {
                visible: s.pill !== ""
                anchors.verticalCenter: parent.verticalCenter
                height: 26
                radius: height / 2
                width: pr.implicitWidth + 20
                color: s.tk.warnSoft
                Row {
                    id: pr
                    anchors.centerIn: parent
                    spacing: 6
                    Sym { name: s.pillIcon; size: 14; tint: s.tk.warn; anchors.verticalCenter: parent.verticalCenter
                          visible: s.pillIcon !== "" }
                    Text { text: s.pill; font.pointSize: store.t.fontMeta; font.weight: Font.DemiBold; color: s.tk.warn
                           anchors.verticalCenter: parent.verticalCenter }
                }
            }
        }
        LButton {
            id: link
            visible: s.action !== ""
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            kind: "ghost"
            small: true
            icon: s.actionIcon
            text: s.action
            onClicked: s.actionClicked()
        }
    }
    Text {
        x: 2
        visible: s.subtitle !== ""
        width: parent.width - 4
        text: s.subtitle
        wrapMode: Text.WordWrap
        font.pointSize: store.t.fontBody
        color: s.tk.text2
        bottomPadding: 12
    }
}
