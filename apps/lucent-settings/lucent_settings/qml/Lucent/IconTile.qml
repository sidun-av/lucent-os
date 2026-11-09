import QtQuick

// A rounded tile with a line glyph at the start of a row: a flat
// --state-hover tint (glass.css), nothing sunken or raised.
Well {
    id: tile
    flat: true
    tint: Theme.hover
    property string icon
    property color glyph: Theme.text2
    width: Theme.iconTile
    height: Theme.iconTile
    radius: Theme.radiusTile
    Sym { anchors.centerIn: parent; name: tile.icon; size: Theme.iconGlyph; color: tile.glyph }
}
