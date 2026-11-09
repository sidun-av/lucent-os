import QtQuick
import QtQuick.Effects
import QtQuick.Layouts
import QtQuick.Shapes
import Lucent

// .mode: a sunken tile with a 170 px preview; chosen = light card, accent ring.
Item {
    id: card
    property string mode            // light | dark | auto
    property string title
    property string hint
    property bool checked: false
    property string dayWallpaper
    property string nightWallpaper
    signal picked()
    Layout.fillWidth: true
    implicitHeight: 8 + Theme.previewHeight + 50

    Well { anchors.fill: parent; radius: Theme.radiusChoice; visible: !card.checked }
    Item {
        anchors.fill: parent
        visible: card.checked
        Shadow { anchors.fill: parent; radius: Theme.radiusChoice }
        Rectangle {
            anchors.fill: parent; anchors.margins: -Theme.ringWidth
            radius: Theme.radiusChoice + Theme.ringWidth
            color: Theme.accent
        }
        Rectangle { anchors.fill: parent; radius: Theme.radiusChoice; color: Theme.selectedCard }
    }

    Item {
        id: pv
        x: 8; y: 8
        width: parent.width - 16
        height: Theme.previewHeight
        visible: false
        layer.enabled: true
        Preview { anchors.fill: parent; dark: card.mode === "dark"; wallpaper: card.mode === "dark" ? card.nightWallpaper : card.dayWallpaper }
        Preview {
            id: darkHalf
            anchors.fill: parent
            dark: true
            wallpaper: card.nightWallpaper
            visible: false
            layer.enabled: true
        }
        MultiEffect {   // .half: clip-path polygon(62% 0, 100% 0, 100% 100%, 38% 100%)
            anchors.fill: parent
            visible: card.mode === "auto"
            source: darkHalf
            maskEnabled: true
            maskSource: tri
            maskThresholdMin: 0.5
            maskSpreadAtMin: 0.2
        }
        Item {
            id: tri
            anchors.fill: parent
            visible: false
            layer.enabled: true
            Shape {
                anchors.fill: parent
                preferredRendererType: Shape.CurveRenderer
                ShapePath {
                    strokeWidth: -1
                    fillColor: "black"
                    PathPolyline { path: [Qt.point(tri.width * 0.62, 0), Qt.point(tri.width, 0), Qt.point(tri.width, tri.height),
                                          Qt.point(tri.width * 0.38, tri.height), Qt.point(tri.width * 0.62, 0)] }
                }
            }
        }
    }
    Item {
        id: round
        anchors.fill: pv
        visible: false
        layer.enabled: true
        Rectangle { anchors.fill: parent; radius: Theme.radiusPreview; color: "black" }
    }
    MultiEffect {
        anchors.fill: pv
        source: pv
        maskEnabled: true
        maskSource: round
        maskThresholdMin: 0.5
        maskSpreadAtMin: 1.0
    }

    RowLayout {
        anchors { left: parent.left; right: parent.right; bottom: parent.bottom; leftMargin: 16; rightMargin: 16; bottomMargin: 13 }
        spacing: 10
        Radio { checked: card.checked }
        LText { text: card.title; px: Theme.fontLabel; weight: Theme.weightHeading }
        Item { Layout.fillWidth: true }
        LText { text: card.hint; px: Theme.fontSub; color: Theme.text2; visible: text !== ""; Layout.maximumWidth: 300 }
    }
    MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: card.picked() }
}
