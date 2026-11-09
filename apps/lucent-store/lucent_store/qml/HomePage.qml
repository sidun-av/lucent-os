// Home: "Instead of Windows programs", the Windows-installer hint, and the beta.
import QtQuick
import QtQuick.Layouts

ScrollPage {
    id: page
    property bool scrollToBeta: false
    readonly property int columns: innerWidth >= 1150 ? 3 : 2
    readonly property var cards: store.home(win.rev)
    property bool showAll: false

    SectionTitle {
        title: l10n.text("Instead of Windows programs")
        action: page.cards.length > store.t.homeCards
                ? (page.showAll ? l10n.text("Show fewer")
                                : l10n.plural("Show {n} more", "Show {n} more", page.cards.length - store.t.homeCards))
                : ""
        actionIcon: page.showAll ? "up" : "down"
        onActionClicked: page.showAll = !page.showAll
        subtitle: l10n.text("Used to a program from Windows? Here's what does the same job here, free and without a subscription.")
    }
    GridLayout {
        width: parent.width
        columns: page.columns
        columnSpacing: store.t.gridGap
        rowSpacing: store.t.gridGap
        Repeater {
            model: page.showAll ? page.cards : page.cards.slice(0, store.t.homeCards)
            ReplacementCard {
                required property var modelData
                card: modelData
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredWidth: 100
            }
        }
    }
    Item { width: 1; height: store.t.gridGap }
    BridgeHint { width: parent.width }

    SectionTitle {
        id: betaTitle
        topGap: 44
        title: l10n.text("Next generation · beta")
        pill: l10n.text("early access")
        pillIcon: "flask"
        subtitle: l10n.text("The ArtCraft family: open-source apps written in Rust by an independent team, fast and with one shared look.")
    }
    BetaPanel { id: beta; width: parent.width; columns: page.columns }
    Text {
        width: parent.width
        topPadding: 12
        wrapMode: Text.WordWrap
        font.pointSize: store.t.fontCaption
        color: store.t.text3
        text: l10n.text("Installed for your account only. Lucent offers the versions it has checked: no AI features and no tracking.")
    }

    Timer {
        interval: 50
        running: page.scrollToBeta
        onTriggered: page.contentY = Math.max(0, Math.min(betaTitle.y + 20, page.contentHeight - page.height))
    }
}
