/*
    Lucent lock screen. Replaces LockScreenUi.qml of Plasma's desktop shell
    package (installed by build_files/design.sh); the authentication flow is
    Plasma's own (kscreenlocker's `authenticator`), the look is Lucent's:

      idle      the night Drift wallpaper, dimmed, with a large clock
      unlocking blurred + darker wallpaper, the avatar (a rounded square on the
                design's gradient), the name, one 360 px matte field (radius
                14) with the indigo unlock button inside, caps-lock / error
                line, and a row of rounded session actions
    Drift night (pebble-drift.css .dark) in light and dark mode, so the
    light text always has contrast; the same look as the login screen.
    No on-screen-keyboard button (Lucent ships none).

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
    // Drift night tokens (pebble-drift.css .dark)
    readonly property color accent: "#7088ff"                          // --accent
    readonly property color onAccent: "#0e1230"                        // --text-on-accent
    readonly property color text1: "#eef0fa"                           // --text-primary
    readonly property color text2: "#bcc1d6"                           // --text-secondary
    readonly property color surface: Qt.rgba(29 / 255, 31 / 255, 46 / 255, 0.72)   // --surface-window, see-through
    readonly property color line: Qt.rgba(220 / 255, 228 / 255, 1, 0.14)          // --line-strong
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
            color: "#0e1020"
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
                color: lockScreenUi.text1
                font.family: lockScreenUi.uiFont
                font.pixelSize: 112
                font.weight: Font.Bold
                font.letterSpacing: -2
                font.features: { "tnum": 1 }
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: clock.now.toLocaleDateString(Qt.locale(), "dddd, d MMMM")
                color: lockScreenUi.text2
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
            width: 360
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
                Rectangle {     // .avatar: radius 12 at 44 px, scaled
                    anchors.fill: parent
                    radius: 28
                    gradient: Gradient {
                        orientation: Gradient.Horizontal
                        GradientStop { position: 0; color: "#6a86ff" }
                        GradientStop { position: 0.6; color: "#9a62e0" }
                        GradientStop { position: 1; color: "#d0679c" }
                    }
                    border.color: Qt.rgba(220 / 255, 228 / 255, 1, 0.20)
                    border.width: 1
                    Text {
                        anchors.centerIn: parent
                        visible: face.status !== Image.Ready
                        text: kscreenlocker_userName.charAt(0).toUpperCase()
                        color: "white"
                        font.family: lockScreenUi.uiFont
                        font.pixelSize: 42
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
                    radius: 27
                    visible: false
                    layer.enabled: true
                }
            }

            Text {
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 14
                text: kscreenlocker_userName
                color: lockScreenUi.text1
                font.family: lockScreenUi.uiFont
                font.pixelSize: 22
                font.weight: Font.DemiBold
            }

            // The pill: field + unlock arrow inside it
            Rectangle {
                id: pill
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 22
                Layout.preferredWidth: 360
                Layout.preferredHeight: 52
                radius: 14                                           // --radius-card
                visible: prompt.passwordVisible && !lockScreenUi.noPasswordUnlock
                color: lockScreenUi.surface
                border.width: passwordBox.activeFocus ? 2 : 1        // --focus-ring / --line-strong
                border.color: passwordBox.activeFocus ? lockScreenUi.accent : lockScreenUi.line
                Rectangle {     // --focus-ring halo: 6 px --accent-soft
                    anchors.fill: parent
                    anchors.margins: -6
                    z: -1
                    radius: 20
                    color: Qt.rgba(112 / 255, 136 / 255, 1, 0.18)
                    visible: passwordBox.activeFocus
                }

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
                    color: lockScreenUi.text1
                    selectionColor: lockScreenUi.accent
                    selectedTextColor: lockScreenUi.onAccent
                    font.family: lockScreenUi.uiFont
                    font.pixelSize: 17
                    font.letterSpacing: text.length > 0 ? 2 : 0
                    placeholderText: i18ndc("plasma_shell_org.kde.plasma.desktop", "@info:placeholder in text field", "Password")
                    placeholderTextColor: lockScreenUi.text2
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
                        radius: 10                                       // --radius-control
                        color: unlockButton.pressed ? "#5f77f0"         // --accent-pressed
                             : unlockButton.hovered || unlockButton.activeFocus ? "#8297ff"   // --accent-hover
                             : passwordBox.text.length > 0 ? lockScreenUi.accent : Qt.rgba(220 / 255, 228 / 255, 1, 0.14)
                        Behavior on color { ColorAnimation { duration: 150 } }
                    }
                    contentItem: Item {
                        Canvas { // arrow →
                            anchors.centerIn: parent
                            width: 18; height: 18
                            onPaint: {
                                const c = getContext("2d");
                                c.reset();
                                c.strokeStyle = passwordBox.text.length > 0 || unlockButton.hovered ? lockScreenUi.onAccent : lockScreenUi.text1;
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
                background: Rectangle { radius: 11; color: lockScreenUi.accent }
                contentItem: Text {
                    text: i18ndc("plasma_shell_org.kde.plasma.desktop", "@action:button", "Unlock")
                    color: lockScreenUi.onAccent
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
                Layout.preferredWidth: 360
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                color: lockScreenUi.text1
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
                            radius: 10
                            color: authButton.checked ? Qt.rgba(51 / 255, 54 / 255, 77 / 255, 0.95)
                                 : authButton.hovered ? Qt.rgba(44 / 255, 47 / 255, 68 / 255, 0.92) : lockScreenUi.surface
                        }
                        contentItem: Kirigami.Icon {
                            source: authButton.iconName
                            color: lockScreenUi.text1
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
                        width: 52; height: 52; radius: 14              // rounded square, --radius-card
                        color: action.pressed ? Qt.rgba(51 / 255, 54 / 255, 77 / 255, 0.95)
                             : action.hovered || action.activeFocus ? Qt.rgba(44 / 255, 47 / 255, 68 / 255, 0.92) : lockScreenUi.surface
                        border.width: 1
                        border.color: lockScreenUi.line
                        Kirigami.Icon {
                            anchors.centerIn: parent
                            width: 22; height: 22
                            source: action.iconName
                            color: lockScreenUi.text1
                            isMask: true
                        }
                    }
                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: action.text.replace("&", "")
                        color: lockScreenUi.text1
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
                radius: 10
                color: lockScreenUi.surface
                border.width: 1
                border.color: lockScreenUi.line
                Text {
                    id: layoutLabel
                    anchors.centerIn: parent
                    text: keyboardLayoutSwitcher.layoutNames.shortName.toUpperCase()
                    color: lockScreenUi.text1
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
