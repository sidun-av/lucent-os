/*
    Lucent login splash: the Lucent wallpaper, the logo and a thin progress
    line, fading out into the desktop (KSplash stages 1-6).

    SPDX-License-Identifier: Apache-2.0
*/
import QtQuick
import org.kde.kirigami as Kirigami

Rectangle {
    id: root
    property int stage

    readonly property bool dark: Kirigami.ColorUtils.brightnessForColor(Kirigami.Theme.backgroundColor) === Kirigami.ColorUtils.Dark
    color: dark ? "#0d1222" : "#e9eefb"

    Image {
        anchors.fill: parent
        source: "file:///usr/share/wallpapers/Lucent/contents/" + (root.dark ? "images_dark" : "images") + "/3840x2160.jpg"
        fillMode: Image.PreserveAspectCrop
        sourceSize.width: root.width
        asynchronous: false
    }

    Item {
        id: content
        anchors.centerIn: parent
        width: 160
        height: 96 + 40 + 4
        opacity: 0
        Image {
            anchors.horizontalCenter: parent.horizontalCenter
            width: 96
            height: 96
            source: "file:///usr/share/icons/Lucent/scalable/apps/lucent-start.svg"
            sourceSize: Qt.size(192, 192)
        }
        Rectangle {
            anchors.bottom: parent.bottom
            width: parent.width
            height: 4
            radius: 2
            color: root.dark ? Qt.rgba(1, 1, 1, 0.16) : Qt.rgba(20 / 255, 28 / 255, 45 / 255, 0.12)
            Rectangle {
                width: parent.width * Math.min(1, root.stage / 6)
                height: parent.height
                radius: 2
                color: root.dark ? "#5b8bff" : "#3b6ef5"
                Behavior on width { NumberAnimation { duration: 400; easing.type: Easing.OutCubic } }
            }
        }
    }

    onStageChanged: {
        if (stage === 1) {
            fadeIn.start()
        }
    }
    OpacityAnimator {
        id: fadeIn
        target: content
        from: 0
        to: 1
        duration: 300
        easing.type: Easing.InOutQuad
    }
}
