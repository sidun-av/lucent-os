import QtQuick
import QtQuick.Dialogs
import QtQuick.Layouts
import Lucent

// Every wallpaper on this computer, Lucent's first, plus your own pictures.
Page {
    id: page
    readonly property var st: AppearancePage.s
    // four tiles per row inside a card
    readonly property real tileWidth: (Math.min(Theme.paneMaxWidth, width - Theme.panePadLeft - Theme.panePadRight)
                                       - 2 * Theme.cardPadH - 3 * 16) / 4
    title: System.tr("Wallpaper")
    lead: System.tr("Lucent's wallpapers switch to their night version in dark mode. Your own pictures stay the same.")
    Component.onCompleted: AppearancePage.refresh()

    Banner { text: AppearancePage.error; onDismissed: AppearancePage.clearError() }

    Card {
        title: System.tr("Lucent")
        GridLayout {
            Layout.fillWidth: true
            Layout.topMargin: 12
            columns: 4
            columnSpacing: 16
            rowSpacing: 18
            Repeater {
                model: (page.st.wallTiles || []).filter(t => ["Drift", "Tide", "Aurora", "Lucent"].indexOf(t.name) >= 0)
                WallTile { required property var modelData; tile: modelData; current: page.st.wallpaper || ""
                           Layout.fillWidth: false; Layout.preferredWidth: page.tileWidth
                           onPicked: (p) => AppearancePage.setWallpaper(p) }
            }
        }
    }
    Card {
        title: System.tr("Your pictures")
        subtitle: System.tr("Pictures in your Pictures folder, or any picture you add.")
        GridLayout {
            Layout.fillWidth: true
            Layout.topMargin: 12
            columns: 4
            columnSpacing: 16
            rowSpacing: 18
            Repeater {
                model: (page.st.wallTiles || []).filter(t => t.variant === "picture")
                WallTile { required property var modelData; tile: modelData; current: page.st.wallpaper || ""
                           Layout.fillWidth: false; Layout.preferredWidth: page.tileWidth
                           onPicked: (p) => AppearancePage.setWallpaper(p) }
            }
            AddPictureTile { onClicked: pick.open(); Layout.fillWidth: false; Layout.preferredWidth: page.tileWidth }
        }
    }
    Card {
        title: System.tr("More wallpapers")
        subtitle: System.tr("They come with the system.")
        GridLayout {
            Layout.fillWidth: true
            Layout.topMargin: 12
            columns: 4
            columnSpacing: 16
            rowSpacing: 18
            Repeater {
                model: (page.st.wallTiles || []).filter(t => t.variant === "" && ["Drift", "Tide", "Aurora", "Lucent"].indexOf(t.name) < 0)
                WallTile { required property var modelData; tile: modelData; current: page.st.wallpaper || ""
                           Layout.fillWidth: false; Layout.preferredWidth: page.tileWidth
                           onPicked: (p) => AppearancePage.setWallpaper(p) }
            }
        }
    }
    FileDialog {
        id: pick
        title: System.tr("Choose a picture")
        nameFilters: [System.tr("Pictures") + " (*.jpg *.jpeg *.png *.webp *.avif *.jxl)"]
        onAccepted: AppearancePage.setWallpaper(selectedFile.toString())
    }
}
