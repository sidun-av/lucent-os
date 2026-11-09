import QtQuick

// A rounded tile with a glyph at the start of a row: coloured with a white
// glyph (like the sidebar squares), or quiet (field + secondary glyph).
Rectangle {
    property string icon
    property color tint: "transparent"
    readonly property bool coloured: tint.a > 0
    width: Theme.iconTile
    height: Theme.iconTile
    radius: Theme.radiusTile
    color: coloured ? tint : Theme.field
    Sym { anchors.centerIn: parent; name: parent.icon; size: Theme.iconGlyph; color: parent.coloured ? "#ffffff" : Theme.text2 }
}
