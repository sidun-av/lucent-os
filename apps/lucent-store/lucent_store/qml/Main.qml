// Lucent Store (docs/mockups/06-store.png): sidebar + one page at a time.
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
    color: tk.winBg

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
        if (startPage.indexOf("search:") === 0) { query = startPage.substring(7); page = "search" }
        else page = startPage
    }

    Image {                  // fine grain over the matte surface (pebble .matte::before)
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
            Layout.topMargin: store.t.sideInset
            Layout.bottomMargin: store.t.sideInset
        }
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0
            PageHeader {
                id: header
                Layout.fillWidth: true
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

    Toast { id: toast }
    Connections {
        target: store
        function onToast(kind, title, detail) { toast.show(kind, title, detail) }
    }
    ConfirmRemove { id: confirmRemove }
}
