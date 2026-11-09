"""Flatpak sandbox metadata in plain words."""

from lucent_store import permissions

GIMP = """[Application]
name=org.gimp.GIMP
runtime=org.gnome.Platform/x86_64/51

[Context]
shared=network;ipc;
sockets=x11;wayland;pulseaudio;fallback-x11;
devices=dri;all;
filesystems=host;xdg-config/GIMP;/tmp;xdg-run/gvfs;!~/.gnupg;

[Session Bus Policy]
org.freedesktop.Notifications=talk
"""

CALM = """[Application]
name=org.example.Calm

[Context]
sockets=wayland;fallback-x11;
devices=dri;
filesystems=xdg-documents:ro;xdg-download;xdg-config/calm:create;
"""

ESCAPE = """[Context]
shared=network;
sockets=x11;session-bus;ssh-auth;
filesystems=home;

[Session Bus Policy]
org.freedesktop.Flatpak=talk
org.freedesktop.secrets=talk
"""


def texts(meta):
    return [p.text for p in permissions.describe(meta)]


def test_broad_access_in_plain_words():
    assert texts(GIMP) == [
        "Can read and change all your files",
        "Uses the internet",
        "Can use cameras, game controllers and other devices",
        "Plays sound and can use the microphone",
    ]
    assert permissions.isolation(GIMP) == "limited"


def test_narrow_access():
    assert texts(CALM) == [
        "Can read your Documents folder",
        "Can read and change your Downloads folder",
    ]
    assert permissions.isolation(CALM) == "good"


def test_nothing_at_all():
    assert texts("[Context]\nsockets=wayland;\n") == ["Opens only the files you choose"]
    assert permissions.isolation("[Context]\nsockets=wayland;\n") == "good"


def test_sandbox_escapes_are_flagged():
    perms = permissions.describe(ESCAPE)
    assert [p.text for p in perms] == [
        "Can read and change your home folder",
        "Uses the internet",
        "Can run programs outside its sandbox",
        "Full access to your session's services",
        "Can use your SSH keys",
        "Can use your saved passwords",
        "Can see other windows (older display system)",
    ]
    assert [p.level for p in perms][2] == "high"
    assert permissions.isolation(ESCAPE) == "none"


def test_bad_metadata_is_not_fatal():
    assert texts("not a keyfile") == ["Opens only the files you choose"]
    assert texts("") == ["Opens only the files you choose"]
