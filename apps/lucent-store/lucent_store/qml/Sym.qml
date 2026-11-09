// A 24 px line symbol from the mockups (icons/sym-*.svg) in any colour.
import QtQuick
import QtQuick.Window

Image {
    property string name
    property color tint: store.t.text
    property int size: 20
    width: size
    height: size
    sourceSize: Qt.size(size * Screen.devicePixelRatio, size * Screen.devicePixelRatio)
    source: name ? "image://sym/" + name + "/" + String(tint).substring(1) : ""
    smooth: true
    cache: true
}
