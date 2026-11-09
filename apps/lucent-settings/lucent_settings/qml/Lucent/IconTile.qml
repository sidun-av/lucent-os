import QtQuick

// A rounded sunken tile with a line glyph at the start of a row.
Well {
    id: tile
    property string icon
    property color glyph: Theme.text2
    width: Theme.iconTile
    height: Theme.iconTile
    radius: Theme.radiusTile
    Sym { anchors.centerIn: parent; name: tile.icon; size: Theme.iconGlyph; color: tile.glyph }
}
