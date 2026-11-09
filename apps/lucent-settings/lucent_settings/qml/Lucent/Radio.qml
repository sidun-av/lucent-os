import QtQuick

// .radio: 22 px ring; checked = 7 px accent ring.
Rectangle {
    property bool checked: false
    width: Theme.radio; height: Theme.radio; radius: Theme.radio / 2
    color: Theme.dark && !checked ? "transparent" : (checked ? "#ffffff" : Theme.winBg)
    border.width: checked ? 7 : 2
    border.color: checked ? Theme.accent : Theme.lineStrong
}
