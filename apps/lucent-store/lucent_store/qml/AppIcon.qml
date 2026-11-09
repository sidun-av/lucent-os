// An app icon (Lucent tiles, icon theme, or Flathub's cached icon).
import QtQuick
import QtQuick.Window

Image {
    property string appId
    property string src: appId ? "image://app/" + appId : ""
    property int size: 64
    width: size
    height: size
    sourceSize: Qt.size(size * Screen.devicePixelRatio, size * Screen.devicePixelRatio)
    source: src
    smooth: true
    mipmap: true
    asynchronous: true
}
