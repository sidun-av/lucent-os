"""Your account through AccountsService (org.freedesktop.Accounts): name,
picture and password, each guarded by polkit (changing your own password
asks for it again).

The password is hashed here (libcrypt, the system's default method) and
the hash is sent over D-Bus from inside the process (`secret_call`), never
through argv like the other, non-secret calls.
"""

from __future__ import annotations

import ctypes
import ctypes.util
import getpass
import subprocess
from dataclasses import dataclass
from typing import Callable

from .. import dbus
from ..run import Result, Runner

SERVICE = "org.freedesktop.Accounts"
USER = "org.freedesktop.Accounts.User"
MIN_LENGTH = 4

SecretCall = Callable[..., tuple[bool, str]]


def initials(name: str) -> str:
    words = name.split()
    if not words:
        return "?"
    return (words[0][0] + (words[-1][0] if len(words) > 1 else "")).upper()


def password_problem(new: str, again: str) -> str | None:
    if not new:
        return "empty"
    if new != again:
        return "mismatch"
    if len(new) < MIN_LENGTH:
        return "short"
    return None


def _libcrypt():
    name = ctypes.util.find_library("crypt")
    if not name:
        return None
    lib = ctypes.CDLL(name)
    lib.crypt.restype = ctypes.c_char_p
    lib.crypt.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    if hasattr(lib, "crypt_gensalt"):
        lib.crypt_gensalt.restype = ctypes.c_char_p
        lib.crypt_gensalt.argtypes = [ctypes.c_char_p, ctypes.c_ulong, ctypes.c_char_p, ctypes.c_int]
    return lib


def hash_password(password: str) -> str:
    lib = _libcrypt()
    if lib is not None and hasattr(lib, "crypt_gensalt"):
        # NULL prefix = libxcrypt's default (yescrypt on Fedora).
        setting = lib.crypt_gensalt(None, 0, None, 0)
        if setting:
            out = lib.crypt(password.encode(), setting)
            if out and not out.startswith(b"*"):
                return out.decode()
    p = subprocess.run(["openssl", "passwd", "-6", "-stdin"], input=password + "\n",
                       capture_output=True, text=True, check=True)
    return p.stdout.strip()


def verify(password: str, hashed: str) -> bool:
    lib = _libcrypt()
    if lib is None:
        raise RuntimeError("libcrypt not available")
    out = lib.crypt(password.encode(), hashed.encode())
    return bool(out) and out.decode() == hashed


@dataclass
class Me:
    path: str
    login: str
    real_name: str
    icon: str
    admin: bool

    @property
    def display_name(self) -> str:
        return self.real_name or self.login


def qtdbus_secret_call(path: str, method: str, *args: str) -> tuple[bool, str]:
    """System-bus call from inside the process, with polkit allowed to ask."""
    from PySide6.QtDBus import QDBus, QDBusConnection, QDBusMessage

    msg = QDBusMessage.createMethodCall(SERVICE, path, USER, method)
    msg.setArguments(list(args))
    msg.setInteractiveAuthorizationAllowed(True)
    reply = QDBusConnection.systemBus().call(msg, QDBus.Block, 180_000)
    if reply.type() == QDBusMessage.MessageType.ErrorMessage:
        return False, reply.errorMessage() or reply.errorName()
    return True, ""


class Users:
    def __init__(self, runner: Runner, user: str | None = None, secret_call: SecretCall | None = None):
        self.r = runner
        self.user = user or getpass.getuser()
        self.secret_call = secret_call or qtdbus_secret_call

    def me(self) -> Me | None:
        res = self.r.run(dbus.call(dbus.SYSTEM, SERVICE, "/org/freedesktop/Accounts", SERVICE,
                                   "FindUserByName", "s", self.user))
        if not res.ok:
            return None
        path = dbus.values(res.out)[0][0]
        props = self.r.run(dbus.get_property(dbus.SYSTEM, SERVICE, path, USER,
                                             "UserName", "RealName", "IconFile", "AccountType"))
        vals = dbus.values(props.out) if props.ok else []
        if len(vals) != 4:
            return Me(path, self.user, "", "", False)
        return Me(path=path, login=vals[0], real_name=vals[1], icon=vals[2], admin=vals[3] == 1)

    def _set(self, path: str, method: str, value: str) -> Result:
        # Long timeout: polkit may be waiting for the person to type a password.
        return self.r.run(dbus.call(dbus.SYSTEM, SERVICE, path, USER, method, "s", value, timeout=120),
                          timeout=125)

    def set_real_name(self, path: str, name: str) -> Result:
        return self._set(path, "SetRealName", name.strip())

    def set_icon(self, path: str, file: str) -> Result:
        return self._set(path, "SetIconFile", file)

    def set_password(self, path: str, password: str) -> tuple[bool, str]:
        return self.secret_call(path, "SetPassword", hash_password(password), "")
