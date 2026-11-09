import QtQuick
import QtQuick.Layouts

// .gh: small heading above a card (14 px / 650, 26 px above, 10 below).
RowLayout {
    property alias text: t.text
    default property alias extra: more.data
    Layout.fillWidth: true
    Layout.topMargin: Theme.groupTop
    Layout.bottomMargin: Theme.groupBottom
    Layout.leftMargin: 4
    Layout.rightMargin: 4
    LText { id: t; px: Theme.fontSub; weight: Theme.weightHeading; color: Theme.text2; Layout.fillWidth: true }
    RowLayout { id: more; spacing: 8 }
}
