import json

from conftest import FakeRunner, fixture

from lucent_settings.backends import updates

STATUS = ("rpm-ostree", "status", "--json")


def test_fresh_install_has_one_version():
    r = FakeRunner().on(*STATUS, out=fixture("rpm-ostree-booted.json"))
    st = updates.Updates(r).status()
    assert [v.role for v in st.versions] == ["current"]
    cur = st.versions[0]
    assert cur.build == "45.20261109.0" and cur.date.year == 2026
    assert st.pending is None and st.previous is None and st.available is None
    assert not st.can_roll_back


def test_staged_update_and_previous_version():
    r = FakeRunner().on(*STATUS, out=fixture("rpm-ostree-staged.json"))
    st = updates.Updates(r).status()
    assert [v.role for v in st.versions] == ["update", "current", "previous"]
    assert st.pending.build == "45.20261116.0"
    assert st.can_roll_back
    assert st.available.build == "45.20261116.0"


def test_after_a_rollback_the_older_version_is_pending():
    data = json.loads(fixture("rpm-ostree-staged.json"))
    staged, booted, old = data["deployments"]
    data["deployments"] = [old, booted]
    data["cached-update"] = None
    r = FakeRunner().on(*STATUS, out=json.dumps(data))
    st = updates.Updates(r).status()
    assert [v.role for v in st.versions] == ["rollback", "current"]
    assert not st.can_roll_back and st.rollback_pending


def test_registry_reference_from_the_deployment_origin():
    ref = updates.registry_ref
    assert ref("ostree-unverified-registry:ghcr.io/sidun-av/lucent-os:latest") == "docker://ghcr.io/sidun-av/lucent-os:latest"
    assert ref("ostree-image-signed:docker://ghcr.io/sidun-av/lucent-os:latest") == "docker://ghcr.io/sidun-av/lucent-os:latest"
    assert ref("ostree-remote-image:fedora:docker://quay.io/x/y:1") == "docker://quay.io/x/y:1"
    assert ref("ostree-unverified-image:oci:/var/tmp/img") is None
    assert ref("") is None


def staged_on(digest_booted, digest_staged=None):
    data = json.loads(fixture("rpm-ostree-booted.json"))
    dep = data["deployments"][0]
    dep["container-image-reference"] = "ostree-unverified-registry:ghcr.io/sidun-av/lucent-os:latest"
    dep["container-image-reference-digest"] = digest_booted
    if digest_staged:
        data["deployments"].insert(0, dict(dep, booted=False, staged=True, checksum="ffff",
                                           **{"container-image-reference-digest": digest_staged}))
    return json.dumps(data)


ARM64 = "sha256:297b06b2d507849084fce5e5cbedf89afd10d7c8879cbb270388290070ed0cbb"


def test_check_compares_the_registry_digest_for_this_cpu(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    old = "sha256:a90007444bbd50fed471a5a4241dac46dc2ecaca3efd649210d91cebddafee9b"
    r = (FakeRunner().on(*STATUS, out=staged_on(old))
         .on("skopeo", "inspect", "--raw", out=fixture("skopeo-index.json")))
    u = updates.Updates(r, machine="aarch64")
    assert u.check() == (True, True, "")
    assert r.called("skopeo", "inspect", "--raw", "docker://ghcr.io/sidun-av/lucent-os:latest")
    assert not r.called("rpm-ostree", "upgrade")
    # the badge survives a restart of Settings
    assert u.status().available is not None
    # already running it: nothing to do
    r2 = (FakeRunner().on(*STATUS, out=staged_on(ARM64))
          .on("skopeo", "inspect", "--raw", out=fixture("skopeo-index.json")))
    assert updates.Updates(r2, machine="aarch64").check() == (True, False, "")
    # already downloaded and waiting for a restart: nothing new either
    r3 = (FakeRunner().on(*STATUS, out=staged_on(old, ARM64))
          .on("skopeo", "inspect", "--raw", out=fixture("skopeo-index.json")))
    assert updates.Updates(r3, machine="aarch64").check() == (True, False, "")


def test_check_single_arch_tag_hashes_the_manifest(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    r = (FakeRunner().on(*STATUS, out=staged_on(ARM64))
         .on("skopeo", "inspect", "--raw", out=fixture("skopeo-arm64-manifest.json")))
    assert updates.Updates(r, machine="aarch64").check() == (True, False, "")


def test_check_without_a_registry_origin_asks_rpm_ostree():
    oci = fixture("rpm-ostree-booted.json").replace("ostree-unverified-registry:localhost/lucent-vmtest:latest",
                                                    "ostree-unverified-image:oci:/var/tmp/img")
    none = FakeRunner().on(*STATUS, out=oci).on(
        "rpm-ostree", "upgrade", "--check", code=77, out="No updates available.\n")
    assert updates.Updates(none).check() == (True, False, "")
    bad = FakeRunner().on(*STATUS, out=oci).on(
        "rpm-ostree", "upgrade", "--check", code=1,
        err="error: Creating importer: failed to invoke method OpenImage: pinging container registry localhost: connection refused\n")
    ok, available, msg = updates.Updates(bad).check()
    assert not ok and "connection refused" in msg


def test_check_offline():
    r = (FakeRunner().on(*STATUS, out=staged_on(ARM64))
         .on("skopeo", "inspect", "--raw", code=1, err="Error: pinging container registry ghcr.io: dial tcp: lookup ghcr.io: no such host\n"))
    ok, available, msg = updates.Updates(r, machine="aarch64").check()
    assert not ok and "no such host" in msg


def test_apply_rollback_and_reboot_commands(runner):
    u = updates.Updates(runner)
    u.apply()
    u.roll_back()
    u.reboot()
    assert runner.calls[0] == ["rpm-ostree", "upgrade"]
    assert runner.calls[1] == ["rpm-ostree", "rollback"]
    # Plasma's own confirm-and-restart (saves the session, like the Power menu)
    assert runner.calls[2] == ["busctl", "--user", "--json=short", "call", "org.kde.LogoutPrompt",
                               "/LogoutPrompt", "org.kde.LogoutPrompt", "promptReboot"]


def test_auto_updates(tmp_path, monkeypatch, runner):
    conf = tmp_path / "rpm-ostreed.conf"
    conf.write_text("[Daemon]\n#AutomaticUpdatePolicy=none\n")
    monkeypatch.setattr(updates, "RPM_OSTREED_CONF", conf)
    u = updates.Updates(runner)
    assert u.auto_updates() is False
    conf.write_text("[Daemon]\nAutomaticUpdatePolicy=stage\n")
    assert u.auto_updates() is True
    u.set_auto_updates(False)
    assert runner.calls == [["pkexec", "/usr/libexec/lucent/settings-helper", "auto-updates", "off"]]


def test_flatpak_updates():
    out = "org.mozilla.firefox\tFirefox\t146.0\norg.gimp.GIMP\tGIMP\t3.0.6\n"
    r = FakeRunner().on("flatpak", "remote-ls", out=out)
    apps = updates.Updates(r).flatpak_updates()
    assert [(a.id, a.name, a.version) for a in apps] == [("org.mozilla.firefox", "Firefox", "146.0"),
                                                         ("org.gimp.GIMP", "GIMP", "3.0.6")]
    assert r.calls[0] == ["flatpak", "remote-ls", "--system", "--updates", "--app",
                          "--columns=application,name,version"]
    r2 = FakeRunner()
    updates.Updates(r2).flatpak_update()
    assert r2.calls == [["flatpak", "update", "--system", "-y", "--noninteractive"]]


def test_last_check_is_remembered(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    u = updates.Updates(FakeRunner())
    assert u.last_check() is None
    u.remember_check(1794233640)
    assert u.last_check() == 1794233640
