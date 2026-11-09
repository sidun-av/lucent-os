import ctypes.util

import pytest
from conftest import FakeRunner, fixture

from lucent_settings.backends import users

FIND = ("busctl", "--system", "--json=short", "call", "org.freedesktop.Accounts", "/org/freedesktop/Accounts")
PROPS = ("busctl", "--system", "--json=short", "get-property", "org.freedesktop.Accounts")


def acc_runner():
    return (FakeRunner()
            .on(*FIND, out='{"type":"o","data":["/org/freedesktop/Accounts/User1000"]}\n')
            .on(*PROPS, out=fixture("accounts-user.txt")))


def test_me_from_accountsservice():
    me = users.Users(acc_runner(), user="lucent").me()
    assert me.path == "/org/freedesktop/Accounts/User1000"
    assert (me.login, me.real_name, me.admin) == ("lucent", "", True)
    assert me.display_name == "lucent"
    assert me.icon == "/var/lib/AccountsService/icons/lucent"
    r = acc_runner()
    users.Users(r, user="lucent").me()
    assert r.calls[0][-3:] == ["FindUserByName", "s", "lucent"]


def test_initials():
    assert users.initials("Anna Smirnova") == "AS"
    assert users.initials("анна") == "А"
    assert users.initials("") == "?"
    assert users.initials("  john   ronald reuel tolkien ") == "JT"


def test_set_name_and_avatar(runner):
    u = users.Users(runner, user="lucent")
    path = "/org/freedesktop/Accounts/User1000"
    u.set_real_name(path, "Anna Smirnova")
    u.set_icon(path, "/home/lucent/.cache/lucent-settings/avatar.png")
    assert runner.calls == [
        ["busctl", "--system", "--json=short", "--timeout=120", "call", "org.freedesktop.Accounts", path,
         "org.freedesktop.Accounts.User", "SetRealName", "s", "Anna Smirnova"],
        ["busctl", "--system", "--json=short", "--timeout=120", "call", "org.freedesktop.Accounts", path,
         "org.freedesktop.Accounts.User", "SetIconFile", "s", "/home/lucent/.cache/lucent-settings/avatar.png"],
    ]


def test_password_goes_in_process_hashed_never_in_argv(runner):
    sent = []
    u = users.Users(runner, user="lucent",
                    secret_call=lambda path, method, *args: sent.append((path, method, args)) or (True, ""))
    ok, _msg = u.set_password("/org/freedesktop/Accounts/User1000", "correct horse")
    assert ok and runner.calls == []
    (path, method, (hashed, hint)), = sent
    assert method == "SetPassword" and hint == ""
    assert hashed.startswith("$") and "correct horse" not in hashed


def test_password_rules():
    assert users.password_problem("", "") == "empty"
    assert users.password_problem("abc", "abd") == "mismatch"
    assert users.password_problem("abc", "abc") == "short"
    assert users.password_problem("long enough", "long enough") is None


@pytest.mark.skipif(not ctypes.util.find_library("crypt"), reason="no libcrypt here (macOS)")
def test_hash_verifies_with_libcrypt():
    h = users.hash_password("correct horse")
    assert users.verify("correct horse", h) and not users.verify("wrong", h)
