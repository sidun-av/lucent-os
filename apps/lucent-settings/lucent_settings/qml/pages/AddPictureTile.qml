import QtQuick
import QtQuick.Layouts
import Lucent

// "Add a picture": a glass card tile that opens the file chooser.
Item {
    signal clicked()
    Layout.fillWidth: true
    Layout.alignment: Qt.AlignTop
    implicitHeight: 138
    Well {
        anchors.fill: parent
        radius: Theme.radiusThumb
        Column {
            anchors.centerIn: parent
            spacing: 8
            Sym { anchors.horizontalCenter: parent.horizontalCenter; name: "plus"; size: 26; color: Theme.text2 }
            LText { text: System.tr("Add a picture"); px: Theme.fontBody; weight: Theme.weightStrong; color: Theme.text2 }
        }
    }
    MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: parent.clicked() }
}
