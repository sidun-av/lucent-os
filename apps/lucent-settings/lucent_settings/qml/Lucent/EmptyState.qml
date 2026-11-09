import QtQuick
import QtQuick.Layouts

// A card that explains why a page has nothing to show.
Card {
    id: es
    property string icon
    property string title
    property string text
    Item {
        Layout.fillWidth: true
        implicitHeight: inner.implicitHeight + 40
        ColumnLayout {
            id: inner
            y: 20
            anchors.horizontalCenter: parent.horizontalCenter
            width: Math.min(parent.width - 48, 640)
            spacing: 10
            Well {
                Layout.alignment: Qt.AlignHCenter
                Layout.bottomMargin: 4
                implicitWidth: 60; implicitHeight: 60
                radius: Theme.radiusCard
                Sym { anchors.centerIn: parent; name: es.icon; size: 28; color: Theme.text2 }
            }
            LText { Layout.fillWidth: true; horizontalAlignment: Text.AlignHCenter; text: es.title; px: Theme.fontCardTitle; weight: Theme.weightCardTitle }
            LText {
                Layout.fillWidth: true
                text: es.text
                px: Theme.fontBody
                color: Theme.text2
                wrapMode: Text.WordWrap
                elide: Text.ElideNone
                horizontalAlignment: Text.AlignHCenter
                lineHeight: 1.2
            }
        }
    }
}
