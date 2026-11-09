import QtQuick

ScrollPage {
    id: page
    property string categoryId
    readonly property var cat: store.category(categoryId, win.rev)
    Text {
        width: parent.width
        topPadding: 10
        bottomPadding: 24
        x: 2
        text: page.cat.description || ""
        wrapMode: Text.WordWrap
        font.pointSize: store.t.fontLead
        color: store.t.text2
    }
    AppGrid { width: parent.width; apps: page.cat.apps || [] }
    Text {
        width: parent.width
        topPadding: 28
        wrapMode: Text.WordWrap
        font.pointSize: store.t.fontCaption
        color: store.t.text3
        text: l10n.text("Looking for something else? Search finds every app on Flathub.")
    }
}
