import QtQuick
import QtQuick.Controls.Basic as C

// Sunken 10 px track, accent fill, a 30 x 24 pillow knob with a focus ring.
C.Slider {
    id: s
    implicitWidth: 320
    implicitHeight: Theme.sliderKnobH + 12
    snapMode: C.Slider.SnapAlways
    background: Item {
        x: s.leftPadding
        y: s.topPadding + s.availableHeight / 2 - Theme.sliderTrack / 2
        width: s.availableWidth
        height: Theme.sliderTrack
        Well { anchors.fill: parent; radius: Theme.sliderTrack / 2 + 1; tint: Theme.wellStrong }
        Rectangle {
            width: s.visualPosition * parent.width
            height: parent.height
            radius: Theme.sliderTrack / 2 + 1
            color: Theme.accent
        }
    }
    handle: Item {
        x: s.leftPadding + s.visualPosition * (s.availableWidth - width)
        y: s.topPadding + s.availableHeight / 2 - height / 2
        width: Theme.sliderKnobW; height: Theme.sliderKnobH
        Rectangle {  // 0 0 0 2px accent, 0 0 0 6px accent-soft
            anchors.fill: parent; anchors.margins: -6
            radius: Theme.radiusKnob + 6
            color: Theme.accentSoft
            visible: s.pressed || s.hovered
        }
        Rectangle {
            anchors.fill: parent; anchors.margins: -2
            radius: Theme.radiusKnob + 2
            color: Theme.accent
        }
        Raised { anchors.fill: parent; radius: Theme.radiusKnob; topColor: "#ffffff"; bottomColor: Theme.dark ? "#e3e6ef" : "#eef1f8" }
    }
}
