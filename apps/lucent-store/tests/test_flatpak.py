"""flatpak command lines, output parsing and progress."""

from lucent_store import flatpak
from lucent_store.flatpak import Progress


def test_install_is_system_wide_from_flathub():
    assert flatpak.install_cmd(["org.gimp.GIMP", "org.kde.okular"]) == [
        "flatpak", "install", "--system", "-y", "--or-update", "flathub", "org.gimp.GIMP", "org.kde.okular"]


def test_install_never_disables_polkit_prompts():
    # --noninteractive would stop polkit from asking a non-admin for a password.
    for cmd in (flatpak.install_cmd(["a.b.C"]), flatpak.uninstall_cmd("a.b.C"), flatpak.update_cmd()):
        assert "--noninteractive" not in cmd and "sudo" not in cmd and "pkexec" not in cmd


def test_uninstall_uses_the_apps_installation():
    assert flatpak.uninstall_cmd("org.gimp.GIMP") == ["flatpak", "uninstall", "--system", "-y", "org.gimp.GIMP"]
    assert flatpak.uninstall_cmd("x.y.Z", installation="user") == ["flatpak", "uninstall", "--user", "-y", "x.y.Z"]


def test_update_commands():
    assert flatpak.update_cmd() == ["flatpak", "update", "--system", "-y"]
    assert flatpak.update_cmd(["org.gimp.GIMP"]) == ["flatpak", "update", "--system", "-y", "org.gimp.GIMP"]
    assert flatpak.appstream_refresh_cmd() == ["flatpak", "update", "--system", "--appstream", "flathub"]


def test_read_only_queries():
    assert flatpak.list_cmd() == ["flatpak", "list", "--app",
                                  "--columns=application,name,version,branch,origin,installation,size"]
    assert flatpak.updates_cmd() == ["flatpak", "remote-ls", "--system", "--updates",
                                     "--columns=ref,name,version,download-size"]
    assert flatpak.sizes_cmd() == ["flatpak", "remote-ls", "--system", "--cached", "--app",
                                   "--columns=application,download-size,installed-size", "flathub"]
    assert flatpak.metadata_cmd("org.gimp.GIMP") == [
        "flatpak", "remote-info", "--system", "--cached", "--show-metadata", "flathub", "org.gimp.GIMP"]
    assert flatpak.metadata_cmd("org.gimp.GIMP", installation="system") == [
        "flatpak", "info", "--system", "--show-metadata", "org.gimp.GIMP"]


def test_english_c_locale_for_parsing():
    env = flatpak.cli_env({"LANG": "ru_RU.UTF-8", "LANGUAGE": "ru", "HOME": "/home/u"})
    assert env["LC_ALL"] == "C.UTF-8" and "LANGUAGE" not in env and env["HOME"] == "/home/u"


LIST = """org.gimp.GIMP\tGNU Image Manipulation Program\t3.2.8\tstable\tflathub\tsystem\t1.2 GB
org.kde.okular\tOkular\t25.08.3\tstable\tflathub\tsystem\t95.3 MB
ai.storyteller.photocraft\tPhotoCraft\t0.22.0\tmaster\tphotocraft-origin\tuser\t41.0 MB
"""


def test_parse_list():
    apps = flatpak.parse_list(LIST)
    assert [a.id for a in apps] == ["org.gimp.GIMP", "org.kde.okular", "ai.storyteller.photocraft"]
    gimp = apps[0]
    assert (gimp.name, gimp.version, gimp.origin, gimp.installation, gimp.size) == (
        "GNU Image Manipulation Program", "3.2.8", "flathub", "system", "1.2 GB")
    assert apps[2].installation == "user"
    assert flatpak.parse_list("") == []


UPDATES = """app/org.gimp.GIMP/x86_64/stable\tGNU Image Manipulation Program\t3.2.10\t310.4 MB
runtime/org.gnome.Platform/x86_64/51\tGNOME Application Platform version 51\t\t120.0 MB
runtime/org.gimp.GIMP.Locale/x86_64/stable\tTranslations\t\t2.0 MB
app/org.kde.okular/x86_64/stable\tOkular\t25.08.4\t12.1 MB
"""


def test_parse_updates_splits_apps_and_shared_parts():
    ups = flatpak.parse_updates(UPDATES)
    assert [(u.id, u.version, u.download) for u in ups.apps] == [
        ("org.gimp.GIMP", "3.2.10", "310.4 MB"), ("org.kde.okular", "25.08.4", "12.1 MB")]
    assert ups.runtimes == 2
    assert ups.count == 2


def test_parse_sizes():
    out = "org.gimp.GIMP\t310.4 MB\t1.2 GB\norg.kde.okular\t40.0 MB\t95.3 MB\n"
    assert flatpak.parse_sizes(out) == {"org.gimp.GIMP": ("310.4 MB", "1.2 GB"),
                                        "org.kde.okular": ("40.0 MB", "95.3 MB")}


# --- progress -----------------------------------------------------------------

def test_progress_lines_of_a_multi_step_install():
    p = flatpak.ProgressParser()
    assert p.feed("Looking for matches…\n") == []
    assert p.feed("Installing 1/3…\n") == [Progress("install", 1, 3, 0)]
    got = p.feed("Installing 1/3… ████████▍            42%  3.4 MB/s  00:15\n")
    assert got == [Progress("install", 1, 3, 42)]
    assert round(got[0].fraction, 3) == round(0.42 / 3, 3)
    got = p.feed("Installing 3/3… ████████████████████ 100%  2.1 MB/s  00:00\nInstallation complete.\n")
    assert got[-1].fraction == 1.0


def test_progress_single_step_and_split_reads():
    p = flatpak.ProgressParser()
    assert p.feed("Uninstalling…\n") == [Progress("uninstall", 1, 1, 0)]
    assert p.feed("Updating… ██     ") == []        # partial line: wait for the rest
    assert p.feed(" 55%\n") == [Progress("update", 1, 1, 55)]


def test_progress_tolerates_carriage_returns_and_ascii_ellipsis():
    p = flatpak.ProgressParser()
    got = p.feed("Installing 2/2... 10%\rInstalling 2/2... 20%\n")
    assert got == [Progress("install", 2, 2, 10), Progress("install", 2, 2, 20)]


def test_error_message_from_stderr():
    err = "Looking for matches…\nerror: No remote refs found for ‘org.nope.App’\n"
    assert flatpak.error_message(err) == "No remote refs found for ‘org.nope.App’"
    assert flatpak.error_message("Warning: foo\n") == "Warning: foo"
    assert flatpak.error_message("") == ""
