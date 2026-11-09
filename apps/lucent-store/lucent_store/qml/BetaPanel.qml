// "Next generation · beta": the warning and the ArtCraft apps (.beta in 06-store.html).
import QtQuick
import QtQuick.Layouts
import QtQuick.Shapes

Item {
    id: p
    property int columns: 3
    readonly property var tk: store.t
    implicitHeight: col.implicitHeight + 48

    Shape {
        anchors.fill: parent
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            strokeColor: p.tk.betaLine
            strokeWidth: 1
            fillGradient: LinearGradient {
                x1: 0; y1: 0; x2: p.width; y2: p.height
                GradientStop { position: 0.0; color: p.tk.betaA }
                GradientStop { position: 0.6; color: p.tk.betaB }
                GradientStop { position: 1.0; color: p.tk.betaC }
            }
            PathRectangle { x: 0.5; y: 0.5; width: p.width - 1; height: p.height - 1; radius: store.t.radiusPanel }
        }
    }
    Column {
        id: col
        x: 24
        y: 24
        width: parent.width - 48
        spacing: 20
        Rectangle {
            width: parent.width
            height: note.implicitHeight + 24
            radius: store.t.radiusField
            color: p.tk.betaNoteBg
            Sym { id: ni; name: "info"; size: 20; tint: p.tk.warn; x: 16; anchors.verticalCenter: parent.verticalCenter }
            Text {
                id: note
                anchors.left: ni.right
                anchors.leftMargin: 12
                anchors.right: parent.right
                anchors.rightMargin: 16
                anchors.verticalCenter: parent.verticalCenter
                wrapMode: Text.WordWrap
                font.pointSize: store.t.fontText
                color: p.tk.betaNoteText
                text: l10n.text("These are alpha versions: they work, but expect bugs and possible loss of unsaved work. Keep copies of important files.")
            }
        }
        GridLayout {
            width: parent.width
            readonly property var apps: store.nextgen(win.rev)
            columns: apps.length === 4 ? 2 : p.columns
            columnSpacing: store.t.rowGap
            rowSpacing: store.t.rowGap
            Repeater {
                model: parent.apps
                CraftCard {
                    required property var modelData
                    app: modelData
                    Layout.fillWidth: true
                    Layout.preferredWidth: 100
                }
            }
        }
    }
}
