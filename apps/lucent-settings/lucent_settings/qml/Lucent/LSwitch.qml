import QtQuick

// .switch: 44 x 26, knob 20, accent when on.
Item {
    id: sw
    property bool checked: false
    signal toggled(bool on)
    implicitWidth: Theme.switchWidth
    implicitHeight: Theme.switchHeight
    opacity: enabled ? 1 : 0.45
    Rectangle {
        anchors.fill: parent
        radius: height / 2
        color: sw.checked ? Theme.accent : Theme.lineStrong
        Behavior on color { ColorAnimation { duration: 120 } }
    }
    Rectangle {
        width: sw.height - 6; height: width; radius: width / 2
        y: 3
        x: sw.checked ? sw.width - width - 3 : 3
        color: "#ffffff"
        Behavior on x { NumberAnimation { duration: 120; easing.type: Easing.OutCubic } }
        layer.enabled: true
        border.color: Qt.rgba(0, 0, 0, 0.12)
        border.width: 0.5
    }
    MouseArea {
        anchors.fill: parent
        anchors.margins: -6
        enabled: sw.enabled
        cursorShape: Qt.PointingHandCursor
        onClicked: { sw.checked = !sw.checked; sw.toggled(sw.checked) }
    }
}
