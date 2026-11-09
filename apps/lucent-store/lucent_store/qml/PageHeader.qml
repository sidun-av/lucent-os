// Top of the pane: back button (on sub-pages), title, and the search field.
import QtQuick
import QtQuick.Controls

Item {
    id: h
    readonly property var tk: store.t
    readonly property bool sub: win.page.indexOf("app:") === 0
    implicitHeight: store.t.paneTop + store.t.searchHeight

    LButton {
        id: backBtn
        visible: h.sub
        kind: "ghost"
        small: true
        icon: "left"
        text: l10n.text("Back")
        x: store.t.paneX - 12
        y: store.t.paneTop + 4
        onClicked: win.back()
    }
    Text {
        id: title
        visible: !h.sub
        x: store.t.paneX
        y: store.t.paneTop
        height: store.t.searchHeight
        verticalAlignment: Text.AlignVCenter
        font.pointSize: store.t.fontH1
        font.weight: Font.Bold
        font.letterSpacing: -0.3
        color: h.tk.text
        text: {
            const p = win.page
            if (p === "home" || p === "nextgen") return l10n.text("Store")
            if (p.indexOf("category:") === 0) return store.category(p.substring(9), 0).name || ""
            if (p === "installed") return l10n.ctext("sidebar", "Installed")
            if (p === "updates") return l10n.text("Updates")
            if (p === "search") return l10n.text("Search")
            if (p === "windows") return l10n.text("Windows programs")
            return ""
        }
    }
    Rectangle {
        id: field
        anchors.right: parent.right
        anchors.rightMargin: store.t.paneX
        y: store.t.paneTop
        width: Math.min(store.t.searchWidth, h.width * 0.42)
        height: store.t.searchHeight
        radius: store.t.radiusField
        color: input.activeFocus ? h.tk.raised : h.tk.well
        border.width: input.activeFocus ? 2 : 1
        border.color: input.activeFocus ? h.tk.accent : h.tk.wellRing
        Rectangle {          // focus halo (0 0 0 6px accent-soft)
            visible: input.activeFocus
            anchors.fill: parent; anchors.margins: -5
            radius: parent.radius + 5
            color: "transparent"
            border.width: 4
            border.color: h.tk.accentSoft
        }
        Sym { id: lens; name: "search"; size: 18; tint: h.tk.text3; x: 13; anchors.verticalCenter: parent.verticalCenter }
        TextField {
            id: input
            objectName: "searchField"
            anchors.left: lens.right
            anchors.leftMargin: 4
            anchors.right: clear.left
            anchors.verticalCenter: parent.verticalCenter
            placeholderText: l10n.text("Search apps")
            placeholderTextColor: h.tk.text3
            color: h.tk.text
            font.pointSize: store.t.fontText
            background: null
            selectByMouse: true
            text: win.query
            onTextEdited: {
                win.query = text
                if (text.trim().length > 0 && win.page !== "search") win.go("search")
                if (text.trim().length === 0 && win.page === "search") win.back()
            }
            Keys.onEscapePressed: { text = ""; win.query = ""; if (win.page === "search") win.back() }
        }
        Sym {
            id: clear
            name: "x"; size: 16; tint: h.tk.text3
            anchors.right: parent.right; anchors.rightMargin: 12
            anchors.verticalCenter: parent.verticalCenter
            visible: input.text.length > 0
            MouseArea { anchors.fill: parent; anchors.margins: -6; cursorShape: Qt.PointingHandCursor
                        onClicked: { input.text = ""; win.query = ""; if (win.page === "search") win.back() } }
        }
    }
    Shortcut { sequences: [StandardKey.Find, "Ctrl+F"]; onActivated: input.forceActiveFocus() }
}
