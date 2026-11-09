import QtQuick

// .pill: 26 px, 7 px corners; kinds ok | accent | warn | neutral.
Rectangle {
    property alias text: t.text
    property string kind: "neutral"
    implicitHeight: 26
    implicitWidth: t.implicitWidth + 20
    radius: Theme.radiusPill
    color: kind === "ok" ? Theme.okSoft : kind === "accent" ? Theme.accentSoft : kind === "warn" ? Theme.warnSoft : Theme.wellStrong
    LText {
        id: t
        anchors.centerIn: parent
        px: Theme.fontSmall
        weight: Theme.weightHeading
        color: parent.kind === "ok" ? Theme.ok : parent.kind === "accent" ? Theme.accentText : parent.kind === "warn" ? Theme.warn : Theme.text2
    }
}
