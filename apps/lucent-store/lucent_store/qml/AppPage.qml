// One app: what it is, screenshots, size, license, permissions; install/open/remove.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Shapes

ScrollPage {
    id: page
    property string appId
    readonly property var d: store.details(appId, win.rev)
    readonly property var tk: store.t
    readonly property bool busy: d.state === "installing" || d.state === "removing" || d.state === "updating" || d.state === "queued"

    Item { width: 1; height: 14 }
    RowLayout {
        width: parent.width
        spacing: 24
        AppIcon { appId: page.d.nextgen ? "" : page.appId; src: page.d.icon; size: store.t.iconPage; Layout.alignment: Qt.AlignTop }
        Column {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignVCenter
            spacing: 6
            Row {
                spacing: 12
                Text { text: page.d.name; font.pointSize: store.t.fontH1; font.weight: Font.Bold; font.letterSpacing: -0.3
                       color: page.tk.text }
                AlphaBadge { visible: page.d.nextgen; anchors.verticalCenter: parent.verticalCenter }
            }
            Row {
                spacing: 10
                visible: page.d.developer !== "" || page.d.verified
                Text { text: page.d.developer; font.pointSize: store.t.fontText; color: page.tk.text2
                       anchors.verticalCenter: parent.verticalCenter; visible: text !== "" }
                Rectangle {
                    visible: page.d.verified
                    anchors.verticalCenter: parent.verticalCenter
                    height: 26; radius: store.t.radiusChip; width: vr.implicitWidth + 20
                    color: page.tk.accentSoft
                    Row { id: vr; anchors.centerIn: parent; spacing: 6
                        Sym { name: "shield"; size: 15; tint: page.tk.accent; anchors.verticalCenter: parent.verticalCenter }
                        Text { text: l10n.text("Verified publisher"); font.pointSize: store.t.fontMeta; font.weight: Font.DemiBold
                               color: page.tk.accent; anchors.verticalCenter: parent.verticalCenter }
                    }
                }
            }
            Text { width: parent.width; text: page.d.summary; font.pointSize: store.t.fontName; color: page.tk.text2
                   wrapMode: Text.WordWrap; visible: text !== "" }
        }
        Row {
            Layout.alignment: Qt.AlignVCenter
            spacing: 10
            LButton {
                visible: page.d.state === "installed" && !page.d.system && !page.busy
                text: l10n.text("Remove")
                onClicked: confirmRemove.ask(page.appId, page.d.name)
            }
            LButton {
                visible: page.d.hasUpdate && page.d.state === "installed"
                text: l10n.text("Update")
                onClicked: store.update(page.appId)
            }
            LButton {
                visible: page.d.state === "installed" || page.d.state === "system"
                kind: "primary"
                text: l10n.text("Open")
                onClicked: store.launch(page.appId)
            }
            ActionButton {
                visible: page.d.state === "available" || page.busy
                small: false
                state_: page.d.state
                progress: page.d.progress
                installText: page.d.nextgen ? l10n.text("Try") : l10n.text("Install")
                onInstall: store.install([page.appId], page.d.name)
            }
        }
    }

    // facts
    Flow {
        width: parent.width
        topPadding: 22
        spacing: 10
        Repeater {
            model: [
                page.d.version ? l10n.text("Version {v}").replace("{v}", page.d.version) : "",
                page.d.state === "installed" && page.d.installedSize ? l10n.text("Uses {size}").replace("{size}", page.d.installedSize)
                    : page.d.download ? l10n.text("Download {size}").replace("{size}", page.d.download) : "",
                page.d.license ? page.d.license + (page.d.licenseCode && page.d.license !== page.d.licenseCode ? " (" + page.d.licenseCode + ")" : "") : "",
                page.d.nextgen ? l10n.text("Only for your account") : page.d.system ? l10n.text("Part of Lucent") : l10n.text("From Flathub"),
            ].filter(function (x) { return x })
            Rectangle {
                required property var modelData
                height: 30; radius: store.t.radiusChip; width: ft.implicitWidth + 22
                color: page.tk.wellStrong
                Text { id: ft; anchors.centerIn: parent; text: modelData; font.pointSize: store.t.fontCaption; color: page.tk.text2 }
            }
        }
    }

    // beta warning
    Item { width: 1; height: page.d.nextgen ? 18 : 0 }
    Rectangle {
        visible: page.d.nextgen
        width: parent.width
        height: visible ? warnText.implicitHeight + 26 : 0
        radius: store.t.radiusField
        color: page.tk.warnSoft
        y: 0
        Sym { id: wi; name: "info"; size: 20; tint: page.tk.warn; x: 16; anchors.verticalCenter: parent.verticalCenter }
        Text { id: warnText; anchors.left: wi.right; anchors.leftMargin: 12; anchors.right: parent.right; anchors.rightMargin: 16
               anchors.verticalCenter: parent.verticalCenter; wrapMode: Text.WordWrap; font.pointSize: store.t.fontText; color: page.tk.text
               text: l10n.text("These are alpha versions: they work, but expect bugs and possible loss of unsaved work. Keep copies of important files.") }
    }

    // screenshots
    Item { width: 1; height: 26; visible: shots.count > 0 }
    ListView {
        id: shots
        visible: count > 0
        width: parent.width
        height: visible ? 380 : 0
        orientation: ListView.Horizontal
        spacing: 16
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        model: page.d.screenshots
        ScrollBar.horizontal: ScrollBar { policy: ScrollBar.AsNeeded }
        delegate: Rectangle {
            required property var modelData
            height: 360
            width: img.status === Image.Ready ? Math.min(height * img.sourceSize.width / Math.max(1, img.sourceSize.height), 900) : 600
            radius: store.t.radiusShot
            color: page.tk.well
            clip: true
            Image {
                id: img
                anchors.fill: parent
                source: modelData.source
                fillMode: Image.PreserveAspectFit
                asynchronous: true
                smooth: true
                mipmap: true
            }
            Shape {                // round the picture's corners (works with every renderer)
                anchors.fill: parent
                ShapePath {
                    fillRule: ShapePath.OddEvenFill
                    fillColor: page.tk.winBg
                    strokeColor: page.tk.line
                    strokeWidth: 1
                    PathRectangle { x: -1; y: -1; width: img.width + 2; height: img.height + 2 }
                    PathRectangle { x: 0.5; y: 0.5; width: img.width - 1; height: img.height - 1
                                    radius: store.t.radiusShot }
                }
            }
            Text {
                anchors.centerIn: parent
                visible: img.status !== Image.Ready
                text: l10n.text("Loading screenshot…")
                font.pointSize: store.t.fontCaption
                color: page.tk.text3
            }
        }
    }

    // description + facts side by side
    Item { width: 1; height: 28 }
    RowLayout {
        width: parent.width
        spacing: 40
        Text {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop
            textFormat: Text.RichText
            wrapMode: Text.WordWrap
            font.pointSize: store.t.fontBody
            lineHeight: 1.15
            color: page.tk.text
            text: page.d.description || ("<p>" + (page.d.summary || "") + "</p>")
        }
        Raised {
            visible: !page.d.system
            Layout.preferredWidth: 420
            Layout.alignment: Qt.AlignTop
            implicitHeight: permCol.implicitHeight + 36
            radius: store.t.radiusCard
            Column {
                id: permCol
                x: 20; y: 18
                width: parent.width - 40
                spacing: 12
                Text { text: l10n.text("What it can access"); font.pointSize: store.t.fontLead; font.weight: Font.DemiBold; color: page.tk.text }
                Text {
                    width: parent.width
                    visible: page.d.nextgen
                    wrapMode: Text.WordWrap; font.pointSize: store.t.fontSmall; color: page.tk.text2
                    text: l10n.text("ArtCraft apps are installed for your account only and checked by Lucent before they are offered. Each one checks GitHub for a newer version when it starts.")
                }
                Text {
                    width: parent.width
                    visible: !page.d.nextgen && page.d.permissions.length === 0
                    font.pointSize: store.t.fontSmall; color: page.tk.text3
                    text: l10n.text("Checking…")
                }
                Repeater {
                    model: page.d.permissions
                    Row {
                        required property var modelData
                        width: permCol.width
                        spacing: 12
                        Sym { name: modelData.icon; size: 18; y: 1
                              tint: modelData.level === "high" ? page.tk.danger : modelData.level === "notice" ? page.tk.warn : page.tk.text3 }
                        Text { width: parent.width - 30; text: modelData.text; wrapMode: Text.WordWrap; font.pointSize: store.t.fontSmall
                               color: modelData.level === "high" ? page.tk.danger : page.tk.text }
                    }
                }
                Text {
                    width: parent.width
                    visible: page.d.isolationText !== ""
                    topPadding: 4
                    wrapMode: Text.WordWrap; font.pointSize: store.t.fontMeta; color: page.tk.text2
                    text: page.d.isolationText
                }
            }
        }
    }
    Text {
        visible: page.d.homepage !== ""
        topPadding: 22
        font.pointSize: store.t.fontSmall
        color: page.tk.accent
        text: l10n.text("Website") + ": " + page.d.homepage
        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: Qt.openUrlExternally(page.d.homepage) }
    }
}
