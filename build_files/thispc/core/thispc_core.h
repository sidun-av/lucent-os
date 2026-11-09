/*
 * Lucent "This PC": what the page lists and how it names it, without KIO.
 *
 * Everything here is plain Qt Core so it can be unit-tested anywhere
 * (tests/core_test.cpp); the KIO worker (worker.cpp) only gathers the facts
 * (Solid volumes, statvfs, KRecentDocument) and turns the result into
 * UDSEntries. See docs/this-pc.md.
 *
 * SPDX-License-Identifier: Apache-2.0
 */
#pragma once

#include <QDateTime>
#include <QList>
#include <QString>
#include <QStringList>
#include <QUrl>

#include <functional>
#include <optional>

namespace ThisPc
{

// ---------------------------------------------------------------- sections

enum class Section { Folders, Drives, Recent };

// Dolphin groups the page by the items' "Type" (UDS_DISPLAY_TYPE): folders
// (user folders and drives) before files, then groups by their text,
// ascending, with ICU collation that ignores spaces and punctuation, so no
// invisible prefix can change the order. In English and Russian that gives
// Drives and devices, Folders, Recent files (tests/core_test.cpp).
QString sectionKey(Section section);

// ------------------------------------------------------------ space

struct Space {
    quint64 total = 0;
    quint64 free = 0; // available to the user (f_bavail)
    bool readOnly = false;
    bool valid = false;
};

// statvfs numbers -> Space (f_frsize * f_blocks, f_frsize * f_bavail).
Space spaceFromStatvfs(quint64 frsize, quint64 blocks, quint64 bavail, bool readOnly);

// Used share in whole percent, 0..100 (0 when unknown).
int usedPercent(const Space &space);

// Usage rounded to the nearest 5 % for the ring icon (0, 5, ... 100).
int gaugeStep(const Space &space);

// Decimals for a size in its unit (1024-based): 1 below 10 units ("4.0 GiB"),
// else 0 ("21 GiB", "476 GiB"), so a drive's line fits under its icon.
int bytePrecision(quint64 bytes);

// --------------------------------------------------------------- drives

// One file system as Solid/UDisks describe it.
struct Volume {
    QString id; // udisks block name: "sdb1", "dm-2"
    QString device; // "/dev/sdb1"
    QString label; // after lucent-drive-letters: "Local Disk (C:)"
    QString fsType; // "ntfs", "vfat", "btrfs", ...
    quint64 size = 0; // bytes
    QString mountPoint; // empty when not mounted
    bool removable = false; // USB stick, SD card, external disk
    bool ignored = false; // recovery, EFI, MS reserved: never a user's drive
    bool fileSystem = true; // has a file system (not swap, raid, a locked container)
    QString uuid;
};

// Every block device from `lsblk -J -b -o KNAME,PATH,TYPE,FSTYPE,LABEL,UUID,
// SIZE,RM,HOTPLUG,TRAN,PARTTYPE,MOUNTPOINTS` (flat or tree). The label is
// udev's, so lucent-drive-letters' "Local Disk (C:)" is there.
QList<Volume> parseLsblk(const QByteArray &json);
inline const char *LsblkColumns = "KNAME,PATH,TYPE,FSTYPE,LABEL,UUID,SIZE,RM,HOTPLUG,TRAN,PARTTYPE,MOUNTPOINTS";

// udisks' D-Bus object for a kernel device name ("dm-3" -> .../dm_2d3).
QString udisksPath(const QString &kname);

enum class DriveKind { System, Windows, Removable, Other };

struct Drive {
    QString id; // "home" or the volume id
    DriveKind kind = DriveKind::Other;
    QString name;
    QString device;
    QString mountPoint; // where it opens; empty = not mounted yet
    bool readOnly = false;
    bool ejectable = false;
    quint64 total = 0;
    std::optional<quint64> free; // unknown until mounted
    Space space;
};

// Mount sources of the OS itself (/, /sysroot, /etc, /var, /boot, /boot/efi,
// /usr) from /proc/self/mountinfo text, canonical device paths; these never
// appear as drives of their own.
QStringList systemDevices(const QString &mountInfo, const std::function<QString(const QString &)> &canonical);

// Swap devices from /proc/swaps text.
QStringList swapDevices(const QString &procSwaps);

using StatFs = std::function<Space(const QString &path)>;

// The drives "This PC" shows: the system drive (as "Home", measured at the
// user's home directory, never at the read-only composefs root), then
// Windows partitions, other internal file systems and removable drives.
QList<Drive> selectDrives(const QList<Volume> &volumes, const QString &home, const QStringList &systemDevices, const StatFs &statFs);

// Ring icon for a drive: lucent-drive-<kind>[-<step>].
QString driveIcon(const Drive &drive);

// ---------------------------------------------------------- user folders

struct Folder {
    QString id; // "Documents" (stable, English)
    QString path;
    QString icon;
};

// Desktop, Documents, Downloads, Pictures, Music, Videos as the XDG user
// dirs say (localised names), skipping ones that are missing or are just
// the home folder itself.
QList<Folder> userFolders(const std::function<QString(const QString &id)> &xdgDir, const QString &home, const std::function<bool(const QString &)> &isDir);

// -------------------------------------------------------------- recent

struct FileFacts {
    bool exists = false;
    bool isFile = false;
    qint64 size = -1;
    QDateTime modified;
};

struct RecentFile {
    QString path;
    qint64 size = -1;
    QDateTime modified;
};

// KRecentDocument::recentUrls() lists the oldest first. Returns the newest
// `max` local files that still exist, skipping folders, the trash and
// hidden (dot) paths.
QList<RecentFile> pickRecent(const QList<QUrl> &oldestFirst, int max, const QString &home, const std::function<FileFacts(const QString &)> &stat);

// --------------------------------------------------------------- entries

struct Entry {
    QString name; // unique within thispc:/ (UDS_NAME)
    QString displayName;
    Section section = Section::Folders;
    QString detail; // the grey lines under the name: "21 GiB free"
    QString detail2; // "of 40 GiB" (Dolphin roles "owner", "group")
    QString icon;
    QStringList overlays;
    bool isDir = true;
    QUrl target; // where activating it goes (UDS_TARGET_URL)
    QString localPath; // UDS_LOCAL_PATH (folders and files; not drives)
    QString mimeType;
    qint64 size = -1;
    QDateTime modified;
};

struct Formatters {
    std::function<QString(quint64)> bytes; // "410 GB"
    std::function<QString(const QDateTime &)> date; // "Today", "Nov 6"
    std::function<int(const QString &)> itemCount; // entries in a folder
    std::function<QString(const QString &)> mimeType; // by file name
};

QList<Entry> buildEntries(const QList<Folder> &folders, const QList<Drive> &drives, const QList<RecentFile> &recent, const QString &home, const Formatters &fmt);

// thispc:/<name> -> what it is
struct Target {
    enum Kind { Root, Folder, Drive, Recent, Unknown } kind = Unknown;
    QString id;
};
Target parseUrl(const QUrl &url);

// ------------------------------------------------------- user-facing text
// Implemented twice from one file (text.cpp): with KI18n in the worker
// (domain "lucent-thispc", po/ru.po) and plain English for the tests.
namespace Text
{
QString thisPc();
QString section(Section section);
QString home();
QString localDisk();
QString usbDrive();
QString items(int count);
QString free(const QString &size);
QString ofTotal(const QString &size);
QString readOnly();
QString usb(const QString &size);
}

} // namespace ThisPc
