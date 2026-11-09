"""ArtCraft beta apps through /usr/bin/lucent-nextgen."""

from lucent_store import catalog, nextgen


def wordcraft():
    return catalog.load().nextgen_app("wordcraft")


def test_install_passes_the_audited_version_and_pinned_hash():
    app = wordcraft()
    cmd = nextgen.install_cmd(app, "x86_64")
    assert cmd == ["lucent-nextgen", "install", "--yes", "--version", app.version,
                   "--sha256", app.sha256["x86_64"], "wordcraft"]
    assert nextgen.install_cmd(app, "aarch64")[6] == app.sha256["aarch64"]


def test_unsupported_architecture():
    assert nextgen.install_cmd(wordcraft(), "riscv64") is None


def test_remove_cmd():
    assert nextgen.remove_cmd(wordcraft()) == ["lucent-nextgen", "remove", "wordcraft"]


def test_progress_through_download_verify_install():
    p = nextgen.ProgressParser()
    assert p.feed("\nDownloading wordcraft-0.17.0-linux-x86_64.flatpak\n") == [0.0]
    got = p.feed("\r#####                     12.5%\r##########                50.0%")
    assert got == [0.1]                          # 12.5 % of the download part; 50 % still partial
    assert p.feed("\r####################     100.0%\n") == [0.4, 0.8]
    assert p.feed("\nVerifying\nwordcraft-0.17.0-linux-x86_64.flatpak: OK\n") == [0.82]
    assert p.feed("Installing… ██████████           50%\n") == [0.925]
    assert p.feed("Installation complete.\n") == [1.0]


def test_script_supports_what_the_store_calls():
    script = nextgen.SCRIPT_SOURCE.read_text()
    for flag in ("--yes", "--version", "--sha256"):
        assert flag in script
    for app in catalog.load().nextgen:
        assert f"{app.key})" in script and app.id in script
