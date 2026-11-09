import QtQuick
import QtQuick.Controls.Basic as C

// A drop-down on a raised pillow (model: [{value, label}]).
C.ComboBox {
    id: c
    property string current
    signal picked(string value)
    textRole: "label"
    valueRole: "value"
    implicitHeight: Theme.controlHeight
    implicitWidth: 260
    font.family: Theme.font
    font.pixelSize: Theme.fontBody
    currentIndex: {
        for (var i = 0; i < (model ? model.length : 0); i++)
            if (model[i].value === current) return i
        return -1
    }
    onActivated: (i) => c.picked(model[i].value)
    background: Raised { radius: Theme.radiusControl; lifted: c.hovered }
    contentItem: LText {
        leftPadding: 14
        rightPadding: 36
        text: c.displayText
        px: Theme.fontBody
        weight: Theme.weightButton
    }
    indicator: Sym {
        x: c.width - width - 12
        y: (c.height - height) / 2
        name: "down"
        size: 16
        color: Theme.text2
    }
    delegate: C.ItemDelegate {
        required property var modelData
        required property int index
        width: c.popup.width - 12
        x: 6
        height: 38
        highlighted: c.highlightedIndex === index
        background: Rectangle { radius: Theme.radiusControl - 2; color: parent.highlighted ? Theme.hover : "transparent" }
        contentItem: LText {
            text: modelData.label
            px: Theme.fontBody
            weight: c.currentIndex === index ? Theme.weightStrong : 400
            color: c.currentIndex === index ? Theme.accentText : Theme.text
            leftPadding: 4
        }
    }
    popup: C.Popup {
        y: c.height + 6
        width: Math.max(c.width, 220)
        implicitHeight: Math.min(contentItem.implicitHeight + 12, 420)
        padding: 6
        contentItem: ListView {
            clip: true
            implicitHeight: contentHeight
            model: c.popup.visible ? c.delegateModel : null
            currentIndex: c.highlightedIndex
            C.ScrollBar.vertical: C.ScrollBar {}
        }
        background: Raised { radius: Theme.radiusPopup; lifted: true }
    }
}
