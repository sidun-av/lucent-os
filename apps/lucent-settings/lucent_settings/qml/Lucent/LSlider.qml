import QtQuick
import QtQuick.Controls.Basic as C

// .slider: 6 px field track, accent fill, 22 px white knob.
C.Slider {
    id: s
    implicitWidth: 280
    implicitHeight: Theme.sliderKnob + 4
    snapMode: C.Slider.SnapAlways
    background: Rectangle {
        x: s.leftPadding
        y: s.topPadding + s.availableHeight / 2 - Theme.sliderTrack / 2
        width: s.availableWidth
        height: Theme.sliderTrack
        radius: Theme.sliderTrack / 2
        color: Theme.field
        Rectangle {
            width: s.visualPosition * parent.width
            height: parent.height
            radius: Theme.sliderTrack / 2
            color: Theme.accent
        }
    }
    handle: Rectangle {
        x: s.leftPadding + s.visualPosition * (s.availableWidth - width)
        y: s.topPadding + s.availableHeight / 2 - Theme.sliderKnob / 2
        width: Theme.sliderKnob; height: Theme.sliderKnob; radius: Theme.sliderKnob / 2
        color: "#ffffff"
        border.color: Qt.rgba(0, 0, 0, 0.18)
        border.width: 0.5
        Rectangle {
            z: -1
            anchors.fill: parent
            anchors.topMargin: 1
            anchors.bottomMargin: -1
            radius: Theme.sliderKnob / 2
            color: Qt.rgba(0, 0, 0, 0.15)
        }
    }
}
