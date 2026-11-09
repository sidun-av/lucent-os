pragma Singleton
import QtQuick

// Lucent design tokens, from docs/mockups/lucent.css (:root and .dark).
// Sizes are the mockups' CSS pixels at 1x.
QtObject {
    readonly property bool dark: System.dark
    readonly property color accent: System.accent
    readonly property color accentSoft: Qt.rgba(accent.r, accent.g, accent.b, dark ? 0.18 : 0.12)
    readonly property color accentText: "#ffffff"

    readonly property color text: dark ? "#eef0f5" : "#1b1f27"
    readonly property color text2: dark ? "#b4bac6" : "#4c5463"
    readonly property color text3: dark ? "#959cab" : "#6a7282"
    readonly property color line: dark ? Qt.rgba(1, 1, 1, 0.09) : Qt.rgba(20 / 255, 28 / 255, 45 / 255, 0.10)
    readonly property color lineStrong: dark ? Qt.rgba(1, 1, 1, 0.15) : Qt.rgba(20 / 255, 28 / 255, 45 / 255, 0.16)
    readonly property color winBg: dark ? "#1f2229" : "#ffffff"
    readonly property color winSide: dark ? "#191b21" : "#f4f5f8"
    readonly property color field: dark ? "#2b2f38" : "#eceef3"
    readonly property color hover: dark ? Qt.rgba(1, 1, 1, 0.05) : Qt.rgba(20 / 255, 28 / 255, 45 / 255, 0.05)
    readonly property color sel: Qt.rgba(accent.r, accent.g, accent.b, dark ? 0.22 : 0.14)
    readonly property color card: dark ? "#262a32" : "#ffffff"
    readonly property color card2: dark ? "#23262d" : "#f7f8fa"
    readonly property color ok: dark ? "#3cc47a" : "#1f9d55"
    readonly property color okSoft: Qt.rgba(31 / 255, 157 / 255, 85 / 255, dark ? 0.2 : 0.12)
    readonly property color warn: dark ? "#f0b04a" : "#b86e00"
    readonly property color warnSoft: dark ? "#3a2e17" : "#fff3df"
    readonly property color danger: dark ? "#f06a6a" : "#d23b3b"
    readonly property color dangerSoft: dark ? "#3a1f22" : "#fdecec"
    readonly property color popup: dark ? "#262a32" : "#ffffff"
    readonly property color scrim: Qt.rgba(15 / 255, 20 / 255, 35 / 255, dark ? 0.45 : 0.18)
    readonly property color shadow: Qt.rgba(0, 0, 0, dark ? 0.25 : 0.10)
    readonly property color toastBg: dark ? "#eef0f5" : "#1b1f27"
    readonly property color toastText: dark ? "#1b1f27" : "#ffffff"
    readonly property color avatarFrom: "#ffb37a"
    readonly property color avatarTo: "#f2668b"

    // ---- type (px at 1x) and weights ----
    readonly property string font: "Inter"
    readonly property int fontH1: 30          // .pane h1
    readonly property int weightH1: 700
    readonly property int fontH2: 21          // .hero h2
    readonly property int fontDialogTitle: 19
    readonly property int fontLead: 16        // .pane .lead
    readonly property int fontLabel: 16       // .row .lbl
    readonly property int weightLabel: 550
    readonly property int fontBody: 15        // body, buttons, values
    readonly property int fontSub: 14         // .row .sub, .gh
    readonly property int fontSmall: 13       // pills, badges, captions
    readonly property int fontName: 17        // sidebar account name
    readonly property int weightStrong: 600
    readonly property int weightHeading: 650  // .gh, .hero h2

    // ---- radii ----
    readonly property int radiusCard: 14      // .group
    readonly property int radiusChoice: 16    // .th, .wbo (big choice cards)
    readonly property int radiusHero: 18      // .hero
    readonly property int radiusDialog: 16
    readonly property int radiusControl: 10   // .btn, .search, fields, .seg track
    readonly property int radiusSegment: 7    // .seg .tbtn
    readonly property int radiusItem: 9       // .si, .sq
    readonly property int radiusPreview: 10   // theme preview, thumbnails
    readonly property int radiusKey: 7        // .keycap
    readonly property int radiusBanner: 12
    readonly property int radiusPopup: 12     // menus, drop-downs
    readonly property int radiusPill: 13
    readonly property int radiusTile: 10      // icon tile in a row
    readonly property int radiusThumb: 8      // wallpaper thumbnail
    readonly property int radiusHeroIcon: 18
    readonly property int iconGlyph: 20
    readonly property int heroIcon: 64
    readonly property int swatch: 34          // accent colour circles
    readonly property int swatchGap: 10     // .row .val gap wins over .accents in the mockup
    readonly property int radio: 22
    readonly property int sliderTrack: 6
    readonly property int sliderKnob: 22
    readonly property int dot: 12             // version dots
    readonly property int logo: 64

    // ---- sizes and spacing ----
    readonly property int sidebarWidth: 340
    readonly property int sidebarPadV: 18
    readonly property int sidebarPadH: 14
    readonly property int sideItemHeight: 46
    readonly property int sideIcon: 30        // .sq
    readonly property int avatarSide: 52
    readonly property int panePadV: 40
    readonly property int panePadH: 64
    readonly property int paneMaxWidth: 1300
    readonly property int leadMaxWidth: 900
    readonly property int sectionTop: 30      // space under the lead
    readonly property int groupTop: 26        // .gh margin-top
    readonly property int groupBottom: 10     // .gh margin-bottom
    readonly property int rowPadV: 16
    readonly property int rowPadH: 20
    readonly property int rowMin: 64
    readonly property int rowGap: 16
    readonly property int controlHeight: 40   // .btn, .search, fields
    readonly property int segHeight: 36
    readonly property int switchWidth: 44
    readonly property int switchHeight: 26
    readonly property int iconTile: 36        // coloured tile in a row
    readonly property int choiceGap: 22      // gap between big choice cards
    readonly property int previewHeight: 200  // theme preview
    readonly property real ringWidth: 4       // accent-soft ring around a chosen card
    // Sidebar square colours (.sq.c-*)
    readonly property var sq: ({
        network: "#3b82f6", bluetooth: "#2f6ff0", display: "#0ea5a3", sound: "#ec4d6e",
        appearance: "#8b5cf6", habits: "#334155", users: "#f59e0b", updates: "#22a35a", winapps: "#64748b",
        about: "#64748b"
    })

    function hex(c) {  // "#aarrggbb" for image://sym
        return c.toString().replace("#", "")
    }
    function sym(name, c) {
        return "image://sym/" + name + "/" + hex(c)
    }
}
