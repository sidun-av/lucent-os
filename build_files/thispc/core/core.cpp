/*
 * Lucent "This PC": enumeration, naming and size logic (see thispc_core.h).
 *
 * SPDX-License-Identifier: Apache-2.0
 */
#include "thispc_core.h"

#include <QCryptographicHash>
#include <QFileInfo>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QRegularExpression>
#include <QSet>

#include <algorithm>

namespace ThisPc
{

namespace
{
constexpr quint64 MinInternalSize = 1024ull * 1024 * 1024; // smaller: OEM/recovery tools

// Mount points that are the operating system itself.
bool isSystemMountPoint(const QString &mp)
{
    static const QSet<QString> exact{QStringLiteral("/"),
                                     QStringLiteral("/sysroot"),
                                     QStringLiteral("/etc"),
                                     QStringLiteral("/var"),
                                     QStringLiteral("/usr"),
                                     QStringLiteral("/boot"),
                                     QStringLiteral("/boot/efi"),
                                     QStringLiteral("/efi"),
                                     QStringLiteral("/home"),
                                     QStringLiteral("/var/home")};
    return exact.contains(mp) || mp.startsWith(QLatin1String("/sysroot/"));
}

// /proc/self/mountinfo escapes blanks as \040 and friends.
QString unescapeMount(const QString &s)
{
    QString out;
    out.reserve(s.size());
    for (int i = 0; i < s.size(); ++i) {
        if (s.at(i) == QLatin1Char('\\') && i + 3 < s.size()) {
            bool ok = false;
            const int code = s.mid(i + 1, 3).toInt(&ok, 8);
            if (ok) {
                out += QChar(code);
                i += 3;
                continue;
            }
        }
        out += s.at(i);
    }
    return out;
}

// "Data (D:)" -> 'D'; letters set by lucent-drive-letters sort first, by letter.
QChar driveLetter(const QString &name)
{
    static const QRegularExpression re(QStringLiteral("\\(([A-Z]):\\)$"));
    const auto m = re.match(name);
    return m.hasMatch() ? m.captured(1).at(0) : QChar(QLatin1Char('~'));
}

int kindRank(DriveKind k)
{
    switch (k) {
    case DriveKind::System:
        return 0;
    case DriveKind::Windows:
        return 1;
    case DriveKind::Other:
        return 2;
    case DriveKind::Removable:
        return 3;
    }
    return 4;
}

QString kindName(DriveKind k)
{
    switch (k) {
    case DriveKind::System:
        return QStringLiteral("system");
    case DriveKind::Windows:
        return QStringLiteral("windows");
    case DriveKind::Removable:
        return QStringLiteral("usb");
    case DriveKind::Other:
        break;
    }
    return QStringLiteral("other");
}

QString shortHash(const QString &s)
{
    return QString::fromLatin1(QCryptographicHash::hash(s.toUtf8(), QCryptographicHash::Sha1).toHex().left(12));
}

bool isHiddenPath(const QString &path, const QString &home)
{
    // Only what lies under the home folder counts: /run/media/.../x is fine.
    if (!path.startsWith(home + QLatin1Char('/')))
        return false;
    const QStringList parts = path.mid(home.size() + 1).split(QLatin1Char('/'), Qt::SkipEmptyParts);
    return std::any_of(parts.cbegin(), parts.cend(), [](const QString &p) {
        return p.startsWith(QLatin1Char('.'));
    });
}
} // namespace

// ---------------------------------------------------------------- sections

QString sectionKey(Section section)
{
    return Text::section(section);
}

// ------------------------------------------------------------------- space

Space spaceFromStatvfs(quint64 frsize, quint64 blocks, quint64 bavail, bool readOnly)
{
    Space s;
    s.total = frsize * blocks;
    s.free = frsize * bavail;
    s.readOnly = readOnly;
    s.valid = s.total > 0;
    return s;
}

int usedPercent(const Space &space)
{
    if (!space.valid || space.total == 0)
        return 0;
    const quint64 free = std::min(space.free, space.total);
    return int(((space.total - free) * 100 + space.total / 2) / space.total);
}

int gaugeStep(const Space &space)
{
    if (!space.valid || space.total == 0)
        return 0;
    const double used = double(space.total - std::min(space.free, space.total)) * 100.0 / double(space.total);
    return std::clamp(int(used / 5.0 + 0.5) * 5, 0, 100);
}

int bytePrecision(quint64 bytes)
{
    if (bytes < 1024)
        return 0;
    double value = double(bytes);
    while (value >= 1024.0)
        value /= 1024.0;
    return value < 10.0 ? 1 : 0;
}

// ------------------------------------------------------------------ drives

namespace
{
// GPT/MBR types that are never a user's drive (as udisks hides them).
bool hiddenPartType(const QString &type)
{
    static const QSet<QString> hidden{
        QStringLiteral("c12a7328-f81f-11d2-ba4b-00a0c93ec93b"), // EFI system
        QStringLiteral("e3c9e316-0b5c-4db8-817d-f92df00215ae"), // Microsoft reserved
        QStringLiteral("de94bba4-06d1-4d40-a16a-bfd50179d6ac"), // Windows recovery
        QStringLiteral("21686148-6449-6e6f-744e-656564454649"), // BIOS boot
        QStringLiteral("0x27"), // hidden NTFS recovery (MBR)
        QStringLiteral("0xef"), // EFI (MBR)
    };
    return hidden.contains(type.toLower());
}

bool isContainer(const QString &fsType)
{
    static const QSet<QString> containers{QStringLiteral("swap"),
                                          QStringLiteral("crypto_luks"),
                                          QStringLiteral("bitlocker"),
                                          QStringLiteral("lvm2_member"),
                                          QStringLiteral("linux_raid_member"),
                                          QStringLiteral("zfs_member")};
    return containers.contains(fsType);
}

void walkLsblk(const QJsonArray &devices, bool parentRemovable, QList<Volume> &out)
{
    for (const QJsonValue &value : devices) {
        const QJsonObject d = value.toObject();
        const QString type = d.value(QLatin1String("type")).toString();
        const QString tran = d.value(QLatin1String("tran")).toString();
        const bool removable = parentRemovable || d.value(QLatin1String("rm")).toBool() || d.value(QLatin1String("hotplug")).toBool()
            || tran == QLatin1String("usb") || tran == QLatin1String("mmc");
        if (type != QLatin1String("loop") && type != QLatin1String("rom")) {
            Volume v;
            v.id = d.value(QLatin1String("kname")).toString();
            v.device = QStringLiteral("/dev/") + v.id;
            v.label = d.value(QLatin1String("label")).toString();
            v.fsType = d.value(QLatin1String("fstype")).toString().toLower();
            v.size = quint64(d.value(QLatin1String("size")).toDouble());
            v.uuid = d.value(QLatin1String("uuid")).toString();
            v.removable = removable;
            v.ignored = hiddenPartType(d.value(QLatin1String("parttype")).toString());
            v.fileSystem = !v.fsType.isEmpty() && !isContainer(v.fsType);
            const QJsonArray mounts = d.value(QLatin1String("mountpoints")).toArray();
            for (const QJsonValue &m : mounts) {
                if (m.isString() && m.toString().startsWith(QLatin1Char('/'))) {
                    v.mountPoint = m.toString();
                    break;
                }
            }
            if (!v.id.isEmpty() && (v.fileSystem || !v.fsType.isEmpty()))
                out << v;
        }
        walkLsblk(d.value(QLatin1String("children")).toArray(), removable, out);
    }
}
} // namespace

QList<Volume> parseLsblk(const QByteArray &json)
{
    QList<Volume> out;
    walkLsblk(QJsonDocument::fromJson(json).object().value(QLatin1String("blockdevices")).toArray(), false, out);
    return out;
}

QString udisksPath(const QString &kname)
{
    QString escaped;
    for (const QChar c : kname) {
        if ((c >= QLatin1Char('a') && c <= QLatin1Char('z')) || (c >= QLatin1Char('A') && c <= QLatin1Char('Z')) || (c >= QLatin1Char('0') && c <= QLatin1Char('9')))
            escaped += c;
        else
            escaped += QStringLiteral("_%1").arg(uint(c.unicode()), 2, 16, QLatin1Char('0'));
    }
    return QStringLiteral("/org/freedesktop/UDisks2/block_devices/") + escaped;
}

QStringList systemDevices(const QString &mountInfo, const std::function<QString(const QString &)> &canonical)
{
    QStringList out;
    const QStringList lines = mountInfo.split(QLatin1Char('\n'), Qt::SkipEmptyParts);
    for (const QString &line : lines) {
        // id parent maj:min root mountpoint options [optional...] - fstype source superopts
        const int dash = line.indexOf(QLatin1String(" - "));
        if (dash < 0)
            continue;
        const QStringList left = line.left(dash).split(QLatin1Char(' '), Qt::SkipEmptyParts);
        const QStringList right = line.mid(dash + 3).split(QLatin1Char(' '), Qt::SkipEmptyParts);
        if (left.size() < 5 || right.size() < 2)
            continue;
        const QString mountPoint = unescapeMount(left.at(4));
        const QString source = unescapeMount(right.at(1));
        if (!isSystemMountPoint(mountPoint) || !source.startsWith(QLatin1String("/dev/")))
            continue;
        const QString dev = canonical(source);
        if (!out.contains(dev))
            out << dev;
    }
    return out;
}

QStringList swapDevices(const QString &procSwaps)
{
    QStringList out;
    const QStringList lines = procSwaps.split(QLatin1Char('\n'), Qt::SkipEmptyParts);
    for (const QString &line : lines) {
        const QString first = line.section(QRegularExpression(QStringLiteral("\\s+")), 0, 0);
        if (first.startsWith(QLatin1String("/dev/")))
            out << first;
    }
    return out;
}

QList<Drive> selectDrives(const QList<Volume> &volumes, const QString &home, const QStringList &systemDevices, const StatFs &statFs)
{
    QList<Drive> drives;

    // The system drive, measured where the user's files are. Asking "/" would
    // describe the read-only composefs image: always full, 0 bytes free.
    Drive sys;
    sys.id = QStringLiteral("home");
    sys.kind = DriveKind::System;
    sys.name = Text::home();
    sys.mountPoint = home;
    sys.space = statFs(home);
    sys.total = sys.space.total;
    if (sys.space.valid)
        sys.free = sys.space.free;
    drives << sys;

    QList<Drive> others;
    for (const Volume &v : volumes) {
        if (!v.fileSystem || v.ignored || v.fsType == QLatin1String("swap"))
            continue;
        if (systemDevices.contains(v.device) || (!v.mountPoint.isEmpty() && isSystemMountPoint(v.mountPoint)))
            continue;
        if (!v.removable && v.size < MinInternalSize)
            continue;

        Drive d;
        d.id = v.id;
        d.device = v.device;
        d.mountPoint = v.mountPoint;
        const bool ntfs = v.fsType == QLatin1String("ntfs") || v.fsType == QLatin1String("ntfs3");
        d.kind = v.removable ? DriveKind::Removable : ntfs ? DriveKind::Windows : DriveKind::Other;
        d.ejectable = v.removable;
        if (!v.label.isEmpty())
            d.name = v.label;
        else
            d.name = v.removable ? Text::usbDrive() : Text::localDisk();

        d.total = v.size;
        if (!v.mountPoint.isEmpty()) {
            d.space = statFs(v.mountPoint);
            if (d.space.valid) {
                d.total = d.space.total;
                d.free = d.space.free;
            }
            d.readOnly = d.space.valid ? d.space.readOnly : d.kind == DriveKind::Windows;
        } else {
            // 99-lucent-windows-readonly.rules: udisks mounts internal NTFS read-only.
            d.readOnly = d.kind == DriveKind::Windows;
        }
        others << d;
    }
    std::stable_sort(others.begin(), others.end(), [](const Drive &a, const Drive &b) {
        if (kindRank(a.kind) != kindRank(b.kind))
            return kindRank(a.kind) < kindRank(b.kind);
        const QChar la = driveLetter(a.name), lb = driveLetter(b.name);
        if (la != lb)
            return la < lb;
        return a.name.localeAwareCompare(b.name) < 0;
    });
    drives << others;
    return drives;
}

QString driveIcon(const Drive &drive)
{
    const QString base = QStringLiteral("lucent-drive-") + kindName(drive.kind);
    if (!drive.free.has_value() || !drive.space.valid)
        return base;
    return base + QLatin1Char('-') + QString::number(gaugeStep(drive.space));
}

// ------------------------------------------------------------ user folders

QList<Folder> userFolders(const std::function<QString(const QString &)> &xdgDir, const QString &home, const std::function<bool(const QString &)> &isDir)
{
    static const QList<QPair<QString, QString>> wanted{
        {QStringLiteral("Desktop"), QStringLiteral("user-desktop")},
        {QStringLiteral("Documents"), QStringLiteral("folder-documents")},
        {QStringLiteral("Downloads"), QStringLiteral("folder-download")},
        {QStringLiteral("Pictures"), QStringLiteral("folder-pictures")},
        {QStringLiteral("Music"), QStringLiteral("folder-music")},
        {QStringLiteral("Videos"), QStringLiteral("folder-videos")},
    };
    QList<Folder> out;
    QSet<QString> seen;
    for (const auto &[id, icon] : wanted) {
        QString path = xdgDir(id);
        while (path.size() > 1 && path.endsWith(QLatin1Char('/')))
            path.chop(1);
        if (path.isEmpty() || path == home || seen.contains(path) || !isDir(path))
            continue;
        seen.insert(path);
        out << Folder{id, path, icon};
    }
    return out;
}

// ------------------------------------------------------------------ recent

QList<RecentFile> pickRecent(const QList<QUrl> &oldestFirst, int max, const QString &home, const std::function<FileFacts(const QString &)> &stat)
{
    QList<RecentFile> out;
    QSet<QString> seen;
    const QString trash = home + QStringLiteral("/.local/share/Trash/");
    for (auto it = oldestFirst.crbegin(); it != oldestFirst.crend() && out.size() < max; ++it) {
        if (!it->isLocalFile())
            continue;
        const QString path = it->toLocalFile();
        if (seen.contains(path) || path.startsWith(trash) || isHiddenPath(path, home))
            continue;
        seen.insert(path);
        const FileFacts f = stat(path);
        if (!f.exists || !f.isFile)
            continue;
        out << RecentFile{path, f.size, f.modified};
    }
    return out;
}

// ----------------------------------------------------------------- entries

QList<Entry> buildEntries(const QList<Folder> &folders, const QList<Drive> &drives, const QList<RecentFile> &recent, const QString &home, const Formatters &fmt)
{
    QList<Entry> out;
    const QString dirMime = QStringLiteral("inode/directory");

    for (const Folder &f : folders) {
        Entry e;
        e.name = QStringLiteral("folder-") + f.id;
        e.displayName = QFileInfo(f.path).fileName();
        e.section = Section::Folders;
        e.detail = Text::items(fmt.itemCount(f.path));
        e.icon = f.icon;
        e.target = QUrl::fromLocalFile(f.path);
        e.localPath = f.path;
        e.mimeType = dirMime;
        out << e;
    }

    for (const Drive &d : drives) {
        Entry e;
        e.name = QStringLiteral("drive-") + d.id;
        e.displayName = d.name;
        e.section = Section::Drives;
        // Like the mockup's drive cards: what is free first, then what it is.
        const QString total = fmt.bytes(d.total);
        if (d.free.has_value()) {
            e.detail = Text::free(fmt.bytes(*d.free));
            e.detail2 = d.readOnly ? Text::readOnly(total) : d.kind == DriveKind::Removable ? Text::usb(total) : Text::ofTotal(total);
        } else {
            e.detail = total;
            e.detail2 = d.readOnly ? Text::readOnly() : d.kind == DriveKind::Removable ? Text::usbDrive() : QString();
        }
        e.icon = driveIcon(d);
        if (d.readOnly)
            e.overlays << QStringLiteral("emblem-locked");
        // Not mounted yet: thispc:/drive-<id> mounts it, then redirects there.
        e.target = d.mountPoint.isEmpty() ? QUrl(QStringLiteral("thispc:/") + e.name) : QUrl::fromLocalFile(d.mountPoint);
        e.mimeType = d.ejectable ? QStringLiteral("inode/x-lucent-removable-drive") : dirMime;
        out << e;
    }

    for (const RecentFile &r : recent) {
        Entry e;
        e.name = QStringLiteral("recent-") + shortHash(r.path);
        const QFileInfo info(r.path);
        e.displayName = info.fileName();
        e.section = Section::Recent;
        const QString parent = info.absolutePath();
        const QString folder = parent == home ? Text::home() : QFileInfo(parent).fileName();
        e.detail = folder;
        e.detail2 = fmt.date(r.modified);
        e.isDir = false;
        e.target = QUrl::fromLocalFile(r.path);
        e.localPath = r.path;
        e.mimeType = fmt.mimeType(r.path);
        e.size = r.size;
        e.modified = r.modified;
        out << e;
    }
    return out;
}

Target parseUrl(const QUrl &url)
{
    Target t;
    if (url.scheme() != QLatin1String("thispc"))
        return t;
    QString path = url.path();
    while (path.startsWith(QLatin1Char('/')))
        path.remove(0, 1);
    while (path.endsWith(QLatin1Char('/')))
        path.chop(1);
    if (path.isEmpty()) {
        t.kind = Target::Root;
        return t;
    }
    if (path.contains(QLatin1Char('/')))
        return t;
    static const QList<QPair<QString, Target::Kind>> prefixes{
        {QStringLiteral("folder-"), Target::Folder},
        {QStringLiteral("drive-"), Target::Drive},
        {QStringLiteral("recent-"), Target::Recent},
    };
    for (const auto &[prefix, kind] : prefixes) {
        if (path.startsWith(prefix) && path.size() > prefix.size()) {
            t.kind = kind;
            t.id = path.mid(prefix.size());
            return t;
        }
    }
    return t;
}

} // namespace ThisPc
