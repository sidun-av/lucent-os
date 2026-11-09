/*
 * kio_thispc: the "This PC" page of Files (Dolphin), thispc:/
 *
 * Lists the user folders, the drives (with free space measured where the
 * files really are) and recently used files. The decisions are in core/
 * (unit-tested); this file only gathers the facts and speaks KIO.
 * Why a KIO worker and not a Dolphin patch: docs/this-pc.md.
 *
 * SPDX-License-Identifier: Apache-2.0
 */
#include "thispc_core.h"

#include <KFormat>
#include <KIO/UDSEntry>
#include <KIO/WorkerBase>
#include <KLocalizedString>
#include <KRecentDocument>

#include <QCoreApplication>
#include <QDBusConnection>
#include <QDBusMessage>
#include <QDBusReply>
#include <QDir>
#include <QDirIterator>
#include <QFile>
#include <QFileInfo>
#include <QMimeDatabase>
#include <QProcess>
#include <QStandardPaths>

#include <cstdio>
#include <sys/stat.h>
#include <sys/statvfs.h>

using namespace ThisPc;

class KIOPluginForMetaData : public QObject
{
    Q_OBJECT
    Q_PLUGIN_METADATA(IID "org.kde.kio.worker.thispc" FILE "thispc.json")
};

namespace
{
const int RecentMax = 10;

QString readFile(const QString &path)
{
    QFile f(path);
    return f.open(QIODevice::ReadOnly) ? QString::fromUtf8(f.readAll()) : QString();
}

QString canonical(const QString &path)
{
    const QString c = QFileInfo(path).canonicalFilePath();
    return c.isEmpty() ? path : c;
}

Space statFs(const QString &path)
{
    struct statvfs s;
    if (::statvfs(QFile::encodeName(path).constData(), &s) != 0)
        return {};
    return spaceFromStatvfs(s.f_frsize, s.f_blocks, s.f_bavail, s.f_flag & ST_RDONLY);
}

QString homePath()
{
    return canonical(QDir::homePath()); // /home/anna -> /var/home/anna
}

struct Gathered {
    QList<Volume> volumes;
    QHash<QString, QString> udiById; // volume id -> udisks object path
    QHash<QString, QString> uuidById; // volume id -> file system UUID
};

// File systems this session already opened for the page: if the user then
// unmounts one, This PC must not open it again behind their back.
QString automountedList()
{
    return QStandardPaths::writableLocation(QStandardPaths::RuntimeLocation) + QStringLiteral("/lucent-thispc-automounted");
}

QStringList automounted()
{
    QFile f(automountedList());
    return f.open(QIODevice::ReadOnly) ? QString::fromUtf8(f.readAll()).split(QLatin1Char('\n'), Qt::SkipEmptyParts) : QStringList();
}

void rememberAutomounted(const QString &uuid)
{
    QFile f(automountedList());
    if (!uuid.isEmpty() && f.open(QIODevice::Append))
        f.write(uuid.toUtf8() + '\n');
}

// The drives as the kernel and udev see them right now. The worker process
// lives on between listings; Solid's cache in it missed mounts and newly
// plugged sticks (seen in the VM), lsblk never does (~10 ms).
Gathered gatherVolumes()
{
    Gathered g;
    QProcess lsblk;
    lsblk.start(QStringLiteral("lsblk"), {QStringLiteral("-J"), QStringLiteral("-b"), QStringLiteral("-o"), QString::fromLatin1(LsblkColumns)});
    if (!lsblk.waitForFinished(10000) || lsblk.exitCode() != 0)
        return g;
    g.volumes = parseLsblk(lsblk.readAllStandardOutput());
    for (const Volume &v : std::as_const(g.volumes)) {
        g.udiById.insert(v.id, udisksPath(v.id));
        g.uuidById.insert(v.id, v.uuid);
    }
    return g;
}

QStringList osDevices()
{
    QStringList devs = systemDevices(readFile(QStringLiteral("/proc/self/mountinfo")), canonical);
    for (const QString &swap : swapDevices(readFile(QStringLiteral("/proc/swaps"))))
        devs << canonical(swap);
    return devs;
}

// udisks Filesystem.Mount. Without interaction (listing the page) polkit
// must already allow it: the active user's USB drives, and for wheel
// members the Windows partitions (50-lucent-windows-disks.rules, read-only).
QString mount(const QString &udi, bool interactive, QString *error)
{
    QDBusMessage call = QDBusMessage::createMethodCall(QStringLiteral("org.freedesktop.UDisks2"),
                                                       udi,
                                                       QStringLiteral("org.freedesktop.UDisks2.Filesystem"),
                                                       QStringLiteral("Mount"));
    QVariantMap options;
    if (!interactive)
        options.insert(QStringLiteral("auth.no_user_interaction"), true);
    call << options;
    const QDBusReply<QString> reply = QDBusConnection::systemBus().call(call, QDBus::Block, interactive ? 300000 : 5000);
    if (!reply.isValid()) {
        if (error)
            *error = reply.error().message();
        return {};
    }
    return reply.value();
}

int countItems(const QString &path)
{
    int n = 0;
    QDirIterator it(path, QDir::AllEntries | QDir::NoDotAndDotDot | QDir::System);
    while (it.hasNext()) {
        it.next();
        ++n;
    }
    return n;
}

Formatters formatters()
{
    Formatters f;
    // KFormat follows the user's unit setting (KiB/KB) like the rest of Files.
    f.bytes = [](quint64 b) {
        return KFormat().formatByteSize(double(b), bytePrecision(b));
    };
    // "Today", "Yesterday", else the short date, as Files' Modified column.
    f.date = [](const QDateTime &t) {
        return KFormat().formatRelativeDate(t.date(), QLocale::ShortFormat);
    };
    f.itemCount = countItems;
    f.mimeType = [](const QString &path) {
        return QMimeDatabase().mimeTypeForFile(path, QMimeDatabase::MatchExtension).name();
    };
    return f;
}

KIO::UDSEntry toUds(const Entry &e)
{
    KIO::UDSEntry u;
    u.fastInsert(KIO::UDSEntry::UDS_NAME, e.name);
    u.fastInsert(KIO::UDSEntry::UDS_DISPLAY_NAME, e.displayName);
    // Dolphin groups this page by "Type" (view properties seeded by
    // design-defaults) and shows "Owner" and "User Group" as the two grey
    // lines under the name.
    u.fastInsert(KIO::UDSEntry::UDS_DISPLAY_TYPE, sectionKey(e.section));
    u.fastInsert(KIO::UDSEntry::UDS_USER, e.detail);
    u.fastInsert(KIO::UDSEntry::UDS_GROUP, e.detail2);
    u.fastInsert(KIO::UDSEntry::UDS_ICON_NAME, e.icon.isEmpty() ? QMimeDatabase().mimeTypeForName(e.mimeType).iconName() : e.icon);
    if (!e.overlays.isEmpty())
        u.fastInsert(KIO::UDSEntry::UDS_ICON_OVERLAY_NAMES, e.overlays.join(QLatin1Char(',')));
    u.fastInsert(KIO::UDSEntry::UDS_FILE_TYPE, e.isDir ? S_IFDIR : S_IFREG);
    // Folders take drops (into the real folder); nothing here is renamed or
    // deleted from this page (thispc.json: no moving, no deleting).
    u.fastInsert(KIO::UDSEntry::UDS_ACCESS, e.localPath.isEmpty() ? 0500 : (e.isDir ? 0700 : 0600));
    u.fastInsert(KIO::UDSEntry::UDS_MIME_TYPE, e.mimeType);
    u.fastInsert(KIO::UDSEntry::UDS_TARGET_URL, e.target.toString());
    if (!e.localPath.isEmpty())
        u.fastInsert(KIO::UDSEntry::UDS_LOCAL_PATH, e.localPath);
    if (e.size >= 0)
        u.fastInsert(KIO::UDSEntry::UDS_SIZE, e.size);
    if (e.modified.isValid())
        u.fastInsert(KIO::UDSEntry::UDS_MODIFICATION_TIME, e.modified.toSecsSinceEpoch());
    return u;
}

KIO::UDSEntry rootEntry()
{
    KIO::UDSEntry u;
    u.fastInsert(KIO::UDSEntry::UDS_NAME, QStringLiteral("."));
    u.fastInsert(KIO::UDSEntry::UDS_DISPLAY_NAME, Text::thisPc());
    u.fastInsert(KIO::UDSEntry::UDS_FILE_TYPE, S_IFDIR);
    u.fastInsert(KIO::UDSEntry::UDS_ACCESS, 0500);
    u.fastInsert(KIO::UDSEntry::UDS_MIME_TYPE, QStringLiteral("inode/directory"));
    u.fastInsert(KIO::UDSEntry::UDS_ICON_NAME, QStringLiteral("lucent-place-pc"));
    return u;
}
} // namespace

class ThisPcWorker : public KIO::WorkerBase
{
public:
    ThisPcWorker(const QByteArray &pool, const QByteArray &app)
        : WorkerBase("thispc", pool, app)
    {
    }

    KIO::WorkerResult listDir(const QUrl &url) override
    {
        const Target t = parseUrl(url);
        if (t.kind != Target::Root)
            return open(url, t);
        listEntry(rootEntry());
        for (const Entry &e : entries(/*mountForSpace=*/true))
            listEntry(toUds(e));
        return KIO::WorkerResult::pass();
    }

    KIO::WorkerResult stat(const QUrl &url) override
    {
        const Target t = parseUrl(url);
        if (t.kind == Target::Root) {
            statEntry(rootEntry());
            return KIO::WorkerResult::pass();
        }
        const QString name = url.path().section(QLatin1Char('/'), -1, -1, QString::SectionSkipEmpty);
        for (const Entry &e : entries(false)) {
            if (e.name == name) {
                statEntry(toUds(e));
                return KIO::WorkerResult::pass();
            }
        }
        return KIO::WorkerResult::fail(KIO::ERR_DOES_NOT_EXIST, url.toDisplayString());
    }

    // The status bar under This PC: the home drive, measured correctly.
    KIO::WorkerResult fileSystemFreeSpace(const QUrl &url) override
    {
        const Target t = parseUrl(url);
        QString path = homePath();
        if (t.kind == Target::Drive) {
            const Gathered g = gatherVolumes();
            for (const Volume &v : g.volumes)
                if (v.id == t.id && !v.mountPoint.isEmpty())
                    path = v.mountPoint;
        }
        const Space s = statFs(path);
        if (!s.valid)
            return KIO::WorkerResult::fail(KIO::ERR_CANNOT_STAT, url.toDisplayString());
        setMetaData(QStringLiteral("total"), QString::number(s.total));
        setMetaData(QStringLiteral("available"), QString::number(s.free));
        return KIO::WorkerResult::pass();
    }

private:
    QList<Entry> entries(bool mountForSpace)
    {
        const QString home = homePath();
        const QStringList os = osDevices();
        Gathered g = gatherVolumes();
        QList<Drive> drives = selectDrives(g.volumes, home, os, statFs);

        // Windows shows every drive's free space. Open the ones polkit lets
        // this user open silently: USB drives as they are plugged in (Eject
        // takes them away again), read-only Windows partitions once per
        // session (unmounted by the user, they stay unmounted).
        if (mountForSpace) {
            QHash<QString, QString> mounted; // id -> mount point
            const QStringList done = automounted();
            for (const Drive &d : std::as_const(drives)) {
                if (!d.mountPoint.isEmpty() || (d.kind != DriveKind::Windows && d.kind != DriveKind::Removable) || !g.udiById.contains(d.id))
                    continue;
                if (d.kind == DriveKind::Windows) {
                    const QString uuid = g.uuidById.value(d.id);
                    if (uuid.isEmpty() || done.contains(uuid))
                        continue;
                    rememberAutomounted(uuid);
                }
                const QString mp = mount(g.udiById.value(d.id), false, nullptr);
                if (!mp.isEmpty())
                    mounted.insert(d.id, mp);
            }
            if (!mounted.isEmpty()) {
                // udisks' answer, in case udev hasn't caught up yet
                for (Volume &v : g.volumes)
                    if (v.mountPoint.isEmpty() && mounted.contains(v.id))
                        v.mountPoint = mounted.value(v.id);
                drives = selectDrives(g.volumes, home, os, statFs);
            }
        }

        const auto xdg = [](const QString &id) {
            static const QHash<QString, QStandardPaths::StandardLocation> loc{
                {QStringLiteral("Desktop"), QStandardPaths::DesktopLocation},
                {QStringLiteral("Documents"), QStandardPaths::DocumentsLocation},
                {QStringLiteral("Downloads"), QStandardPaths::DownloadLocation},
                {QStringLiteral("Pictures"), QStandardPaths::PicturesLocation},
                {QStringLiteral("Music"), QStandardPaths::MusicLocation},
                {QStringLiteral("Videos"), QStandardPaths::MoviesLocation},
            };
            return canonical(QStandardPaths::writableLocation(loc.value(id)));
        };
        const QList<Folder> folders = userFolders(xdg, home, [](const QString &p) {
            return QFileInfo(p).isDir();
        });
        const QList<RecentFile> recent = pickRecent(KRecentDocument::recentUrls(), RecentMax, home, [](const QString &path) {
            const QFileInfo info(path);
            FileFacts f;
            f.exists = info.exists();
            f.isFile = info.isFile();
            f.size = info.size();
            f.modified = info.lastModified();
            return f;
        });
        return buildEntries(folders, drives, recent, home, formatters());
    }

    // thispc:/<item> opened directly: go where the item lives, mounting a
    // drive first if needed (polkit may ask for a password here).
    KIO::WorkerResult open(const QUrl &url, const Target &t)
    {
        if (t.kind == Target::Drive) {
            const Gathered g = gatherVolumes();
            for (const Volume &v : g.volumes) {
                if (v.id != t.id)
                    continue;
                QString mp = v.mountPoint;
                if (mp.isEmpty()) {
                    QString error;
                    mp = mount(g.udiById.value(v.id), true, &error);
                    if (mp.isEmpty())
                        return KIO::WorkerResult::fail(KIO::ERR_CANNOT_MOUNT, error);
                }
                redirection(QUrl::fromLocalFile(mp));
                return KIO::WorkerResult::pass();
            }
            if (t.id == QLatin1String("home")) {
                redirection(QUrl::fromLocalFile(homePath()));
                return KIO::WorkerResult::pass();
            }
        }
        for (const Entry &e : entries(false)) {
            if (QStringLiteral("thispc:/") + e.name == url.adjusted(QUrl::StripTrailingSlash).toString() && e.isDir && e.target.isLocalFile()) {
                redirection(e.target);
                return KIO::WorkerResult::pass();
            }
        }
        return KIO::WorkerResult::fail(KIO::ERR_DOES_NOT_EXIST, url.toDisplayString());
    }
};

extern "C" Q_DECL_EXPORT int kdemain(int argc, char **argv)
{
    QCoreApplication app(argc, argv);
    app.setApplicationName(QStringLiteral("kio_thispc"));
    KLocalizedString::setApplicationDomain("lucent-thispc");
    if (argc != 4) {
        fprintf(stderr, "Usage: kio_thispc protocol domain-socket1 domain-socket2\n");
        return -1;
    }
    ThisPcWorker worker(argv[2], argv[3]);
    worker.dispatchLoop();
    return 0;
}

#include "worker.moc"
