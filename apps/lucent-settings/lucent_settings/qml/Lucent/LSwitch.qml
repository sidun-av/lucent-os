import QtQuick

// .tog: 52 x 30 rounded-rect well, 24 px pillow knob; accent when on.
Item {
    id: sw
    property bool checked: false
    signal toggled(bool on)
    implicitWidth: Theme.switchWidth
    implicitHeight: Theme.switchHeight
    opacity: enabled ? 1 : 0.45
    Well {
        anchors.fill: parent
        radius: Theme.radiusSwitch
        flat: true      // --track: a flat tint, no inner shadow
        tint: sw.checked ? Theme.accent : Theme.track
    }
    Raised {
        width: sw.height - 6; height: width
        y: 3
        x: sw.checked ? sw.width - width - 3 : 3
        radius: Theme.radiusKnob
        topColor: Theme.knobTop; bottomColor: Theme.knobBottom
        Behavior on x { NumberAnimation { duration: 120; easing.type: Easing.OutCubic } }
    }
    MouseArea {
        anchors.fill: parent
        anchors.margins: -6
        enabled: sw.enabled
        cursorShape: Qt.PointingHandCursor
        onClicked: { sw.checked = !sw.checked; sw.toggled(sw.checked) }
    }
}
