import QtQuick
import QtQuick.Layouts

ColumnLayout {
    property alias title: h.text
    property alias lead: l.text
    spacing: 4
    Layout.fillWidth: true
    Layout.bottomMargin: Theme.leadBottom
    LText { id: h; px: Theme.fontH1; weight: Theme.weightH1; font.letterSpacing: -0.6; Layout.fillWidth: true }
    LText {
        id: l
        px: Theme.fontLead
        color: Theme.text2
        wrapMode: Text.WordWrap
        elide: Text.ElideNone
        lineHeight: 1.15
        Layout.fillWidth: true
        Layout.maximumWidth: Theme.leadMaxWidth
        visible: text !== ""
    }
}
