import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

// .page: title and lead, then cards; scrolls.
Flickable {
    id: page
    default property alias content: col.data
    property string title
    property string lead
    clip: true
    contentWidth: width
    contentHeight: col.implicitHeight + Theme.panePadTop + 30
    boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: ScrollBar {
        policy: page.contentHeight > page.height ? ScrollBar.AsNeeded : ScrollBar.AlwaysOff
        contentItem: Rectangle { implicitWidth: 6; radius: 3; color: Theme.line2 }
    }
    ColumnLayout {
        id: col
        x: Theme.panePadLeft
        y: Theme.panePadTop
        width: Math.min(Theme.paneMaxWidth, page.width - Theme.panePadLeft - Theme.panePadRight)
        spacing: Theme.cardGap
        PageHeader { title: page.title; lead: page.lead; Layout.bottomMargin: Theme.leadBottom - Theme.cardGap }
    }
}
