// A scrolling page body with the pane's side margins (lucent.css .pane: 34px 56px).
import QtQuick
import QtQuick.Controls

Flickable {
    id: f
    default property alias content: col.data
    property alias spacing: col.spacing
    readonly property real innerWidth: width - 2 * store.t.paneX
    contentWidth: width
    contentHeight: col.implicitHeight + 48
    clip: true
    boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
    Column {
        id: col
        x: store.t.paneX
        width: f.innerWidth
        spacing: 0
    }
}
