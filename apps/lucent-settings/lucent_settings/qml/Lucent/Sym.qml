import QtQuick

// A line symbol from the mockups' icon set, in any colour.
Image {
    id: root
    property string name
    property color color: Theme.text2
    property int size: 20
    width: size
    height: size
    sourceSize: Qt.size(Math.round(size * Screen.devicePixelRatio), Math.round(size * Screen.devicePixelRatio))
    source: name ? Theme.sym(name, color) : ""
    smooth: true
    asynchronous: false
}
