import QtQuick
import QtQuick.Layouts

// .group: white card, hairline border, 14 px corners; rows stack inside.
Rectangle {
    id: card
    default property alias rows: col.data
    property alias spacing: col.spacing
    Layout.fillWidth: true
    implicitHeight: col.implicitHeight + 2
    radius: Theme.radiusCard
    color: Theme.card
    border.color: Theme.line
    border.width: 1
    clip: true
    ColumnLayout {
        id: col
        x: 1; y: 1
        width: parent.width - 2
        spacing: 0
    }
}
