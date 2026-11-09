import QtQuick

ScrollPage {
    id: page
    property string query
    readonly property var results: store.search(query, win.rev)
    Text {
        x: 2
        width: parent.width
        topPadding: 10
        bottomPadding: 22
        wrapMode: Text.WordWrap
        font.pointSize: store.t.fontLead
        color: store.t.text2
        text: page.query.trim().length < 2 ? l10n.text("Type the name of an app, or of the Windows program you are used to.")
            : page.results.length === 0 ? l10n.text("Nothing found. Try another word, or the name of the Windows program you are used to.")
            : l10n.plural("{n} app found", "{n} apps found", page.results.length)
    }
    Rectangle {
        visible: store.appstreamState !== "ready"
        width: parent.width
        height: msg.implicitHeight + 28
        radius: store.t.radiusField
        color: store.t.warnSoft
        Text {
            id: msg
            x: 16; width: parent.width - 32
            anchors.verticalCenter: parent.verticalCenter
            wrapMode: Text.WordWrap
            font.pointSize: store.t.fontSmall
            color: store.t.text
            text: store.appstreamState === "loading" ? l10n.text("Loading the list of apps…")
                : l10n.text("The full list of apps from Flathub isn't on this computer yet, so only Lucent's own picks are searched. It is downloaded with the next update check.")
        }
    }
    Item { width: 1; height: store.appstreamState !== "ready" ? 18 : 0 }
    AppGrid { width: parent.width; apps: page.results }
}
