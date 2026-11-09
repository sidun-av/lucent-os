// Lucent Store (docs/mockups/06-store.png): sidebar + one page at a time.
// Frameless (`frameless`, the shared org.lucent.chrome module): one top row,
// the app icon above the sidebar and the window buttons at the end of the
// page header; without the module KWin's title bar sits above.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: win
    width: startWidth
    height: startHeight
    minimumWidth: 960
    minimumHeight: 620
    visible: true
    title: l10n.text("Store")
    flags: frameless ? (Qt.Window | Qt.FramelessWindowHint) : Qt.Window
    color: frameless ? "transparent" : tk.winBg
    readonly property int headerBand: 64       // the one top row when frameless

    readonly property var tk: store.t
    readonly property int rev: store.revision
    // home | nextgen | category:<id> | installed | updates | windows | search | app:<id>
    property string page: "home"
    property var history: []
    property string query: ""

    function go(p) {
        if (p === page) return
        history = history.concat([page])
        page = p
    }
    function back() {
        if (history.length === 0) { page = "home"; return }
        page = history[history.length - 1]
        history = history.slice(0, -1)
    }
    function openApp(id) { go("app:" + id) }

    Component.onCompleted: {
        if (frameless)
            chrome.setSource("chrome/Frame.qml", { win: win, leftSlot: leftSlot, rightSlot: rightSlot,
                                                   overlay: overlay, headerHeight: headerBand })
        if (startPage.indexOf("search:") === 0) { query = startPage.substring(7); page = "search" }
        else page = startPage
    }

    Loader { id: chrome; anchors.fill: parent }   // frameless: surface, shadow, buttons

    Image {                  // fine grain over the matte surface (pebble .matte::before)
        visible: !frameless
        anchors.fill: parent
        source: "../icons/" + tk.grain
        fillMode: Image.Tile
        opacity: tk.grainOpacity
        smooth: false
    }
    RowLayout {
        anchors.fill: parent
        spacing: 0
        Sidebar {
            Layout.fillHeight: true
            Layout.preferredWidth: store.t.sidebarWidth
            Layout.leftMargin: store.t.sideInset
            Layout.topMargin: frameless ? win.headerBand : store.t.sideInset
            Layout.bottomMargin: store.t.sideInset
        }
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0
            PageHeader {
                id: header
                Layout.fillWidth: true
                Layout.preferredHeight: frameless ? win.headerBand : implicitHeight
                topPad: frameless ? (win.headerBand - store.t.searchHeight) / 2 : store.t.paneTop
                rightPad: frameless ? rightSlot.width + 12 + 20 : store.t.paneX
            }
            Loader {
                id: loader
                Layout.fillWidth: true
                Layout.fillHeight: true
                sourceComponent: {
                    if (win.page === "home" || win.page === "nextgen") return homePage
                    if (win.page.indexOf("category:") === 0)
                        return win.page === "category:windows" ? windowsPage : categoryPage
                    if (win.page === "windows") return windowsPage
                    if (win.page === "installed") return installedPage
                    if (win.page === "updates") return updatesPage
                    if (win.page === "search") return searchPage
                    if (win.page.indexOf("app:") === 0) return appPage
                    return homePage
                }
            }
        }
    }

    Component { id: homePage; HomePage { scrollToBeta: win.page === "nextgen" } }
    Component { id: categoryPage; CategoryPage { categoryId: win.page.substring(9) } }
    Component { id: windowsPage; WindowsPage {} }
    Component { id: installedPage; InstalledPage {} }
    Component { id: updatesPage; UpdatesPage {} }
    Component { id: searchPage; SearchPage { query: win.query } }
    Component { id: appPage; AppPage { appId: win.page.substring(4) } }

    Item {                   // frameless: window buttons kwinrc puts on the left (Lucent: the app icon)
        id: leftSlot
        visible: frameless
        x: store.t.sideInset + 2
        width: children.length ? children[0].implicitWidth : 0
        height: win.headerBand
    }
    Item {                   // frameless: minimise / maximise / close
        id: rightSlot
        visible: frameless
        anchors.right: parent.right
        anchors.rightMargin: 12
        width: children.length ? children[0].implicitWidth : 0
        height: win.headerBand
    }

    Toast { id: toast }
    Connections {
        target: store
        function onToast(kind, title, detail) { toast.show(kind, title, detail) }
    }
    ConfirmRemove { id: confirmRemove }
    Item { id: overlay; anchors.fill: parent; z: 1000 }   // frameless: resize edges
}
