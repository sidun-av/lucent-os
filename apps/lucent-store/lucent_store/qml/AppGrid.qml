// Apps as cards, two columns on a wide window.
import QtQuick
import QtQuick.Layouts

GridLayout {
    id: g
    property var apps: []
    property bool showRemove: false
    property bool showUpdate: false
    property var metaFor: function (app) { return "" }
    columns: width >= 1100 ? 2 : 1
    columnSpacing: store.t.rowGap
    rowSpacing: store.t.rowGap
    Repeater {
        model: g.apps
        AppRow {
            required property var modelData
            app: modelData
            meta: g.metaFor(modelData)
            showRemove: g.showRemove
            showUpdate: g.showUpdate
            Layout.fillWidth: true
            Layout.preferredWidth: 100
        }
    }
}
