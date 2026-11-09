import QtQuick
import QtQuick.Effects

// Account picture (AccountsService icon) or initials on the peach gradient.
Item {
    id: av
    property string source
    property string initials: "?"
    property int size: 52
    property real corner: size * 0.28     // Pebble: rounded square
    width: size; height: size
    Rectangle {
        anchors.fill: parent
        radius: av.corner
        visible: img.status !== Image.Ready
        gradient: Gradient {
            orientation: Gradient.Horizontal  // 135deg in the mockup
            GradientStop { position: 0; color: Theme.avatarFrom }
            GradientStop { position: 1; color: Theme.avatarTo }
        }
        LText {
            anchors.centerIn: parent
            text: av.initials
            px: Math.round(av.size * 0.33)
            weight: 750
            color: "#ffffff"
        }
    }
    Image {
        id: img
        anchors.fill: parent
        source: av.source
        sourceSize: Qt.size(av.size * 2, av.size * 2)
        fillMode: Image.PreserveAspectCrop
        cache: false
        visible: false
    }
    MultiEffect {
        anchors.fill: img
        source: img
        visible: img.status === Image.Ready
        maskEnabled: true
        maskSource: mask
        maskThresholdMin: 0.5
        maskSpreadAtMin: 1.0
    }
    Item {
        id: mask
        anchors.fill: parent
        layer.enabled: true
        visible: false
        Rectangle { anchors.fill: parent; radius: av.corner; color: "black" }
    }
}
