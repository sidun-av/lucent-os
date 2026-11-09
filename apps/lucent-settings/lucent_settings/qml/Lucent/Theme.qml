pragma Singleton
import QtQuick

// Lucent design tokens: the ONLY place with visual values. Pages and
// components use these names; a restyle swaps values here.
//
// Source of truth: docs/mockups/concepts-2026/pebble-drift/pebble-drift.css
// (part 1, light and .dark), ported 1:1; the CSS variable is named next to
// each value. Pebble's materials (matte surfaces, raised pillows, sunken
// wells, long soft shadows, radii 18 -> 14 -> 10 -> 6) in Prism's palette.
QtObject {
    readonly property bool dark: System.dark

    // ---- accent (--accent*): the swatch chosen in Settings, else the design's indigo ----
    readonly property bool customAccent: System.customAccent !== ""
    readonly property color accent: customAccent ? System.customAccent : (dark ? "#7088ff" : "#4257e8")
    readonly property color accentHover: customAccent ? Qt.lighter(accent, 1.08) : (dark ? "#8297ff" : "#3549d6")
    readonly property color accentPressed: customAccent ? Qt.darker(accent, 1.12) : (dark ? "#5f77f0" : "#2c3dbb")
    readonly property color accentText: customAccent ? (dark ? Qt.lighter(accent, 1.35) : Qt.darker(accent, 1.15))
                                                     : (dark ? "#9aabff" : "#3346cf")
    readonly property color accentSoft: Qt.rgba(accent.r, accent.g, accent.b, dark ? 0.18 : 0.12)
    readonly property color accentSoftStrong: Qt.rgba(accent.r, accent.g, accent.b, dark ? 0.28 : 0.20)
    readonly property color textOnAccent: customAccent ? "#ffffff" : (dark ? "#0e1230" : "#ffffff")
    readonly property color knobTop: dark ? "#e4e7f3" : "#ffffff"          // --knob
    readonly property color knobBottom: dark ? "#c9cde0" : "#eceef8"
    readonly property var accents: ([                                      // 04-settings swatches
        { color: "#4257e8", name: System.tr("Indigo") }, { color: "#2f7ae0", name: System.tr("Azure") },
        { color: "#1f96a8", name: System.tr("Lagoon") }, { color: "#7a55e0", name: System.tr("Violet") },
        { color: "#a54fc4", name: System.tr("Orchid") }, { color: "#cf4f86", name: System.tr("Rose") },
        { color: "#3f8f68", name: System.tr("Pine") }, { color: "#5f6684", name: System.tr("Slate") }
    ])

    // ---- text (--text-*) ----
    readonly property color text: dark ? "#eef0fa" : "#171a2b"            // primary
    readonly property color text2: dark ? "#bcc1d6" : "#474d66"           // secondary
    readonly property color text3: dark ? "#9ca2bb" : "#525972"           // tertiary
    readonly property color textDisabled: dark ? "#656b84" : "#9095a8"

    // ---- surfaces (--surface-*) ----
    readonly property color surface: dark ? "#1d1f2e" : "#f2f3fa"         // window-solid
    readonly property color raised: dark ? "#33364d" : "#fdfdff"          // raised
    readonly property color raised2: dark ? "#2c2f44" : "#f3f4fb"         // raised-2
    readonly property color selectedCard: dark ? "#343b6a" : "#eef0ff"    // selected
    readonly property color selectedCard2: dark ? "#2e345e" : "#e6e9fd"   // selected-2
    readonly property color well: dark ? Qt.rgba(0, 0, 10 / 255, 0.20) : Qt.rgba(48 / 255, 58 / 255, 120 / 255, 0.065)        // sunken
    readonly property color wellStrong: dark ? Qt.rgba(0, 0, 10 / 255, 0.30) : Qt.rgba(48 / 255, 58 / 255, 120 / 255, 0.11)   // sunken-strong
    readonly property color popup: dark ? Qt.rgba(36 / 255, 38 / 255, 56 / 255, 0.97) : Qt.rgba(248 / 255, 249 / 255, 253 / 255, 0.96)
    readonly property color scrim: dark ? Qt.rgba(14 / 255, 16 / 255, 32 / 255, 0.60) : Qt.rgba(40 / 255, 48 / 255, 100 / 255, 0.18)
    readonly property color hover: dark ? Qt.rgba(220 / 255, 228 / 255, 1, 0.07) : Qt.rgba(48 / 255, 58 / 255, 120 / 255, 0.065)   // state-hover
    readonly property color pressed: dark ? Qt.rgba(220 / 255, 228 / 255, 1, 0.11) : Qt.rgba(48 / 255, 58 / 255, 120 / 255, 0.11)
    readonly property color lineStrong: dark ? Qt.rgba(220 / 255, 228 / 255, 1, 0.14) : Qt.rgba(40 / 255, 50 / 255, 110 / 255, 0.17)
    readonly property color line: dark ? Qt.rgba(220 / 255, 228 / 255, 1, 0.08) : Qt.rgba(40 / 255, 50 / 255, 110 / 255, 0.10)
    readonly property color line2: dark ? Qt.rgba(220 / 255, 228 / 255, 1, 0.14) : Qt.rgba(40 / 255, 50 / 255, 110 / 255, 0.17)  // line-strong
    readonly property color lineControl: dark ? Qt.rgba(220 / 255, 228 / 255, 1, 0.38) : Qt.rgba(40 / 255, 50 / 255, 110 / 255, 0.30)
    readonly property real grainOpacity: dark ? 0.09 : 0.07

    // ---- elevation (--shadow-*), drawn as layers by Shadow.qml: [alpha, y, spread] ----
    readonly property color shadowColor: dark ? "#000000" : "#19235a"
    readonly property var shRaised: dark ? [[0.30, 1, 1], [0.25, 3, 4]] : [[0.10, 1, 1], [0.08, 3, 4]]
    readonly property var shLift: dark ? [[0.30, 2, 2], [0.50, 10, 12]] : [[0.08, 2, 2], [0.22, 10, 12]]
    readonly property color ringRaised: dark ? Qt.rgba(0, 0, 0, 0.35) : Qt.rgba(30 / 255, 40 / 255, 100 / 255, 0.08)
    readonly property color topLight: dark ? Qt.rgba(220 / 255, 228 / 255, 1, 0.08) : Qt.rgba(1, 1, 1, 0.9)   // highlight-top
    readonly property color wellTop: dark ? Qt.rgba(0, 0, 0, 0.35) : Qt.rgba(25 / 255, 35 / 255, 90 / 255, 0.10)  // shadow-sunken

    // ---- status (--status-*) ----
    readonly property color ok: dark ? "#56c08a" : "#2f8a5c"
    readonly property color okSoft: Qt.rgba(ok.r, ok.g, ok.b, dark ? 0.20 : 0.12)
    readonly property color warn: dark ? "#e3a547" : "#b7791f"
    readonly property color warnSoft: Qt.rgba(warn.r, warn.g, warn.b, dark ? 0.20 : 0.13)
    readonly property color danger: dark ? "#ef5f6b" : "#cf3a48"
    readonly property color dangerSoft: Qt.rgba(danger.r, danger.g, danger.b, dark ? 0.18 : 0.10)
    readonly property color toastBg: text
    readonly property color toastText: surface
    // .avatar (artwork): linear-gradient(135deg, #6a86ff, #9a62e0 60%, #d0679c)
    readonly property color avatarFrom: "#6a86ff"
    readonly property color avatarMid: "#9a62e0"
    readonly property color avatarTo: "#d0679c"

    // ---- type (px at 1x) ----
    // Figtree; Inter when the session runs on it (a language Figtree has no
    // letters for, e.g. Russian: lucent-theme font), so Latin and Cyrillic never mix
    readonly property string font: Qt.application.font.family === "Inter" ? "Inter" : "Figtree"
    readonly property int fontH1: 32            // --type-display
    readonly property int weightH1: 800
    readonly property int fontCardTitle: 17     // --type-subhead (card titles)
    readonly property int weightCardTitle: 700
    readonly property int fontH2: 21
    readonly property int fontDialogTitle: 19
    readonly property int fontLead: 16
    readonly property int fontLabel: 16         // .row .t b
    readonly property int weightLabel: 600
    readonly property int fontBody: 15          // --type-body is 15.5: Qt sizes are whole pixels
    readonly property int fontSide: 15
    readonly property int weightSide: 500
    readonly property int fontSub: 14           // --type-small 14.5
    readonly property int fontSmall: 14         // --type-caption: never below 14
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
    readonly property int radiusKey: 6
    readonly property int radiusBanner: 12
    readonly property int radiusPopup: 12
    readonly property int radiusPill: 6       // --radius-chip
    readonly property int radiusTile: 10
    readonly property int radiusSwitch: 10
    readonly property int radiusKnob: 8
    readonly property int radiusSwatch: 13
    readonly property int radiusHeroIcon: 16

    // ---- sizes and spacing ----
    readonly property int headerHeight: 58     // under KWin's title bar (two rows)
    readonly property int headerHeightFrameless: 64   // .head: the one row of the CSD mockup
    readonly property int fontWindowTitle: 16  // .head .ttl
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
