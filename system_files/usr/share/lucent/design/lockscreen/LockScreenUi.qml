/*
    Lucent lock screen. Replaces LockScreenUi.qml of Plasma's desktop shell
    package (installed by build_files/design.sh); the authentication flow is
    Plasma's own (kscreenlocker's `authenticator`), the look is Lucent's:

      idle      the Lucent wallpaper, dimmed, with a large clock
      unlocking blurred + darker wallpaper, initials avatar, the name, one
                340 px rounded translucent field with the unlock arrow inside,
                caps-lock / error line, and a row of round session actions
    The same dark treatment in light and dark mode, so white text always has
    contrast. No on-screen-keyboard button (Lucent ships none).

    Based on Plasma's LockScreenUi.qml (SPDX-FileCopyrightText: 2014 Aleix Pol
    Gonzalez, 2026 Kristen McWilliam).
    SPDX-License-Identifier: GPL-2.0-or-later
*/

pragma ComponentBehavior: Bound

import QtQml
import QtQuick
import QtQuick.Effects
import QtQuick.Layouts
import QtQuick.Templates as T

import org.kde.plasma.private.accessibility
import org.kde.plasma.workspace.components as PW
import org.kde.plasma.private.keyboardindicator as KeyboardIndicator
import org.kde.kirigami as Kirigami
import org.kde.kscreenlocker as ScreenLocker
import org.kde.ki18n

import org.kde.plasma.private.sessions

Item {
    id: lockScreenUi

    readonly property bool softwareRendering: GraphicsInfo.api === GraphicsInfo.Software
    property bool expectingPrompt: false
    property bool showPrompt: false
    property bool noPasswordUnlock: false
    property string pendingPassword

    // Lucent tokens (docs/mockups/lucent.css), on a dark scrim in both modes
    readonly property color accent: "#5b8bff"
    readonly property string uiFont: "Inter"

    function handleMessage(msg) {
        if (!msg) {
            return;
        }
        if (!root.notification) {
            root.notification += msg;
        } else if (root.notification.includes(msg)) {
            root.notificationRepeated();
        } else {
            root.notification += "\n" + msg;
        }
        lockScreenRoot.uiVisible = true;
    }

    function startLogin() {
        const password = passwordBox.text;
        unlockButton.forceActiveFocus();
        if (authenticator.pamTimeout) {
            lockScreenUi.pendingPassword = password;
            prompt.enabled = false;
        } else {
            authenticator.respond(password);
        }
    }

    Kirigami.Theme.inherit: false
    Kirigami.Theme.colorSet: Kirigami.Theme.Complementary

    Connections {
        target: authenticator
        function onFailed(kind) {
            if (kind != 0) { // non-interactive authenticators report themselves
                return;
            }
            lockScreenUi.handleMessage(i18ndc("plasma_shell_org.kde.plasma.desktop", "@info:status", "Unlocking failed"));
            root.clearPassword();
            authenticator.startAuthenticating();
            notificationRemoveTimer.restart();
            shake.start();
        }
        function onSucceeded() {
            authenticator.stopAuthenticating();
            if (!lockScreenUi.expectingPrompt || authenticator.hadPrompt) {
                Qt.quit();
            } else {
                lockScreenUi.noPasswordUnlock = true;
                unlockButton.forceActiveFocus();
            }
        }
        function onInfoMessageChanged() { lockScreenUi.handleMessage(authenticator.infoMessage); }
        function onErrorMessageChanged() { lockScreenUi.handleMessage(authenticator.errorMessage); }
        function onPromptChanged() { lockScreenUi.handleMessage(authenticator.prompt); }
        function onPromptForSecretChanged() {
            passwordBox.forceActiveFocus();
            if (lockScreenUi.showPrompt) {
                lockScreenUi.handleMessage(authenticator.promptForSecret);
            }
        }
        function onPamTimeoutChanged() {
            if (!authenticator.pamTimeout && lockScreenUi.pendingPassword.length > 0) {
                authenticator.respond(lockScreenUi.pendingPassword);
                lockScreenUi.pendingPassword = "";
                prompt.enabled = true;
            }
        }
    }

    SessionManagement { id: sessionManagement }
    AccessibilityStatus { id: accessibilityStatus }
    KeyboardIndicator.KeyState { id: capsLockState; key: Qt.Key_CapsLock }
    Connections {
        target: sessionManagement
        function onAboutToSuspend() { root.clearPassword(); }
    }
    Connections {
        target: root
        function onClearPassword() {
            passwordBox.text = "";
            passwordBox.text = Qt.binding(() => PasswordSync.password);
            passwordBox.forceActiveFocus();
        }
        function onNotificationRepeated() { shake.start(); }
    }

    // Authenticators (password, fingerprint, smartcard): selecting one sets
    // what the prompt shows. Buttons only when there is more than one.
    Repeater {
        id: authenticatorRepeater
        model: ScreenLocker.AuthenticatorModel
        delegate: Item {
            required property int type
            required property bool passwordField
            required property bool expectingPrompt
            required property bool showPrompt
            function select() {
                authenticator.authenticator = type;
                root.notification = "";
                prompt.passwordVisible = passwordField;
                lockScreenUi.expectingPrompt = expectingPrompt;
                lockScreenUi.showPrompt = showPrompt;
            }
            Component.onCompleted: if (authenticator.authenticator === type) select()
        }
    }

    MouseArea {
        id: lockScreenRoot

        property bool uiVisible: false
        property bool seenPositionChange: false
        property bool blockUI: containsMouse && (passwordBox.text.length > 0 || lockScreenUi.noPasswordUnlock)

        anchors.fill: parent
        hoverEnabled: true
        cursorShape: uiVisible ? Qt.ArrowCursor : Qt.BlankCursor
        drag.filterChildren: true
        onPressed: uiVisible = true
        onPositionChanged: {
            uiVisible = seenPositionChange;
            seenPositionChange = true;
        }
        onUiVisibleChanged: {
            if (uiVisible) {
                Window.window.requestActivate();
                passwordBox.forceActiveFocus();
            }
            if (blockUI) {
                fadeoutTimer.running = false;
            } else if (uiVisible) {
                fadeoutTimer.restart();
            }
            authenticator.startAuthenticating();
        }
        onBlockUIChanged: {
            if (blockUI) {
                fadeoutTimer.running = false;
                uiVisible = true;
            } else {
                fadeoutTimer.restart();
            }
        }
        Keys.onEscapePressed: {
            // Escape turns the screen off in kscreenlocker; hide the prompt.
            if (uiVisible) {
                uiVisible = false;
                root.clearPassword();
            }
        }
        Keys.onPressed: event => {
            uiVisible = true;
            event.accepted = false;
        }

        Timer { // heart beat keeping the backend active while visible
            interval: 1000
            running: !authenticator.unlocked && lockScreenRoot.uiVisible
            repeat: true
            onTriggered: authenticator.startAuthenticating()
        }
        Timer {
            id: fadeoutTimer
            interval: 10000
            onTriggered: if (!lockScreenRoot.blockUI) lockScreenRoot.uiVisible = false
        }
        Timer {
            id: notificationRemoveTimer
            interval: 3000
            onTriggered: root.notification = ""
        }
        ScreenLocker.ActiveScreenMonitor {
            lockscreenState: ScreenLocker.LockscreenState
            window: lockScreenRoot.Window.window
            onActiveChanged: if (!active) lockScreenRoot.uiVisible = false
        }

        opacity: 0
        Component.onCompleted: opacity = 1
        Behavior on opacity { NumberAnimation { duration: 400; easing.type: Easing.OutCubic } }

        // ---------------------------------------------------- background --
        MultiEffect {
            id: blurredWallpaper
            anchors.fill: parent
            source: wallpaper
            visible: !lockScreenUi.softwareRendering
            blurEnabled: true
            blurMax: 64
            blur: lockScreenRoot.uiVisible ? 1.0 : 0.0
            autoPaddingEnabled: false
            Behavior on blur { NumberAnimation { duration: 300; easing.type: Easing.InOutQuad } }
        }
        Rectangle { // dark scrim: white text keeps 4.5:1 on any wallpaper
            anchors.fill: parent
            color: "#0b0f1a"
            opacity: lockScreenRoot.uiVisible ? 0.55 : 0.38
            Behavior on opacity { NumberAnimation { duration: 300; easing.type: Easing.InOutQuad } }
        }

        // --------------------------------------------------------- clock --
        Column {
            id: clock
            anchors.horizontalCenter: parent.horizontalCenter
            y: lockScreenRoot.uiVisible ? parent.height * 0.13 : parent.height * 0.30
            spacing: 4
            visible: config.alwaysShowClock || lockScreenRoot.uiVisible
            scale: lockScreenRoot.uiVisible ? 0.72 : 1.0
            transformOrigin: Item.Top
            Behavior on y { NumberAnimation { duration: 300; easing.type: Easing.OutCubic } }
            Behavior on scale { NumberAnimation { duration: 300; easing.type: Easing.OutCubic } }

            property date now: new Date()
            Timer {
                interval: 1000; running: true; repeat: true
                onTriggered: clock.now = new Date()
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: Qt.formatTime(clock.now, Qt.locale().timeFormat(Locale.ShortFormat).replace(/:ss|\.ss/, ""))
                color: "white"
                font.family: lockScreenUi.uiFont
                font.pixelSize: 112
                font.weight: Font.DemiBold
                font.letterSpacing: -2
                font.features: { "tnum": 1 }
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: clock.now.toLocaleDateString(Qt.locale(), "dddd, d MMMM")
                color: Qt.rgba(1, 1, 1, 0.86)
                font.family: lockScreenUi.uiFont
                font.pixelSize: 24
                font.weight: Font.Medium
            }
        }

        // -------------------------------------------------------- prompt --
        ColumnLayout {
            id: prompt
            property bool passwordVisible: true
            anchors.horizontalCenter: parent.horizontalCenter
            y: parent.height * 0.42
            width: 340
            spacing: 0
            opacity: lockScreenRoot.uiVisible ? 1 : 0
            visible: opacity > 0
            Behavior on opacity { NumberAnimation { duration: 250 } }
            transform: Translate { id: shakeX }

            SequentialAnimation {
                id: shake
                loops: 2
                NumberAnimation { target: shakeX; property: "x"; to: -10; duration: 50 }
                NumberAnimation { target: shakeX; property: "x"; to: 10; duration: 80 }
                NumberAnimation { target: shakeX; property: "x"; to: 0; duration: 50 }
            }

            Item { // avatar: account picture or the initial on Lucent's gradient
                Layout.alignment: Qt.AlignHCenter
                implicitWidth: 104
                implicitHeight: 104
                Rectangle {
                    anchors.fill: parent
                    radius: width / 2
                    gradient: Gradient {
                        orientation: Gradient.Vertical
                        GradientStop { position: 0; color: "#ffb37a" }
                        GradientStop { position: 1; color: "#f2668b" }
                    }
                    border.color: Qt.rgba(1, 1, 1, 0.35)
                    border.width: 2
                    Text {
                        anchors.centerIn: parent
                        visible: face.status !== Image.Ready
                        text: kscreenlocker_userName.charAt(0).toUpperCase()
                        color: "white"
                        font.family: lockScreenUi.uiFont
                        font.pixelSize: 46
                        font.weight: Font.Bold
                    }
                }
                Image {
                    id: face
                    anchors.fill: parent
                    anchors.margins: 2
                    source: kscreenlocker_userImage !== "" ? "file://" + kscreenlocker_userImage.split("/").map(encodeURIComponent).join("/") : ""
                    sourceSize: Qt.size(208, 208)
                    fillMode: Image.PreserveAspectCrop
                    visible: false
                }
                MultiEffect {
                    anchors.fill: face
                    source: face
                    visible: face.status === Image.Ready
                    maskEnabled: true
                    maskSource: faceMask
                }
                Rectangle {
                    id: faceMask
                    anchors.fill: face
                    radius: width / 2
                    visible: false
                    layer.enabled: true
                }
            }

            Text {
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 14
                text: kscreenlocker_userName
                color: "white"
                font.family: lockScreenUi.uiFont
                font.pixelSize: 22
                font.weight: Font.DemiBold
            }

            // The pill: field + unlock arrow inside it
            Rectangle {
                id: pill
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 22
                Layout.preferredWidth: 340
                Layout.preferredHeight: 50
                radius: 25
                visible: prompt.passwordVisible && !lockScreenUi.noPasswordUnlock
                color: Qt.rgba(1, 1, 1, passwordBox.activeFocus ? 0.20 : 0.14)
                border.width: 1
                border.color: passwordBox.activeFocus ? Qt.rgba(1, 1, 1, 0.55) : Qt.rgba(1, 1, 1, 0.25)
                Behavior on color { ColorAnimation { duration: 150 } }

                T.TextField {
                    id: passwordBox
                    anchors.left: parent.left
                    anchors.right: unlockButton.left
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.leftMargin: 22
                    anchors.rightMargin: 8
                    height: parent.height
                    verticalAlignment: TextInput.AlignVCenter
                    echoMode: TextInput.Password
                    passwordCharacter: "●"
                    passwordMaskDelay: 0
                    color: "white"
                    selectionColor: lockScreenUi.accent
                    selectedTextColor: "white"
                    font.family: lockScreenUi.uiFont
                    font.pixelSize: 17
                    font.letterSpacing: text.length > 0 ? 2 : 0
                    placeholderText: i18ndc("plasma_shell_org.kde.plasma.desktop", "@info:placeholder in text field", "Password")
                    placeholderTextColor: Qt.rgba(1, 1, 1, 0.62)
                    text: PasswordSync.password
                    focus: true
                    cursorVisible: visible && activeFocus
                    inputMethodHints: Qt.ImhHiddenText | Qt.ImhSensitiveData | Qt.ImhNoAutoUppercase | Qt.ImhNoPredictiveText
                    Accessible.name: i18ndc("plasma_shell_org.kde.plasma.desktop", "@info:placeholder in text field", "Password")
                    onAccepted: if (lockScreenRoot.uiVisible) lockScreenUi.startLogin()
                    Keys.onEscapePressed: event => { event.accepted = false; }
                }
                Text { // Templates draw no placeholder
                    anchors.left: passwordBox.left
                    anchors.verticalCenter: passwordBox.verticalCenter
                    visible: passwordBox.text.length === 0 && !passwordBox.preeditText
                    text: passwordBox.placeholderText
                    color: passwordBox.placeholderTextColor
                    font.family: lockScreenUi.uiFont
                    font.pixelSize: 17
                }
                Binding {
                    target: PasswordSync
                    property: "password"
                    value: passwordBox.text
                }

                T.Button {
                    id: unlockButton
                    anchors.right: parent.right
                    anchors.rightMargin: 6
                    anchors.verticalCenter: parent.verticalCenter
                    width: 38
                    height: 38
                    Accessible.name: i18ndc("plasma_shell_org.kde.plasma.desktop", "@action:button accessible only", "Unlock")
                    onClicked: lockScreenUi.startLogin()
                    Keys.onReturnPressed: clicked()
                    Keys.onEnterPressed: clicked()
                    background: Rectangle {
                        radius: width / 2
                        color: unlockButton.pressed ? Qt.darker(lockScreenUi.accent, 1.15)
                             : unlockButton.hovered || unlockButton.activeFocus ? Qt.lighter(lockScreenUi.accent, 1.08)
                             : passwordBox.text.length > 0 ? lockScreenUi.accent : Qt.rgba(1, 1, 1, 0.18)
                        Behavior on color { ColorAnimation { duration: 150 } }
                    }
                    contentItem: Item {
                        Canvas { // arrow →
                            anchors.centerIn: parent
                            width: 18; height: 18
                            onPaint: {
                                const c = getContext("2d");
                                c.reset();
                                c.strokeStyle = "white";
                                c.lineWidth = 2;
                                c.lineCap = "round";
                                c.lineJoin = "round";
                                c.beginPath();
                                if (LayoutMirroring.enabled) {
                                    c.moveTo(15, 9); c.lineTo(3, 9); c.moveTo(8, 4); c.lineTo(3, 9); c.lineTo(8, 14);
                                } else {
                                    c.moveTo(3, 9); c.lineTo(15, 9); c.moveTo(10, 4); c.lineTo(15, 9); c.lineTo(10, 14);
                                }
                                c.stroke();
                            }
                        }
                    }
                }
            }

            // No password needed (e.g. passwordless account): one button
            T.Button {
                id: noPasswordButton
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 22
                visible: lockScreenUi.noPasswordUnlock
                implicitWidth: 180
                implicitHeight: 46
                onClicked: Qt.quit()
                Keys.onReturnPressed: clicked()
                Keys.onEnterPressed: clicked()
                background: Rectangle { radius: 23; color: lockScreenUi.accent }
                contentItem: Text {
                    text: i18ndc("plasma_shell_org.kde.plasma.desktop", "@action:button", "Unlock")
                    color: "white"
                    font.family: lockScreenUi.uiFont
                    font.pixelSize: 16
                    font.weight: Font.DemiBold
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }

            Text { // caps lock, slow keys, PAM messages
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 14
                Layout.preferredWidth: 340
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                color: Qt.rgba(1, 1, 1, 0.9)
                font.family: lockScreenUi.uiFont
                font.pixelSize: 15
                text: {
                    const parts = [];
                    if (capsLockState.locked) {
                        parts.push(i18ndc("plasma_shell_org.kde.plasma.desktop", "@info:status", "Caps Lock is on"));
                    }
                    if (accessibilityStatus.slowKeysEnabled) {
                        parts.push(i18ndc("plasma_shell_org.kde.plasma.desktop", "@info:status", "Slow Keys are enabled"));
                    }
                    if (root.notification) {
                        parts.push(root.notification);
                    }
                    return parts.join(" • ");
                }
                opacity: text.length > 0 ? 1 : 0
            }

            // Alternative authenticators (fingerprint, smartcard), if several
            Row {
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 10
                spacing: 8
                visible: authenticatorModelRepeater.count > 1
                Repeater {
                    id: authenticatorModelRepeater
                    model: ScreenLocker.AuthenticatorModel
                    delegate: T.Button {
                        id: authButton
                        required property int type
                        required property string iconName
                        required property string tooltip
                        required property bool passwordField
                        required property bool expectingPrompt
                        required property bool showPrompt
                        required property bool functional
                        enabled: functional
                        implicitWidth: 40
                        implicitHeight: 40
                        checked: authenticator.authenticator === type
                        Accessible.name: tooltip
                        onClicked: {
                            authenticator.authenticator = type;
                            root.notification = "";
                            prompt.passwordVisible = passwordField;
                            lockScreenUi.expectingPrompt = expectingPrompt;
                            lockScreenUi.showPrompt = showPrompt;
                        }
                        background: Rectangle {
                            radius: 20
                            color: authButton.checked ? Qt.rgba(1, 1, 1, 0.28) : Qt.rgba(1, 1, 1, authButton.hovered ? 0.18 : 0.10)
                        }
                        contentItem: Kirigami.Icon {
                            source: authButton.iconName
                            color: "white"
                            isMask: true
                            implicitWidth: 20
                            implicitHeight: 20
                        }
                    }
                }
            }
        }

        // ---------------------------------------------- session actions --
        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: Math.round(parent.height * 0.07)
            spacing: 28
            opacity: lockScreenRoot.uiVisible ? 1 : 0
            visible: opacity > 0
            Behavior on opacity { NumberAnimation { duration: 250 } }

            component ActionButton: T.Button {
                id: action
                property string iconName
                implicitWidth: 92
                implicitHeight: 86
                focusPolicy: Qt.TabFocus
                background: Item {}
                contentItem: Column {
                    spacing: 8
                    Rectangle {
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: 52; height: 52; radius: 26
                        color: Qt.rgba(1, 1, 1, action.pressed ? 0.30 : action.hovered || action.activeFocus ? 0.22 : 0.13)
                        border.width: 1
                        border.color: Qt.rgba(1, 1, 1, 0.20)
                        Kirigami.Icon {
                            anchors.centerIn: parent
                            width: 22; height: 22
                            source: action.iconName
                            color: "white"
                            isMask: true
                        }
                    }
                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: action.text.replace("&", "")
                        color: "white"
                        font.family: lockScreenUi.uiFont
                        font.pixelSize: 14
                        font.weight: Font.Medium
                    }
                }
            }

            ActionButton {
                text: i18ndc("plasma_shell_org.kde.plasma.desktop", "@action:button", "Slee&p")
                iconName: "system-suspend"
                visible: sessionManagement.canSuspend
                onClicked: sessionManagement.suspend()
            }
            ActionButton {
                text: i18ndc("plasma_shell_org.kde.plasma.desktop", "@action:button", "&Hibernate")
                iconName: "system-suspend-hibernate"
                visible: sessionManagement.canHibernate
                onClicked: sessionManagement.hibernate()
            }
            ActionButton {
                text: i18ndc("plasma_shell_org.kde.plasma.desktop", "@action:button", "Switch &User")
                iconName: "system-switch-user"
                visible: sessionManagement.canSwitchUser
                onClicked: sessionManagement.switchUser()
            }
        }

        // keyboard layout (only with more than one) and battery, bottom corners
        PW.KeyboardLayoutSwitcher {
            id: keyboardLayoutSwitcher
            anchors.left: parent.left
            anchors.bottom: parent.bottom
            anchors.margins: 20
            width: layoutLabel.implicitWidth + 24
            height: 32
            visible: hasMultipleKeyboardLayouts && lockScreenRoot.uiVisible
            acceptedButtons: Qt.LeftButton
            onClicked: keyboardLayout.switchToNextLayout()
            Rectangle {
                anchors.fill: parent
                radius: 16
                color: Qt.rgba(1, 1, 1, 0.14)
                Text {
                    id: layoutLabel
                    anchors.centerIn: parent
                    text: keyboardLayoutSwitcher.layoutNames.shortName.toUpperCase()
                    color: "white"
                    font.family: lockScreenUi.uiFont
                    font.pixelSize: 14
                    font.weight: Font.Bold
                }
            }
        }

        Loader {
            z: 2
            active: root.viewVisible
            source: "LockOsd.qml"
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: Kirigami.Units.gridUnit
        }
    }
}
