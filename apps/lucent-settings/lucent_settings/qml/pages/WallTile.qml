import QtQuick
import QtQuick.Effects
import QtQuick.Layouts
import Lucent

// A wallpaper tile (04-settings): rounded picture, accent ring when in use,
// name and a short line under it.
ColumnLayout {
    id: t
    property var tile: ({})
    property string current
    // a day/night pair shares one wallpaper: the half that shows now is "in use"
    readonly property bool on: tile.path === current
        && (tile.variant !== "day" && tile.variant !== "night" || tile.variant === (Theme.dark ? "night" : "day"))
    signal picked(string path)
    Layout.fillWidth: true
    Layout.alignment: Qt.AlignTop
    spacing: 10
    Item {
        Layout.fillWidth: true
        implicitHeight: 138
        Rectangle {  // 0 0 0 3px raised, 0 0 0 5.5px accent
            visible: t.on
            anchors.fill: parent; anchors.margins: -5.5
            radius: Theme.radiusThumb + 5.5
            color: Theme.accent
            Rectangle { anchors.fill: parent; anchors.margins: 2.5; radius: Theme.radiusThumb + 3; color: Theme.raised }
        }
        Shadow { anchors.fill: parent; radius: Theme.radiusThumb }
        Image {
            id: img
            anchors.fill: parent
            source: t.tile.thumb || ""
            sourceSize: Qt.size(560, 320)
            fillMode: Image.PreserveAspectCrop
            asynchronous: true
            visible: false
        }
        Item { id: mask; anchors.fill: parent; visible: false; layer.enabled: true
               Rectangle { anchors.fill: parent; radius: Theme.radiusThumb; color: "black" } }
        MultiEffect { anchors.fill: parent; source: img; maskEnabled: true; maskSource: mask
                      maskThresholdMin: 0.5; maskSpreadAtMin: 1.0 }
        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: t.picked(t.tile.path) }
    }
    ColumnLayout {
        spacing: 1
        Layout.fillWidth: true
        LText {
            Layout.fillWidth: true
            text: t.tile.variant === "night" ? System.tr("{name} night").replace("{name}", t.tile.name) : (t.tile.name || "")
            px: Theme.fontBody; weight: Theme.weightStrong
        }
        LText {
            Layout.fillWidth: true
            text: t.on ? System.tr("In use")
                : t.tile.variant === "night" ? System.tr("For dark mode")
                : t.tile.variant === "picture" ? System.tr("Your picture")
                : t.tile.dayNight ? ((t.tile.about ? t.tile.about + " · " : "") + System.tr("day and night"))
                : (t.tile.about || System.tr("Included"))
            px: Theme.fontSmall
            weight: t.on ? Theme.weightStrong : 400
            color: t.on ? Theme.accentText : Theme.text2
        }
    }
}
