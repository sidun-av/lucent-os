import QtQuick

// .keycap: 14/650 on card-2, hairline with a 2.5 px bottom edge.
Item {
    property alias text: t.text
    implicitWidth: t.implicitWidth + 20
    implicitHeight: 28
    Rectangle {
        anchors.fill: parent
        radius: Theme.radiusKey
        color: Theme.lineStrong
    }
    Rectangle {
        anchors { fill: parent; leftMargin: 1; rightMargin: 1; topMargin: 1; bottomMargin: 2.5 }
        radius: Theme.radiusKey - 1
        color: Theme.card2
    }
    LText { id: t; anchors.centerIn: parent; anchors.verticalCenterOffset: -1; px: Theme.fontSub; weight: Theme.weightHeading }
}
