import QtQuick

Text {
    property bool first: false
    topPadding: first ? 4 : 14
    bottomPadding: 6
    leftPadding: 12
    font.pointSize: store.t.fontLabel
    font.weight: Font.DemiBold
    font.letterSpacing: 0.13
    color: store.t.text3
}
