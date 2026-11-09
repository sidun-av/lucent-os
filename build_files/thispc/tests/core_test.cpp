/*
 * Tests for the This PC logic (core/): enumeration, naming, sizes.
 * Runs on any Qt 6 (no KDE needed); the image build runs it too.
 *
 * SPDX-License-Identifier: Apache-2.0
 */
#include "../core/thispc_core.h"

#include <QCollator>
#include <QTest>

using namespace ThisPc;

namespace
{
constexpr quint64 GB = 1000ull * 1000 * 1000;
constexpr quint64 GiB = 1024ull * 1024 * 1024;

// /proc/self/mountinfo of the Lucent test VM (bootc qcow2, btrfs): the home
// directory lives on /var, a bind mount of a btrfs subvolume, and / is the
// read-only composefs overlay that reports 0 bytes free.
const char *VM_MOUNTINFO = R"(51 1 0:42 / / ro,relatime shared:1 - overlay composefs ro,seclabel,lowerdir+=/run/ostree/.private/cfsroot-lower,datadir+=/sysroot/ostree/repo/objects,redirect_dir=on,metacopy=on
48 51 0:37 /root/ostree/deploy/default/deploy/47128c.0/etc /etc rw,relatime shared:2 - btrfs /dev/vda3 rw,seclabel,discard=async,space_cache=v2,subvolid=256,subvol=/root
52 51 0:37 /root /sysroot ro,relatime shared:3 - btrfs /dev/vda3 rw,seclabel,discard=async,space_cache=v2,subvolid=256,subvol=/root
53 52 0:37 /root/ostree/deploy/default/var /sysroot/ostree/deploy/default/var rw,relatime shared:4 - btrfs /dev/vda3 rw,seclabel
41 51 0:7 / /dev rw,nosuid shared:5 - devtmpfs devtmpfs rw,seclabel,size=2847136k,nr_inodes=711784,mode=755,inode64
62 51 0:30 / /run rw,nosuid,nodev shared:17 - tmpfs tmpfs rw,seclabel,size=1206216k,nr_inodes=819200,mode=755,inode64
64 51 0:37 /root/ostree/deploy/default/var /var rw,relatime shared:161 master:4 - btrfs /dev/vda3 rw,seclabel,discard=async,space_cache=v2,subvolid=256,subvol=/root
73 51 0:45 / /tmp rw,nosuid,nodev shared:162 - tmpfs tmpfs rw,seclabel,nr_inodes=1048576,inode64,usrquota
79 51 253:2 / /boot ro,relatime shared:208 - ext4 /dev/vda2 rw,seclabel
85 79 253:1 / /boot/efi rw,relatime shared:214 - vfat /dev/vda1 rw,fmask=0077,dmask=0077,codepage=437,iocharset=ascii,shortname=winnt,errors=remount-ro
90 62 0:85 / /run/media/anna/KINGSTON rw,nosuid,nodev,relatime shared:300 - vfat /dev/sdb1 rw,uid=1000
91 51 253:5 / /var/home rw,relatime shared:301 - btrfs /dev/mapper/luks-1234 rw,subvol=/home
)";

QString same(const QString &path)
{
    return path;
}

Volume vol(const QString &id, const QString &fs, quint64 size, const QString &label = {}, const QString &mount = {}, bool removable = false)
{
    Volume v;
    v.id = id;
    v.device = QStringLiteral("/dev/") + id;
    v.fsType = fs;
    v.size = size;
    v.label = label;
    v.mountPoint = mount;
    v.removable = removable;
    return v;
}

Space space(quint64 total, quint64 free, bool ro = false)
{
    Space s;
    s.total = total;
    s.free = free;
    s.readOnly = ro;
    s.valid = true;
    return s;
}

// statvfs as on the VM: "/" is composefs (full, read-only), the home volume
// has room, mounted drives answer for themselves.
Space fakeStatFs(const QString &path)
{
    if (path == QLatin1String("/"))
        return space(49483776, 0, true);
    if (path.startsWith(QLatin1String("/var/home/anna")))
        return space(512 * GB, 410 * GB);
    if (path == QLatin1String("/run/media/anna/C"))
        return space(476 * GB, 121 * GB, true);
    if (path == QLatin1String("/run/media/anna/KINGSTON"))
        return space(32 * GB, 14200 * 1000ull * 1000);
    return {};
}

const QString HOME = QStringLiteral("/var/home/anna");

Formatters fmt()
{
    Formatters f;
    f.bytes = [](quint64 b) {
        return QString::number(double(b) / GB, 'f', b % GB ? 1 : 0) + QStringLiteral(" GB");
    };
    f.date = [](const QDateTime &) {
        return QStringLiteral("Today");
    };
    f.itemCount = [](const QString &path) {
        return path.endsWith(QLatin1String("Documents")) ? 212 : 0;
    };
    f.mimeType = [](const QString &path) {
        return path.endsWith(QLatin1String(".docx")) ? QStringLiteral("application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                                                     : QStringLiteral("application/octet-stream");
    };
    return f;
}

const Entry *find(const QList<Entry> &entries, const QString &name)
{
    for (const Entry &e : entries)
        if (e.name == name)
            return &e;
    return nullptr;
}
} // namespace

class CoreTest : public QObject
{
    Q_OBJECT
private Q_SLOTS:

    // ---- sections: Dolphin sorts groups by the text, ascending

    void sectionsSortInPageOrder()
    {
        QCollator collator; // as Dolphin's KFileItemModel sets it up
        collator.setNumericMode(true);
        collator.setCaseSensitivity(Qt::CaseInsensitive);
        const QString folders = sectionKey(Section::Folders);
        const QString drives = sectionKey(Section::Drives);
        const QString recent = sectionKey(Section::Recent);
        QVERIFY2(collator.compare(folders, drives) < 0, qPrintable(folders + QStringLiteral(" !< ") + drives));
        QVERIFY(collator.compare(drives, recent) < 0);
        QVERIFY(collator.compare(folders, recent) < 0);
    }

    void sectionKeyShowsTheLabel()
    {
        QCOMPARE(sectionKey(Section::Folders).trimmed(), QStringLiteral("Folders"));
        QCOMPARE(sectionKey(Section::Drives).trimmed(), QStringLiteral("Drives and devices"));
        QCOMPARE(sectionKey(Section::Recent).trimmed(), QStringLiteral("Recent files"));
        // nothing but hair spaces in front
        for (Section s : {Section::Folders, Section::Drives, Section::Recent}) {
            const QString key = sectionKey(s);
            const QString label = Text::section(s);
            QVERIFY(key.endsWith(label));
            for (QChar c : key.left(key.size() - label.size()))
                QCOMPARE(c, QChar(0x200A));
        }
    }

    // ---- space

    void spaceFromStatvfsMultipliesByFragmentSize()
    {
        const Space s = spaceFromStatvfs(4096, 1000, 250, false);
        QCOMPARE(s.total, quint64(4096000));
        QCOMPARE(s.free, quint64(1024000));
        QVERIFY(s.valid);
        QVERIFY(!s.readOnly);
    }

    void usedPercentAndGauge()
    {
        QCOMPARE(usedPercent(space(512 * GB, 410 * GB)), 20);
        QCOMPARE(usedPercent(space(476 * GB, 121 * GB)), 75);
        QCOMPARE(usedPercent(space(100, 0)), 100);
        QCOMPARE(usedPercent(Space{}), 0);
        QCOMPARE(gaugeStep(space(512 * GB, 410 * GB)), 20);
        QCOMPARE(gaugeStep(space(100, 44)), 55); // 56 % used
        QCOMPARE(gaugeStep(space(100, 98)), 0); // 2 %
        QCOMPARE(gaugeStep(space(100, 97)), 5); // 3 % rounds up to 5
        QCOMPARE(gaugeStep(space(100, 1)), 100); // 99 %
    }

    // ---- what belongs to the OS

    void systemDevicesFromMountInfo()
    {
        const QStringList devs = systemDevices(QString::fromLatin1(VM_MOUNTINFO), [](const QString &p) {
            return p == QLatin1String("/dev/mapper/luks-1234") ? QStringLiteral("/dev/dm-0") : p;
        });
        QVERIFY(devs.contains(QStringLiteral("/dev/vda3"))); // /, /etc, /var, /sysroot
        QVERIFY(devs.contains(QStringLiteral("/dev/vda2"))); // /boot
        QVERIFY(devs.contains(QStringLiteral("/dev/vda1"))); // /boot/efi
        QVERIFY(devs.contains(QStringLiteral("/dev/dm-0"))); // /var/home on LUKS
        QVERIFY(!devs.contains(QStringLiteral("/dev/sdb1"))); // a USB stick is the user's
        QVERIFY(!devs.contains(QStringLiteral("composefs")));
        QVERIFY(!devs.contains(QStringLiteral("tmpfs")));
        QCOMPARE(devs.count(QStringLiteral("/dev/vda3")), 1);
    }

    void swapDevicesFromProcSwaps()
    {
        const QString swaps = QStringLiteral(
            "Filename\t\t\t\tType\t\tSize\t\tUsed\t\tPriority\n"
            "/dev/zram0                              partition\t6029308\t\t0\t\t100\n"
            "/dev/sda3                               partition\t8388604\t\t0\t\t-2\n");
        QCOMPARE(swapDevices(swaps), (QStringList{QStringLiteral("/dev/zram0"), QStringLiteral("/dev/sda3")}));
    }

    // ---- drives

    void homeDriveMeasuresTheHomeFolderNotTheImageRoot()
    {
        // The status-bar bug: Solid matched /var/home to the composefs "/"
        // and Dolphin showed "0 B free". This PC measures the home folder.
        const QList<Drive> drives = selectDrives({}, HOME, {}, fakeStatFs);
        QCOMPARE(drives.size(), 1);
        const Drive &home = drives.first();
        QCOMPARE(home.kind, DriveKind::System);
        QCOMPARE(home.id, QStringLiteral("home"));
        QCOMPARE(home.name, QStringLiteral("Home"));
        QCOMPARE(home.mountPoint, HOME);
        QCOMPARE(home.total, 512 * GB);
        QVERIFY(home.free.has_value());
        QCOMPARE(*home.free, 410 * GB);
        QVERIFY(!home.readOnly);
        QVERIFY(!home.ejectable);
    }

    void osVolumesAreNotListedTwice()
    {
        const QList<Volume> vols{
            vol(QStringLiteral("vda1"), QStringLiteral("vfat"), 501 * 1024 * 1024ull, QStringLiteral("EFI-SYSTEM"), QStringLiteral("/boot/efi")),
            vol(QStringLiteral("vda2"), QStringLiteral("ext4"), 1 * GiB, QStringLiteral("boot"), QStringLiteral("/boot")),
            vol(QStringLiteral("vda3"), QStringLiteral("btrfs"), 40 * GiB, QStringLiteral("root"), QStringLiteral("/etc")),
            vol(QStringLiteral("zram0"), QStringLiteral("swap"), 6 * GiB),
        };
        const QStringList sys{QStringLiteral("/dev/vda1"), QStringLiteral("/dev/vda2"), QStringLiteral("/dev/vda3"), QStringLiteral("/dev/zram0")};
        const QList<Drive> drives = selectDrives(vols, HOME, sys, fakeStatFs);
        QCOMPARE(drives.size(), 1);
        QCOMPARE(drives.first().kind, DriveKind::System);
    }

    void windowsPartitionKeepsItsLetterNameAndIsReadOnly()
    {
        // lucent-drive-letters already named it through udev (label).
        Volume c = vol(QStringLiteral("vdb1"), QStringLiteral("ntfs"), 476 * GB, QStringLiteral("Local Disk (C:)"));
        QList<Drive> drives = selectDrives({c}, HOME, {}, fakeStatFs);
        QCOMPARE(drives.size(), 2);
        const Drive &win = drives.at(1);
        QCOMPARE(win.kind, DriveKind::Windows);
        QCOMPARE(win.name, QStringLiteral("Local Disk (C:)"));
        QCOMPARE(win.id, QStringLiteral("vdb1"));
        QVERIFY(win.readOnly); // udev makes udisks mount internal NTFS read-only
        QVERIFY(!win.ejectable);
        QVERIFY(win.mountPoint.isEmpty());
        QCOMPARE(win.total, 476 * GB);
        QVERIFY(!win.free.has_value()); // not opened yet

        c.mountPoint = QStringLiteral("/run/media/anna/C");
        drives = selectDrives({c}, HOME, {}, fakeStatFs);
        QCOMPARE(drives.at(1).mountPoint, QStringLiteral("/run/media/anna/C"));
        QCOMPARE(*drives.at(1).free, 121 * GB);
        QVERIFY(drives.at(1).readOnly);
    }

    void unlabeledWindowsPartitionIsALocalDisk()
    {
        const QList<Drive> drives = selectDrives({vol(QStringLiteral("sda4"), QStringLiteral("ntfs"), 200 * GB)}, HOME, {}, fakeStatFs);
        QCOMPARE(drives.at(1).name, QStringLiteral("Local Disk"));
    }

    void usbDriveIsEjectableAndWritable()
    {
        const Volume usb = vol(QStringLiteral("sdb1"), QStringLiteral("vfat"), 32 * GB, QStringLiteral("KINGSTON"), QStringLiteral("/run/media/anna/KINGSTON"), true);
        const QList<Drive> drives = selectDrives({usb}, HOME, {}, fakeStatFs);
        const Drive &d = drives.at(1);
        QCOMPARE(d.kind, DriveKind::Removable);
        QCOMPARE(d.name, QStringLiteral("KINGSTON"));
        QVERIFY(d.ejectable);
        QVERIFY(!d.readOnly);
        QCOMPARE(*d.free, 14200 * 1000ull * 1000);
    }

    void usbNtfsIsNotForcedReadOnly()
    {
        const Volume usb = vol(QStringLiteral("sdc1"), QStringLiteral("ntfs"), 1000 * GB, {}, {}, true);
        const Drive d = selectDrives({usb}, HOME, {}, fakeStatFs).at(1);
        QCOMPARE(d.kind, DriveKind::Removable);
        QVERIFY(!d.readOnly);
        QCOMPARE(d.name, QStringLiteral("USB drive"));
    }

    void hiddenAndTinyVolumesAreSkipped()
    {
        Volume recovery = vol(QStringLiteral("sda5"), QStringLiteral("ntfs"), 900 * 1024 * 1024ull, QStringLiteral("Recovery"));
        Volume ignored = vol(QStringLiteral("sda1"), QStringLiteral("vfat"), 100 * GB);
        ignored.ignored = true;
        Volume locked = vol(QStringLiteral("sda6"), QStringLiteral("crypto_LUKS"), 100 * GB);
        locked.fileSystem = false;
        Volume tinyUsb = vol(QStringLiteral("sdd1"), QStringLiteral("vfat"), 64 * 1024 * 1024ull, QStringLiteral("TINY"), {}, true);
        const QList<Drive> drives = selectDrives({recovery, ignored, locked, tinyUsb}, HOME, {}, fakeStatFs);
        QCOMPARE(drives.size(), 2);
        QCOMPARE(drives.at(1).name, QStringLiteral("TINY")); // small USB sticks stay
    }

    void drivesInWindowsOrder()
    {
        const QList<Volume> vols{
            vol(QStringLiteral("sdb1"), QStringLiteral("vfat"), 32 * GB, QStringLiteral("KINGSTON"), {}, true),
            vol(QStringLiteral("sda5"), QStringLiteral("ext4"), 100 * GB, QStringLiteral("Data")),
            vol(QStringLiteral("sda4"), QStringLiteral("ntfs"), 300 * GB, QStringLiteral("Data (D:)")),
            vol(QStringLiteral("sda3"), QStringLiteral("ntfs"), 476 * GB, QStringLiteral("Local Disk (C:)")),
        };
        const QList<Drive> drives = selectDrives(vols, HOME, {}, fakeStatFs);
        QStringList names;
        for (const Drive &d : drives)
            names << d.name;
        QCOMPARE(names, (QStringList{QStringLiteral("Home"), QStringLiteral("Local Disk (C:)"), QStringLiteral("Data (D:)"), QStringLiteral("Data"), QStringLiteral("KINGSTON")}));
        QCOMPARE(drives.at(3).kind, DriveKind::Other);
    }

    void driveIcons()
    {
        const QList<Drive> drives = selectDrives({vol(QStringLiteral("sdb1"), QStringLiteral("vfat"), 32 * GB, QStringLiteral("K"), QStringLiteral("/run/media/anna/KINGSTON"), true),
                                                  vol(QStringLiteral("vdb1"), QStringLiteral("ntfs"), 476 * GB, QStringLiteral("Local Disk (C:)"))},
                                                 HOME,
                                                 {},
                                                 fakeStatFs);
        QCOMPARE(driveIcon(drives.at(0)), QStringLiteral("lucent-drive-system-20"));
        QCOMPARE(driveIcon(drives.at(1)), QStringLiteral("lucent-drive-windows")); // unknown usage
        QCOMPARE(driveIcon(drives.at(2)), QStringLiteral("lucent-drive-usb-55"));
    }

    // ---- user folders

    void userFoldersInPageOrderWithLocalisedPaths()
    {
        const auto xdg = [](const QString &id) -> QString {
            if (id == QLatin1String("Documents"))
                return QStringLiteral("/var/home/anna/Документы");
            if (id == QLatin1String("Music"))
                return HOME; // XDG_MUSIC_DIR=$HOME: disabled
            if (id == QLatin1String("Videos"))
                return QStringLiteral("/var/home/anna/Videos"); // missing on disk
            return HOME + QLatin1Char('/') + id;
        };
        const auto isDir = [](const QString &p) {
            return !p.endsWith(QLatin1String("Videos"));
        };
        const QList<Folder> folders = userFolders(xdg, HOME, isDir);
        QStringList ids, paths, icons;
        for (const Folder &f : folders) {
            ids << f.id;
            paths << f.path;
            icons << f.icon;
        }
        QCOMPARE(ids, (QStringList{QStringLiteral("Desktop"), QStringLiteral("Documents"), QStringLiteral("Downloads"), QStringLiteral("Pictures")}));
        QCOMPARE(paths.at(1), QStringLiteral("/var/home/anna/Документы"));
        QCOMPARE(icons,
                 (QStringList{QStringLiteral("user-desktop"), QStringLiteral("folder-documents"), QStringLiteral("folder-download"), QStringLiteral("folder-pictures")}));
    }

    // ---- recent files

    void recentNewestFirstOnlyExistingLocalFiles()
    {
        const QDateTime t = QDateTime::fromSecsSinceEpoch(1762600000);
        const QList<QUrl> oldestFirst{
            QUrl::fromLocalFile(HOME + QStringLiteral("/Documents/old.odt")),
            QUrl(QStringLiteral("https://example.org/page")),
            QUrl::fromLocalFile(HOME + QStringLiteral("/Documents")), // a folder
            QUrl::fromLocalFile(HOME + QStringLiteral("/Downloads/gone.pdf")), // deleted since
            QUrl::fromLocalFile(HOME + QStringLiteral("/.config/kate/katerc")), // hidden
            QUrl::fromLocalFile(HOME + QStringLiteral("/.local/share/Trash/files/x.txt")),
            QUrl::fromLocalFile(HOME + QStringLiteral("/Pictures/lake.jpg")),
            QUrl::fromLocalFile(HOME + QStringLiteral("/Documents/old.odt")), // used again
            QUrl::fromLocalFile(HOME + QStringLiteral("/Documents/Lease 2026.docx")),
        };
        const auto stat = [&](const QString &path) {
            FileFacts f;
            if (path.endsWith(QLatin1String("gone.pdf")))
                return f;
            f.exists = true;
            f.isFile = !path.endsWith(QLatin1String("/Documents"));
            f.size = 48000;
            f.modified = t;
            return f;
        };
        QList<RecentFile> recent = pickRecent(oldestFirst, 10, HOME, stat);
        QStringList paths;
        for (const RecentFile &r : recent)
            paths << r.path.mid(HOME.size() + 1);
        QCOMPARE(paths, (QStringList{QStringLiteral("Documents/Lease 2026.docx"), QStringLiteral("Documents/old.odt"), QStringLiteral("Pictures/lake.jpg")}));
        QCOMPARE(recent.first().size, qint64(48000));
        QCOMPARE(recent.first().modified, t);

        recent = pickRecent(oldestFirst, 2, HOME, stat);
        QCOMPARE(recent.size(), 2);
    }

    // ---- entries (what Dolphin gets)

    void entriesForAFullPage()
    {
        const QList<Folder> folders{{QStringLiteral("Documents"), HOME + QStringLiteral("/Documents"), QStringLiteral("folder-documents")}};
        Volume c = vol(QStringLiteral("vdb1"), QStringLiteral("ntfs"), 476 * GB, QStringLiteral("Local Disk (C:)"));
        Volume usb = vol(QStringLiteral("sdb1"), QStringLiteral("vfat"), 32 * GB, QStringLiteral("KINGSTON"), QStringLiteral("/run/media/anna/KINGSTON"), true);
        const QList<Drive> drives = selectDrives({c, usb}, HOME, {}, fakeStatFs);
        RecentFile lease{HOME + QStringLiteral("/Documents/Lease 2026.docx"), 48000, QDateTime::fromSecsSinceEpoch(1762600000)};
        RecentFile top{HOME + QStringLiteral("/notes.txt"), 10, QDateTime::fromSecsSinceEpoch(1762600000)};
        const QList<Entry> entries = buildEntries(folders, drives, {lease, top}, HOME, fmt());
        QCOMPARE(entries.size(), 6);

        QSet<QString> names;
        for (const Entry &e : entries)
            names.insert(e.name);
        QCOMPARE(names.size(), entries.size()); // unique

        const Entry *docs = find(entries, QStringLiteral("folder-Documents"));
        QVERIFY(docs);
        QCOMPARE(docs->section, Section::Folders);
        QCOMPARE(docs->displayName, QStringLiteral("Documents"));
        QCOMPARE(docs->detail, QStringLiteral("212 items"));
        QCOMPARE(docs->icon, QStringLiteral("folder-documents"));
        QVERIFY(docs->isDir);
        QCOMPARE(docs->target, QUrl::fromLocalFile(HOME + QStringLiteral("/Documents")));
        QCOMPARE(docs->localPath, HOME + QStringLiteral("/Documents"));
        QCOMPARE(docs->mimeType, QStringLiteral("inode/directory"));

        const Entry *home = find(entries, QStringLiteral("drive-home"));
        QVERIFY(home);
        QCOMPARE(home->section, Section::Drives);
        QCOMPARE(home->displayName, QStringLiteral("Home"));
        QCOMPARE(home->detail, QStringLiteral("410 GB free of 512 GB"));
        QCOMPARE(home->target, QUrl::fromLocalFile(HOME));
        QVERIFY(home->localPath.isEmpty()); // no folder preview over the ring icon
        QCOMPARE(home->icon, QStringLiteral("lucent-drive-system-20"));

        const Entry *win = find(entries, QStringLiteral("drive-vdb1"));
        QVERIFY(win);
        QCOMPARE(win->displayName, QStringLiteral("Local Disk (C:)"));
        QCOMPARE(win->detail, QStringLiteral("Read-only · 476 GB"));
        QCOMPARE(win->target, QUrl(QStringLiteral("thispc:/drive-vdb1"))); // mounts on open
        QVERIFY(win->overlays.contains(QStringLiteral("emblem-locked")));
        QCOMPARE(win->mimeType, QStringLiteral("inode/directory"));

        const Entry *stick = find(entries, QStringLiteral("drive-sdb1"));
        QVERIFY(stick);
        QCOMPARE(stick->detail, QStringLiteral("14.2 GB free of 32 GB"));
        QCOMPARE(stick->target, QUrl::fromLocalFile(QStringLiteral("/run/media/anna/KINGSTON")));
        QCOMPARE(stick->mimeType, QStringLiteral("inode/x-lucent-removable-drive")); // gets "Eject"
        QVERIFY(stick->overlays.isEmpty());

        const Entry *doc = nullptr;
        const Entry *notes = nullptr;
        for (const Entry &e : entries) {
            if (e.section == Section::Recent && e.displayName.endsWith(QLatin1String(".docx")))
                doc = &e;
            if (e.section == Section::Recent && e.displayName == QLatin1String("notes.txt"))
                notes = &e;
        }
        QVERIFY(doc && notes);
        QVERIFY(doc->name.startsWith(QLatin1String("recent-")));
        QCOMPARE(doc->displayName, QStringLiteral("Lease 2026.docx"));
        QCOMPARE(doc->detail, QStringLiteral("Documents · Today"));
        QVERIFY(!doc->isDir);
        QCOMPARE(doc->size, qint64(48000));
        QCOMPARE(doc->target, QUrl::fromLocalFile(lease.path));
        QCOMPARE(doc->localPath, lease.path);
        QVERIFY(doc->mimeType.contains(QLatin1String("wordprocessingml")));
        QCOMPARE(notes->detail, QStringLiteral("Home · Today"));
    }

    void mountedWindowsDriveShowsFreeSpace()
    {
        Volume c = vol(QStringLiteral("vdb1"), QStringLiteral("ntfs"), 476 * GB, QStringLiteral("Local Disk (C:)"), QStringLiteral("/run/media/anna/C"));
        const QList<Entry> entries = buildEntries({}, selectDrives({c}, HOME, {}, fakeStatFs), {}, HOME, fmt());
        const Entry *win = find(entries, QStringLiteral("drive-vdb1"));
        QCOMPARE(win->detail, QStringLiteral("Read-only · 121 GB free of 476 GB"));
        QCOMPARE(win->target, QUrl::fromLocalFile(QStringLiteral("/run/media/anna/C")));
        QCOMPARE(win->icon, QStringLiteral("lucent-drive-windows-75"));
    }

    void unmountedUsbSaysWhatItIs()
    {
        Volume usb = vol(QStringLiteral("sdb1"), QStringLiteral("exfat"), 32 * GB, QStringLiteral("KINGSTON"), {}, true);
        const QList<Entry> entries = buildEntries({}, selectDrives({usb}, HOME, {}, fakeStatFs), {}, HOME, fmt());
        QCOMPARE(find(entries, QStringLiteral("drive-sdb1"))->detail, QStringLiteral("USB drive · 32 GB"));
    }

    void recentNamesAreStable()
    {
        const RecentFile r{HOME + QStringLiteral("/a.txt"), 1, QDateTime::fromSecsSinceEpoch(1)};
        const QString a = buildEntries({}, {}, {r}, HOME, fmt()).first().name;
        const QString b = buildEntries({}, {}, {r}, HOME, fmt()).first().name;
        QCOMPARE(a, b);
        QCOMPARE(parseUrl(QUrl(QStringLiteral("thispc:/") + a)).kind, Target::Recent);
        QCOMPARE(parseUrl(QUrl(QStringLiteral("thispc:/") + a)).id, a.mid(7));
    }

    // ---- URLs

    void parseUrls()
    {
        QCOMPARE(parseUrl(QUrl(QStringLiteral("thispc:/"))).kind, Target::Root);
        QCOMPARE(parseUrl(QUrl(QStringLiteral("thispc:"))).kind, Target::Root);
        QCOMPARE(parseUrl(QUrl(QStringLiteral("thispc:///"))).kind, Target::Root);
        const Target f = parseUrl(QUrl(QStringLiteral("thispc:/folder-Documents")));
        QCOMPARE(f.kind, Target::Folder);
        QCOMPARE(f.id, QStringLiteral("Documents"));
        const Target d = parseUrl(QUrl(QStringLiteral("thispc:/drive-sdb1/")));
        QCOMPARE(d.kind, Target::Drive);
        QCOMPARE(d.id, QStringLiteral("sdb1"));
        QCOMPARE(parseUrl(QUrl(QStringLiteral("thispc:/drive-sdb1/sub"))).kind, Target::Unknown);
        QCOMPARE(parseUrl(QUrl(QStringLiteral("thispc:/whatever"))).kind, Target::Unknown);
        QCOMPARE(parseUrl(QUrl(QStringLiteral("file:///"))).kind, Target::Unknown);
    }
};

QTEST_GUILESS_MAIN(CoreTest)
#include "core_test.moc"
