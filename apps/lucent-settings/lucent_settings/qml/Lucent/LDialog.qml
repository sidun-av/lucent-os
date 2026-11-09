import QtQuick
import QtQuick.Controls.Basic as C
import QtQuick.Layouts

// A small modal sheet: title, plain-words text, optional content, buttons.
C.Popup {
    id: d
    property string title
    property string text
    property string acceptText: System.tr("OK")
    property string rejectText: System.tr("Cancel")
    property bool destructive: false
    property bool acceptEnabled: true
    default property alias extra: more.data
    signal accepted()
    signal rejected()
    modal: true
    focus: true
    anchors.centerIn: C.Overlay.overlay
    width: 520
    padding: 28
    closePolicy: C.Popup.CloseOnEscape | C.Popup.CloseOnPressOutside
    C.Overlay.modal: Rectangle { color: Theme.scrim }
    background: Rectangle {
        radius: Theme.radiusDialog
        color: Theme.popup
        border.color: Theme.line
    }
    contentItem: ColumnLayout {
        spacing: 0
        LText { text: d.title; px: Theme.fontDialogTitle; weight: Theme.weightHeading; Layout.fillWidth: true; wrapMode: Text.WordWrap; elide: Text.ElideNone }
        LText {
            text: d.text
            visible: text !== ""
            px: Theme.fontBody
            color: Theme.text2
            wrapMode: Text.WordWrap
            elide: Text.ElideNone
            lineHeight: 1.2
            Layout.fillWidth: true
            Layout.topMargin: 10
        }
        ColumnLayout { id: more; Layout.fillWidth: true; Layout.topMargin: children.length ? 18 : 0; spacing: 10 }
        RowLayout {
            Layout.topMargin: 24
            Layout.alignment: Qt.AlignRight
            spacing: 12
            LButton { text: d.rejectText; onClicked: { d.rejected(); d.close() } }
            LButton {
                text: d.acceptText
                primary: !d.destructive
                danger: d.destructive
                enabled: d.acceptEnabled
                onClicked: d.accepted()
            }
        }
    }
}
