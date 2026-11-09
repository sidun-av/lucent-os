import QtQuick
import QtQuick.Layouts
import Lucent

Page {
    id: page
    readonly property var st: SoundPage.s
    title: System.tr("Sound")
    lead: System.tr("Where sound plays, and the microphone apps use.")
    Component.onCompleted: SoundPage.refresh()
    Timer { interval: 3000; repeat: true; running: true; onTriggered: SoundPage.refresh() }

    component VolumeRow: SettingRow {
        id: vr
        property string kind
        property var dev: ({})
        label: kind === "output" ? System.tr("Volume") : System.tr("Microphone level")
        sub: dev.muted ? (kind === "output" ? System.tr("Muted") : System.tr("Microphone off")) : ""
        leading: Item { width: Theme.iconTile; height: 1 }
        LButton {
            flat: true
            icon: vr.kind === "output" ? (vr.dev.muted ? "mute" : "volume") : "mic"
            text: ""
            implicitWidth: 40
            onClicked: SoundPage.setMuted(vr.kind, !vr.dev.muted)
        }
        LSlider {
            implicitWidth: 360
            from: 0; to: 100; stepSize: 1
            value: vr.dev.volume || 0
            onMoved: SoundPage.setVolume(vr.kind, Math.round(value))
        }
        LText { text: Math.round(vr.dev.volume || 0) + "%"; px: Theme.fontBody; color: Theme.text2; Layout.preferredWidth: 46; horizontalAlignment: Text.AlignRight }
    }

    GroupHeader { text: System.tr("Output"); Layout.topMargin: Theme.sectionTop }
    Card {
        SettingRow {
            label: System.tr("Play sound through")
            sub: page.st.noHardware ? System.tr("No speakers or headphones found. Connect some, or check that the sound card is enabled in the firmware.") : ""
            leading: IconTile { icon: "volume"; tint: Theme.sq.sound }
            LCombo {
                implicitWidth: 340
                model: (page.st.outputs || []).map(d => ({ value: d.name, label: d.label }))
                current: page.st.output ? page.st.output.name || "" : ""
                onPicked: (v) => SoundPage.setDefault("output", v)
            }
        }
        VolumeRow { kind: "output"; dev: page.st.output || ({}); visible: (page.st.outputs || []).length > 0 }
    }

    GroupHeader { text: System.tr("Input") }
    Card {
        SettingRow {
            label: System.tr("Microphone")
            sub: (page.st.inputs || []).length === 0 ? System.tr("No microphone found.") : ""
            leading: IconTile { icon: "mic" }
            LCombo {
                visible: (page.st.inputs || []).length > 0
                implicitWidth: 340
                model: (page.st.inputs || []).map(d => ({ value: d.name, label: d.label }))
                current: page.st.input ? page.st.input.name || "" : ""
                onPicked: (v) => SoundPage.setDefault("input", v)
            }
        }
        VolumeRow { kind: "input"; dev: page.st.input || ({}); visible: (page.st.inputs || []).length > 0 }
    }
}
