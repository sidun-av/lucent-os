pragma Singleton
import QtQuick

// Lucent design tokens: the ONLY place with visual values. Pages and
// components use these names; a restyle swaps values here.
//
// Direction "Pebble-Drift" (owner's 2026 pick): Pebble's materials and
// structure (docs/mockups/concepts-2026/pebble/pebble.css: near-opaque matte
// surfaces with grain, raised "pillow" controls, sunken wells, long soft
// shadows, radii 18 -> 14 -> 10) in Prism's colours (prism/prism.css: blue
// accent, cool tinted neutrals). Names follow the CSS variables, so the final
// pebble-drift.css maps 1:1 onto this file.
QtObject {
    readonly property bool dark: System.dark

    // ---- accent: the system's (kdeglobals) or the one chosen in Settings ----
    readonly property color accent: System.accent
    readonly property color accentStrong: Qt.darker(accent, dark ? 0.85 : 1.12)
    readonly property color accentSoft: Qt.rgba(accent.r, accent.g, accent.b, dark ? 0.20 : 0.14)
    readonly property color accentText: dark ? Qt.lighter(accent, 1.25) : Qt.darker(accent, 1.18)
    readonly property color textOnAccent: "#ffffff"
    readonly property var accents: ([           // Prism's swatches, solid
        { color: "#3d6bff", name: "Blue" }, { color: "#7b5cff", name: "Violet" },
        { color: "#e8508f", name: "Pink" }, { color: "#e5484d", name: "Red" },
        { color: "#f0731c", name: "Orange" }, { color: "#f2b01e", name: "Yellow" },
        { color: "#1f9d55", name: "Green" }, { color: "#0f9aa8", name: "Teal" },
        { color: "#5f677b", name: "Graphite" }
    ])

    // ---- text ----
    readonly property color text: dark ? "#f2f4fb" : "#10131c"
    readonly property color text2: dark ? "#b9c0d2" : "#444b5c"
    readonly property color text3: dark ? "#9aa2b6" : "#626a7d"

    // ---- surfaces (matte, near-opaque; cool tint) ----
    readonly property color surface: dark ? "#1b1e2b" : "#f6f8fd"      // window body
    readonly property color raised: dark ? "#2a2e3e" : "#ffffff"       // pillow top
    readonly property color raised2: dark ? "#252938" : "#f5f7fc"      // pillow bottom
    readonly property color well: dark ? Qt.rgba(0, 0, 0, 0.20) : Qt.rgba(60 / 255, 80 / 255, 140 / 255, 0.065)
    readonly property color wellStrong: dark ? Qt.rgba(0, 0, 0, 0.28) : Qt.rgba(60 / 255, 80 / 255, 140 / 255, 0.10)
    readonly property color hover: dark ? Qt.rgba(1, 1, 1, 0.06) : Qt.rgba(60 / 255, 80 / 255, 140 / 255, 0.06)
    readonly property color line: dark ? Qt.rgba(1, 1, 1, 0.08) : Qt.rgba(16 / 255, 24 / 255, 48 / 255, 0.09)
    readonly property color line2: dark ? Qt.rgba(1, 1, 1, 0.13) : Qt.rgba(16 / 255, 24 / 255, 48 / 255, 0.15)
    readonly property color selectedCard: dark ? "#2c3350" : "#f3f6ff"   // .card.sel
    readonly property color popup: raised
    readonly property color scrim: Qt.rgba(10 / 255, 14 / 255, 30 / 255, dark ? 0.50 : 0.22)
    readonly property real grainOpacity: dark ? 0.09 : 0.06

    // ---- shadows (layers drawn by Shadow.qml; colour, alpha, y, spread) ----
    readonly property color shadowColor: dark ? "#000000" : "#1e2a6e"
    readonly property var shRaised: dark ? [[0.30, 1, 1], [0.22, 3, 4]] : [[0.07, 1, 1], [0.06, 3, 5]]
    readonly property var shLift: dark ? [[0.32, 2, 2], [0.30, 10, 14]] : [[0.08, 2, 2], [0.12, 10, 16]]
    readonly property color ringRaised: dark ? Qt.rgba(0, 0, 0, 0.35) : Qt.rgba(16 / 255, 24 / 255, 48 / 255, 0.08)
    readonly property color topLight: dark ? Qt.rgba(1, 1, 1, 0.07) : Qt.rgba(1, 1, 1, 0.9)
    readonly property color wellTop: dark ? Qt.rgba(0, 0, 0, 0.35) : Qt.rgba(30 / 255, 40 / 255, 90 / 255, 0.10)

    // ---- status ----
    readonly property color ok: dark ? "#4fd18b" : "#1f9d55"
    readonly property color okSoft: Qt.rgba(31 / 255, 157 / 255, 85 / 255, dark ? 0.22 : 0.12)
    readonly property color warn: dark ? "#f0b04a" : "#b86e00"
    readonly property color warnSoft: dark ? "#3a2e17" : "#fff3df"
    readonly property color danger: dark ? "#ff7b7b" : "#d23b3b"
    readonly property color dangerSoft: dark ? "#3a2026" : "#fdecee"
    readonly property color closeHover: "#d9453a"
    readonly property color toastBg: dark ? "#f2f4fb" : "#10131c"
    readonly property color toastText: dark ? "#10131c" : "#ffffff"
    readonly property color avatarFrom: "#6f9bff"
    readonly property color avatarTo: "#8a5cff"

    // ---- type (px at 1x) ----
    readonly property string font: "Figtree"
    readonly property int fontH1: 32
    readonly property int weightH1: 800
    readonly property int fontCardTitle: 18     // .gt
    readonly property int weightCardTitle: 750
    readonly property int fontH2: 21
    readonly property int fontDialogTitle: 19
    readonly property int fontLead: 16
    readonly property int fontLabel: 16         // .row .t b
    readonly property int weightLabel: 600
    readonly property int fontBody: 15
    readonly property int fontSide: 15          // .si (15.5 in CSS)
    readonly property int weightSide: 500
    readonly property int fontSub: 14
    readonly property int fontSmall: 13
    readonly property int fontName: 16
    readonly property int weightStrong: 600
    readonly property int weightHeading: 650
    readonly property int weightButton: 550

    // ---- radii: window 18 -> card 14 -> control 10 -> chip 6 ----
    readonly property int radiusCard: 14
    readonly property int radiusChoice: 14
    readonly property int radiusHero: 14
    readonly property int radiusDialog: 18
    readonly property int radiusControl: 10
    readonly property int radiusSegTrack: 12
    readonly property int radiusSegment: 9
    readonly property int radiusItem: 10
    readonly property int radiusPreview: 9
    readonly property int radiusThumb: 12
    readonly property int radiusKey: 7
    readonly property int radiusBanner: 12
    readonly property int radiusPopup: 12
    readonly property int radiusPill: 7
    readonly property int radiusTile: 10
    readonly property int radiusSwitch: 10
    readonly property int radiusKnob: 8
    readonly property int radiusSwatch: 13
    readonly property int radiusHeroIcon: 16

    // ---- sizes and spacing ----
    readonly property int headerHeight: 58     // under KWin's title bar (64 in the CSD mockup)
    readonly property int bodyPad: 12           // .body padding / gap
    readonly property int sidebarWidth: 290
    readonly property int sidebarPadV: 12
    readonly property int sidebarPadH: 10
    readonly property int sideItemHeight: 38
    readonly property int sideGlyph: 20
    readonly property int avatarSide: 46
    readonly property int panePadTop: 18
    readonly property int panePadLeft: 30
    readonly property int panePadRight: 26
    readonly property int paneMaxWidth: 1500
    readonly property int leadMaxWidth: 1000
    readonly property int leadBottom: 24
    readonly property int cardGap: 18
    readonly property int cardPadV: 22
    readonly property int cardPadH: 24
    readonly property int groupTop: 18
    readonly property int groupBottom: 10
    readonly property int sectionTop: 0
    readonly property int rowPadV: 14
    readonly property int rowPadH: 0
    readonly property int rowMin: 60
    readonly property int rowGap: 20
    readonly property int controlHeight: 38
    readonly property int fieldHeight: 40
    readonly property int segHeight: 40
    readonly property int switchWidth: 52
    readonly property int switchHeight: 30
    readonly property int iconTile: 36
    readonly property int iconGlyph: 20
    readonly property int choiceGap: 18
    readonly property int previewHeight: 170
    readonly property real ringWidth: 2
    readonly property int heroIcon: 56
    readonly property int swatchHeight: 52
    readonly property int swatchGap: 12
    readonly property int radio: 22
    readonly property int sliderTrack: 10
    readonly property int sliderKnobW: 30
    readonly property int sliderKnobH: 24
    readonly property int dot: 12
    readonly property int logo: 64
    readonly property int searchWidth: 520

    function hex(c) {  // "#aarrggbb" for image://sym
        return c.toString().replace("#", "")
    }
    function sym(name, c) {
        return "image://sym/" + name + "/" + hex(c)
    }
}
