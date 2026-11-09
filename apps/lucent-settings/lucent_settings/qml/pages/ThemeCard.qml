import QtQuick
import QtQuick.Effects
import QtQuick.Layouts
import QtQuick.Shapes
import Lucent

// One of the three theme choices (docs/mockups/03-settings .th): a 200 px
// preview, then radio + name + glyph (Auto: a hint on the right).
Rectangle {
    id: card
    property string mode            // light | dark | auto
    property string title
    property string hint
    property string icon
    property bool checked: false
    signal picked()
    Layout.fillWidth: true
    implicitHeight: 10 + Theme.previewHeight + 50
    radius: Theme.radiusChoice
    color: Theme.card
    border.width: 2
    border.color: checked ? Theme.accent : Theme.line
    Rectangle {  // box-shadow: 0 0 0 4px accent-soft
        visible: card.checked
        anchors.fill: parent
        anchors.margins: -Theme.ringWidth
        radius: Theme.radiusChoice + Theme.ringWidth
        color: "transparent"
        border.width: Theme.ringWidth
        border.color: Theme.accentSoft
    }

    Item {
        id: pv
        x: 10; y: 10
        width: parent.width - 20
        height: Theme.previewHeight
        visible: false
        layer.enabled: true
        Preview { anchors.fill: parent; dark: card.mode === "dark" }
        Preview {
            id: darkHalf
            anchors.fill: parent
            dark: true
            visible: false
            layer.enabled: true
        }
        MultiEffect {   // clip-path: polygon(100% 0, 100% 100%, 0 100%)
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
                    PathPolyline { path: [Qt.point(tri.width, 0), Qt.point(tri.width, tri.height), Qt.point(0, tri.height), Qt.point(tri.width, 0)] }
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
        spacing: 12
        Radio { checked: card.checked }
        LText { text: card.title; px: Theme.fontLabel; weight: Theme.weightStrong }
        Sym { name: card.icon; size: 20; color: Theme.text2; visible: card.icon !== "" }
        Item { Layout.fillWidth: true }
        LText { text: card.hint; px: Theme.fontSub; color: Theme.text2; visible: text !== ""; Layout.maximumWidth: 280 }
    }
    MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: card.picked() }
}
