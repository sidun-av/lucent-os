/*
 * Lucent "This PC": enumeration, naming and size logic (see thispc_core.h).
 *
 * SPDX-License-Identifier: Apache-2.0
 */
#include "thispc_core.h"

#include <QCryptographicHash>
#include <QFileInfo>
#include <QRegularExpression>
#include <QSet>

#include <algorithm>

namespace ThisPc
{

namespace
{
constexpr quint64 MinInternalSize = 1024ull * 1024 * 1024; // smaller: OEM/recovery tools
constexpr QChar HairSpace(0x200A);

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
    const int pad = section == Section::Folders ? 2 : section == Section::Drives ? 1 : 0;
    return QString(pad, HairSpace) + Text::section(section);
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

// ------------------------------------------------------------------ drives

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
        QString detail;
        if (d.free.has_value())
            detail = Text::freeOf(fmt.bytes(*d.free), fmt.bytes(d.total));
        else if (d.kind == DriveKind::Removable)
            detail = Text::usb(fmt.bytes(d.total));
        else
            detail = fmt.bytes(d.total);
        e.detail = d.readOnly ? Text::readOnly(detail) : detail;
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
        e.detail = Text::recent(folder, fmt.date(r.modified));
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
