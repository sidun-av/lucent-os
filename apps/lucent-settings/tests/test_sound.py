from conftest import FakeRunner, fixture

from lucent_settings.backends import sound


def vm_runner():
    return (FakeRunner()
            .on("pactl", "-f", "json", "list", "sinks", out=fixture("pactl-sinks.json"))
            .on("pactl", "-f", "json", "list", "sources", out=fixture("pactl-sources.json"))
            .on("pactl", "get-default-sink", out="auto_null\n")
            .on("pactl", "get-default-source", out="@DEFAULT_SOURCE@\n"))


def test_vm_has_only_the_dummy_output():
    st = sound.Sound(vm_runner()).state()
    assert [(d.name, d.label, d.volume, d.muted, d.default) for d in st.outputs] == [
        ("auto_null", "Dummy Output", 100, False, True)]
    assert st.inputs == []  # monitors of outputs are not microphones
    assert st.output.name == "auto_null" and st.input is None
    assert st.no_hardware


def test_laptop_outputs():
    r = (FakeRunner()
         .on("pactl", "-f", "json", "list", "sinks", out=fixture("pactl-sinks-laptop.json"))
         .on("pactl", "get-default-sink", out="alsa_output.pci-0000_00_1f.3.analog-stereo\n"))
    st = sound.Sound(r).state()
    assert [d.label for d in st.outputs] == ["Built-in Audio Analog Stereo", "Dell U2723QE (HDMI)"]
    assert st.output.volume == 42 and not st.no_hardware
    assert st.outputs[1].muted


def test_volume_and_mute_commands(runner):
    s = sound.Sound(runner)
    s.set_volume("output", 42)
    s.set_volume("input", 150)
    s.set_muted("output", True)
    s.set_default("output", "alsa_output.hdmi")
    s.set_default("input", "alsa_input.mic")
    assert runner.calls == [
        ["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "0.42"],
        ["wpctl", "set-volume", "@DEFAULT_AUDIO_SOURCE@", "1.00"],
        ["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "1"],
        ["pactl", "set-default-sink", "alsa_output.hdmi"],
        ["pactl", "set-default-source", "alsa_input.mic"],
    ]
