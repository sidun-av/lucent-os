import QtQuick

Text {
    property int px: Theme.fontBody
    property int weight: 400
    color: Theme.text
    font.family: Theme.font
    font.pixelSize: px
    font.weight: weight
    renderType: Text.NativeRendering
    elide: Text.ElideRight
    verticalAlignment: Text.AlignVCenter
}
