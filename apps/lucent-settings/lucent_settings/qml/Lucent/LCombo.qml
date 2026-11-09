import QtQuick
import QtQuick.Controls.Basic as C

// A field-coloured drop-down (model: [{value, label}]).
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
    background: Rectangle {
        radius: Theme.radiusControl
        color: c.hovered ? Qt.darker(Theme.field, Theme.dark ? 0.9 : 1.03) : Theme.field
        border.color: Theme.line
    }
    contentItem: LText {
        leftPadding: 14
        rightPadding: 36
        text: c.displayText
        px: Theme.fontBody
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
        background: Rectangle { radius: Theme.radiusItem - 1; color: parent.highlighted ? Theme.sel : "transparent" }
        contentItem: LText {
            text: modelData.label
            px: Theme.fontBody
            weight: c.currentIndex === index ? Theme.weightStrong : 400
            leftPadding: 4
        }
    }
    popup: C.Popup {
        y: c.height + 4
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
        background: Rectangle {
            radius: Theme.radiusPopup
            color: Theme.popup
            border.color: Theme.line
        }
    }
}
