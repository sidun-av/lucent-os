/*
    Lucent login screen (SDDM, Qt 6 greeter). Same language as the Lucent
    lock screen: the dark Lucent Flow wallpaper, blurred and dimmed; a large
    clock; the user's picture or initial on Lucent's gradient; one 340 px
    rounded translucent password field with the sign-in arrow inside it; a
    row of round power actions. No on-screen keyboard button.

    Uses only QtQuick, so it doesn't depend on Plasma's QML being installed
    for the sddm user. SPDX-License-Identifier: Apache-2.0
*/
import QtQuick
import QtQuick.Effects
import QtQuick.Templates as T

Rectangle {
    id: root
    width: 1920
    height: 1080
    color: "#10131c"

    readonly property color accent: config.accent || "#5b8bff"
    readonly property string uiFont: config.font || "Inter"
    readonly property real s: Math.max(0.8, Math.min(1.25, height / 1440)) // scale with the screen
    property int userIndex: userModel.lastIndex >= 0 ? userModel.lastIndex : 0
    property int sessionIndex: sessionModel.lastIndex >= 0 ? sessionModel.lastIndex : 0
    property bool busy: false
    property string message: ""

    LayoutMirroring.enabled: Qt.application.layoutDirection === Qt.RightToLeft
    LayoutMirroring.childrenInherit: true

    function signIn() {
        if (busy || !users.currentItem) {
            return;
        }
        busy = true;
        message = "";
        sddm.login(users.currentItem.userName, password.text, sessionIndex);
    }

    Connections {
        target: sddm
        function onLoginFailed() {
            root.busy = false;
            root.message = qsTr("That password didn't work. Try again.");
            password.text = "";
            password.forceActiveFocus();
            shake.start();
        }
        function onLoginSucceeded() {
            root.message = "";
        }
        function onInformationMessage(message) {
            root.message = message;
        }
    }

    // -------------------------------------------------------- background --
    Image {
        id: wallpaper
        anchors.fill: parent
        source: config.background || ""
        fillMode: Image.PreserveAspectCrop
        sourceSize: Qt.size(root.width, root.height)
        asynchronous: false
        visible: false
    }
    MultiEffect {
        anchors.fill: parent
        source: wallpaper
        blurEnabled: true
        blurMax: 64
        blur: 0.9
        autoPaddingEnabled: false
    }
    Rectangle {
        anchors.fill: parent
        color: "#0b0f1a"
        opacity: 0.45
    }

    // users: one delegate per account; the selected one is shown big
    ListView {
        id: users
        model: userModel
        currentIndex: root.userIndex
        visible: false
        width: 1; height: 1
        delegate: Item {
            required property int index
            required property string name
            required property string realName
            required property string icon
            required property bool needsPassword
            readonly property string userName: name
            readonly property string displayName: realName !== "" ? realName : name
            readonly property string face: icon
            readonly property bool passwordNeeded: needsPassword
        }
    }

    // ------------------------------------------------------------- clock --
    Column {
        id: clock
        anchors.horizontalCenter: parent.horizontalCenter
        y: root.height * 0.12
        spacing: 2 * root.s
        property date now: new Date()
        Timer {
            interval: 1000; running: true; repeat: true
            onTriggered: clock.now = new Date()
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: Qt.formatTime(clock.now, Qt.locale().timeFormat(Locale.ShortFormat).replace(/:ss|\.ss/, ""))
            color: "white"
            font.family: root.uiFont
            font.pixelSize: 84 * root.s
            font.weight: Font.DemiBold
            font.letterSpacing: -1.5
            font.features: { "tnum": 1 }
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: clock.now.toLocaleDateString(Qt.locale(), "dddd, d MMMM")
            color: Qt.rgba(1, 1, 1, 0.86)
            font.family: root.uiFont
            font.pixelSize: 19 * root.s
            font.weight: Font.Medium
        }
    }

    // ------------------------------------------------------------ prompt --
    Column {
        id: prompt
        anchors.horizontalCenter: parent.horizontalCenter
        y: root.height * 0.38
        width: 340 * root.s
        spacing: 0
        transform: Translate { id: shakeX }

        SequentialAnimation {
            id: shake
            loops: 2
            NumberAnimation { target: shakeX; property: "x"; to: -10; duration: 50 }
            NumberAnimation { target: shakeX; property: "x"; to: 10; duration: 80 }
            NumberAnimation { target: shakeX; property: "x"; to: 0; duration: 50 }
        }

        Avatar {
            anchors.horizontalCenter: parent.horizontalCenter
            size: 104 * root.s
            name: users.currentItem ? users.currentItem.displayName : ""
            face: users.currentItem ? users.currentItem.face : ""
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            topPadding: 14 * root.s
            text: users.currentItem ? users.currentItem.displayName : ""
            color: "white"
            font.family: root.uiFont
            font.pixelSize: 22 * root.s
            font.weight: Font.DemiBold
        }

        Item { width: 1; height: 22 * root.s }

        Rectangle {
            id: pill
            width: parent.width
            height: 50 * root.s
            radius: height / 2
            color: Qt.rgba(1, 1, 1, password.activeFocus ? 0.20 : 0.14)
            border.width: 1
            border.color: password.activeFocus ? Qt.rgba(1, 1, 1, 0.55) : Qt.rgba(1, 1, 1, 0.25)
            Behavior on color { ColorAnimation { duration: 150 } }

            T.TextField {
                id: password
                anchors.left: parent.left
                anchors.right: go.left
                anchors.leftMargin: 22 * root.s
                anchors.rightMargin: 8
                height: parent.height
                verticalAlignment: TextInput.AlignVCenter
                echoMode: TextInput.Password
                passwordCharacter: "●"
                passwordMaskDelay: 0
                color: "white"
                selectionColor: root.accent
                selectedTextColor: "white"
                font.family: root.uiFont
                font.pixelSize: 17 * root.s
                font.letterSpacing: text.length > 0 ? 2 : 0
                focus: true
                enabled: !root.busy
                inputMethodHints: Qt.ImhHiddenText | Qt.ImhSensitiveData | Qt.ImhNoAutoUppercase | Qt.ImhNoPredictiveText
                Accessible.name: qsTr("Password")
                onAccepted: root.signIn()
                Keys.onLeftPressed: event => {
                    if (text.length === 0 && root.userIndex > 0) { root.userIndex--; } else { event.accepted = false; }
                }
                Keys.onRightPressed: event => {
                    if (text.length === 0 && root.userIndex < userModel.count - 1) { root.userIndex++; } else { event.accepted = false; }
                }
                Component.onCompleted: forceActiveFocus()
            }
            Text {
                anchors.left: password.left
                anchors.verticalCenter: password.verticalCenter
                visible: password.text.length === 0 && !password.preeditText
                text: users.currentItem && !users.currentItem.passwordNeeded ? qsTr("Press Enter to sign in") : qsTr("Password")
                color: Qt.rgba(1, 1, 1, 0.62)
                font.family: root.uiFont
                font.pixelSize: 17 * root.s
            }

            T.Button {
                id: go
                anchors.right: parent.right
                anchors.rightMargin: 6 * root.s
                anchors.verticalCenter: parent.verticalCenter
                width: 38 * root.s
                height: width
                enabled: !root.busy
                Accessible.name: qsTr("Sign in")
                onClicked: root.signIn()
                Keys.onReturnPressed: clicked()
                Keys.onEnterPressed: clicked()
                background: Rectangle {
                    radius: width / 2
                    color: go.pressed ? Qt.darker(root.accent, 1.15)
                         : go.hovered || go.activeFocus ? Qt.lighter(root.accent, 1.08)
                         : password.text.length > 0 ? root.accent : Qt.rgba(1, 1, 1, 0.18)
                    Behavior on color { ColorAnimation { duration: 150 } }
                }
                contentItem: Item {
                    Canvas {
                        anchors.centerIn: parent
                        width: 18; height: 18
                        visible: !root.busy
                        onPaint: {
                            const c = getContext("2d");
                            c.reset();
                            c.strokeStyle = "white";
                            c.lineWidth = 2;
                            c.lineCap = "round";
                            c.lineJoin = "round";
                            c.beginPath();
                            c.moveTo(3, 9); c.lineTo(15, 9); c.moveTo(10, 4); c.lineTo(15, 9); c.lineTo(10, 14);
                            c.stroke();
                        }
                    }
                    Rectangle { // busy: a small spinning arc
                        anchors.centerIn: parent
                        width: 16; height: 16; radius: 8
                        visible: root.busy
                        color: "transparent"
                        border.width: 2
                        border.color: Qt.rgba(1, 1, 1, 0.9)
                        RotationAnimation on rotation { from: 0; to: 360; duration: 900; loops: Animation.Infinite; running: root.busy }
                        Rectangle { width: 8; height: 8; color: root.accent; anchors.right: parent.right; anchors.top: parent.top }
                    }
                }
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width
            topPadding: 14 * root.s
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            color: Qt.rgba(1, 1, 1, 0.92)
            font.family: root.uiFont
            font.pixelSize: 15 * root.s
            text: {
                const parts = [];
                if (keyboard.capsLock) {
                    parts.push(qsTr("Caps Lock is on"));
                }
                if (root.message) {
                    parts.push(root.message);
                }
                return parts.join(" • ");
            }
        }

        // other accounts on this computer
        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            topPadding: 26 * root.s
            spacing: 14 * root.s
            visible: userModel.count > 1
            Repeater {
                model: userModel
                delegate: T.Button {
                    id: other
                    required property int index
                    required property var model
                    readonly property string label: model.realName !== "" ? model.realName : model.name
                    visible: index !== root.userIndex
                    width: 64 * root.s
                    height: 82 * root.s
                    onClicked: { root.userIndex = index; password.text = ""; password.forceActiveFocus(); }
                    background: Item {}
                    contentItem: Column {
                        spacing: 6
                        Avatar {
                            anchors.horizontalCenter: parent.horizontalCenter
                            size: 48 * root.s
                            name: other.label
                            face: other.model.icon
                            opacity: other.hovered ? 1 : 0.85
                        }
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            width: other.width
                            elide: Text.ElideRight
                            horizontalAlignment: Text.AlignHCenter
                            text: other.label
                            color: "white"
                            font.family: root.uiFont
                            font.pixelSize: 13 * root.s
                        }
                    }
                }
            }
        }
    }

    // ---------------------------------------------------- power actions --
    Row {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: Math.round(root.height * 0.07)
        spacing: 28 * root.s

        PowerButton {
            text: qsTr("Sleep")
            glyph: "system-suspend"
            visible: sddm.canSuspend
            onClicked: sddm.suspend()
        }
        PowerButton {
            text: qsTr("Restart")
            glyph: "system-reboot"
            visible: sddm.canReboot
            onClicked: sddm.reboot()
        }
        PowerButton {
            text: qsTr("Shut Down")
            glyph: "system-shutdown"
            visible: sddm.canPowerOff
            onClicked: sddm.powerOff()
        }
    }

    // keyboard layout, only with more than one
    T.Button {
        id: layoutButton
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        anchors.margins: 24 * root.s
        visible: keyboard.layouts.length > 1
        width: layoutText.implicitWidth + 28
        height: 34 * root.s
        onClicked: keyboard.currentLayout = (keyboard.currentLayout + 1) % keyboard.layouts.length
        background: Rectangle { radius: height / 2; color: Qt.rgba(1, 1, 1, layoutButton.hovered ? 0.22 : 0.14) }
        contentItem: Text {
            id: layoutText
            text: keyboard.layouts.length > 0 ? keyboard.layouts[keyboard.currentLayout].shortName.toUpperCase() : ""
            color: "white"
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            font.family: root.uiFont
            font.pixelSize: 14 * root.s
            font.weight: Font.Bold
        }
    }

    // ------------------------------------------------------- components --
    component Avatar: Item {
        id: av
        property real size: 104
        property string name: ""
        property string face: ""
        // SDDM's stock face means "no picture": draw the initial instead
        readonly property bool hasFace: face !== "" && face.indexOf("/sddm/faces/") < 0
        implicitWidth: size
        implicitHeight: size
        Rectangle {
            anchors.fill: parent
            radius: width / 2
            gradient: Gradient {
                GradientStop { position: 0; color: "#ffb37a" }
                GradientStop { position: 1; color: "#f2668b" }
            }
            border.color: Qt.rgba(1, 1, 1, 0.35)
            border.width: 2
            Text {
                anchors.centerIn: parent
                visible: img.status !== Image.Ready
                text: av.name.charAt(0).toUpperCase()
                color: "white"
                font.family: root.uiFont
                font.pixelSize: av.size * 0.44
                font.weight: Font.Bold
            }
        }
        Image {
            id: img
            anchors.fill: parent
            anchors.margins: 2
            source: av.hasFace ? "file://" + av.face : ""
            sourceSize: Qt.size(av.size * 2, av.size * 2)
            fillMode: Image.PreserveAspectCrop
            visible: false
        }
        Rectangle {
            id: mask
            anchors.fill: img
            radius: width / 2
            visible: false
            layer.enabled: true
        }
        MultiEffect {
            anchors.fill: img
            source: img
            visible: img.status === Image.Ready
            maskEnabled: true
            maskSource: mask
        }
    }

    component PowerButton: T.Button {
        id: pb
        property string glyph
        implicitWidth: 92 * root.s
        implicitHeight: 86 * root.s
        focusPolicy: Qt.TabFocus
        background: Item {}
        contentItem: Column {
            spacing: 8
            Rectangle {
                anchors.horizontalCenter: parent.horizontalCenter
                width: 52 * root.s; height: width; radius: width / 2
                color: Qt.rgba(1, 1, 1, pb.pressed ? 0.30 : pb.hovered || pb.activeFocus ? 0.22 : 0.13)
                border.width: 1
                border.color: Qt.rgba(1, 1, 1, 0.20)
                Image { // Lucent line glyphs (design/lucent_extra_icons.py), light variant
                    anchors.centerIn: parent
                    width: 22 * root.s; height: width
                    sourceSize: Qt.size(width, height)
                    source: "file:///usr/share/icons/Lucent-Dark/scalable/actions/" + pb.glyph + ".svg"
                }
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: pb.text
                color: "white"
                font.family: root.uiFont
                font.pixelSize: 14 * root.s
                font.weight: Font.Medium
            }
        }
    }
}
