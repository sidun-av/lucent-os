import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

// .pane: 40 px / 64 px padding, content at most 1300 px wide, scrolls.
Flickable {
    id: page
    default property alias content: col.data
    property string title
    property string lead
    property bool active: false
    clip: true
    contentWidth: width
    contentHeight: col.implicitHeight + 2 * Theme.panePadV
    boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: ScrollBar {
        policy: page.contentHeight > page.height ? ScrollBar.AsNeeded : ScrollBar.AlwaysOff
        contentItem: Rectangle { implicitWidth: 6; radius: 3; color: Theme.lineStrong }
    }
    ColumnLayout {
        id: col
        x: Theme.panePadH
        y: Theme.panePadV
        width: Math.min(Theme.paneMaxWidth, page.width - 2 * Theme.panePadH)
        spacing: 0
        PageHeader { title: page.title; lead: page.lead }
    }
}
