import QtQuick

// A key: a small pillow.
Item {
    property alias text: t.text
    implicitWidth: t.implicitWidth + 20
    implicitHeight: 28
    Raised { anchors.fill: parent; radius: Theme.radiusKey }
    LText { id: t; anchors.centerIn: parent; px: Theme.fontSub; weight: Theme.weightHeading }
}
