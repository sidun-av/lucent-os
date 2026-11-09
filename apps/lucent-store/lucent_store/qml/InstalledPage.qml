import QtQuick

ScrollPage {
    id: page
    readonly property var apps: store.installed(win.rev)
    Text {
        x: 2
        width: parent.width
        topPadding: 10
        bottomPadding: 22
        font.pointSize: store.t.fontLead
        color: store.t.text2
        wrapMode: Text.WordWrap
        text: l10n.plural("{n} app installed", "{n} apps installed", page.apps.length)
    }
    AppGrid {
        width: parent.width
        apps: page.apps
        showRemove: true
        metaFor: function (a) {
            return [a.size, a.user ? l10n.text("Only for you") : ""].filter(function (x) { return x }).join("  ·  ")
        }
    }
}
