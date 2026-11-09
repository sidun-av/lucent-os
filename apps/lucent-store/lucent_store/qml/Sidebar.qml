// Left column: catalogue categories and "My apps", a floating glass card
// (glass.css .side, tier 1: no wallpaper blur) with an accent-pill selection.
import QtQuick

Well {
    id: side
    tint: tk.glassSidebar

    Column {
        anchors.fill: parent
        anchors.topMargin: 12
        anchors.leftMargin: 10
        anchors.rightMargin: 10
        spacing: 1

        SideHeading { text: l10n.text("Catalog"); first: true }
        SideItem { icon: "star"; text: l10n.text("Home"); target: "home"
                   selected: win.page === "home" || win.page === "nextgen" }
        Repeater {
            model: store.categories()
            SideItem {
                required property var modelData
                icon: modelData.icon
                text: modelData.name
                target: "category:" + modelData.id
            }
        }
        SideHeading { text: l10n.text("My apps") }
        SideItem { icon: "check"; text: l10n.ctext("sidebar", "Installed"); target: "installed" }
        SideItem { icon: "refresh"; text: l10n.text("Updates"); target: "updates"; count: store.updateCount }
    }
}
