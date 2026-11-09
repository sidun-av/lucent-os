import QtQuick
import QtQuick.Layouts

// A small heading between cards (used sparingly; cards carry their own titles).
RowLayout {
    property alias text: t.text
    default property alias extra: more.data
    Layout.fillWidth: true
    Layout.topMargin: Theme.groupTop
    Layout.bottomMargin: Theme.groupBottom
    Layout.leftMargin: 4
    Layout.rightMargin: 4
    LText { id: t; px: Theme.fontSub; weight: Theme.weightHeading; color: Theme.text3; Layout.fillWidth: true }
    RowLayout { id: more; spacing: 8 }
}
