import QtQuick

// .radio: a small pillow; checked = accent with a white dot.
Item {
    property bool checked: false
    width: Theme.radio; height: Theme.radio
    Rectangle {
        anchors.fill: parent
        radius: width / 2
        color: parent.checked ? Theme.accent : Theme.raised
        border.width: parent.checked ? 0 : 1.5
        border.color: Theme.line2
    }
    Rectangle {
        visible: parent.checked
        anchors.centerIn: parent
        width: 8; height: 8; radius: 4
        color: Theme.textOnAccent
    }
}
