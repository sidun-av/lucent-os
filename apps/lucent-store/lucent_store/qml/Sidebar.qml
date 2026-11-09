// Left column: catalogue categories and "My apps" (lucent.css .side, .si).
import QtQuick

Rectangle {
    id: side
    readonly property var tk: store.t
    color: tk.side
    Rectangle { anchors.right: parent.right; width: 1; height: parent.height; color: side.tk.line }

    Column {
        anchors.fill: parent
        anchors.topMargin: 14
        anchors.leftMargin: 12
        anchors.rightMargin: 13
        spacing: 2

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
