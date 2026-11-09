import QtQuick
import QtQuick.Layouts

// .group.card: a raised pillow with its title inside (.gt / .gs), then rows.
Item {
    id: card
    property string title
    property string subtitle
    property alias headerItems: hdr.data      // e.g. a "Browse…" button next to the title
    default property alias rows: col.data
    property alias spacing: col.spacing
    property bool selected: false
    Layout.fillWidth: true
    implicitHeight: body.implicitHeight + 2 * Theme.cardPadV
    implicitWidth: 400
    Raised {
        anchors.fill: parent
        radius: Theme.radiusCard
        topColor: card.selected ? Theme.selectedCard : Theme.raised
        bottomColor: card.selected ? Theme.selectedCard2 : Theme.raised2
    }
    ColumnLayout {
        id: body
        x: Theme.cardPadH; y: Theme.cardPadV
        width: parent.width - 2 * Theme.cardPadH
        spacing: 0
        RowLayout {
            visible: card.title !== ""
            Layout.fillWidth: true
            Layout.bottomMargin: card.subtitle !== "" ? 4 : 6
            spacing: 10
            LText { text: card.title; px: Theme.fontCardTitle; weight: Theme.weightCardTitle; Layout.fillWidth: true }
            RowLayout { id: hdr; spacing: 10 }
        }
        LText {
            visible: card.subtitle !== ""
            text: card.subtitle
            px: Theme.fontSub
            color: Theme.text2
            wrapMode: Text.WordWrap
            elide: Text.ElideNone
            Layout.fillWidth: true
            Layout.bottomMargin: 6
        }
        ColumnLayout {
            id: col
            Layout.fillWidth: true
            spacing: 0
        }
    }
}
