import QtQuick

// .pill: 26 px, 13.5/600; kinds ok | accent | warn | neutral.
Rectangle {
    property alias text: t.text
    property string kind: "neutral"
    implicitHeight: 26
    implicitWidth: t.implicitWidth + 20
    radius: Theme.radiusPill
    color: kind === "ok" ? Theme.okSoft : kind === "accent" ? Theme.accentSoft : kind === "warn" ? Theme.warnSoft : Theme.hover
    border.color: kind === "neutral" ? Theme.line : "transparent"
    LText {
        id: t
        anchors.centerIn: parent
        px: Theme.fontSmall
        weight: Theme.weightStrong
        color: parent.kind === "ok" ? Theme.ok : parent.kind === "accent" ? Theme.accent : parent.kind === "warn" ? Theme.warn : Theme.text2
    }
}
