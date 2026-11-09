/*
 * User-facing text of "This PC". English is the source; with THISPC_KI18N
 * (the KIO worker) every string goes through KI18n, domain "lucent-thispc",
 * translated in po/ru.po. Without it (the tests) the English is used as is.
 *
 * SPDX-License-Identifier: Apache-2.0
 */
#include "thispc_core.h"

#ifdef THISPC_KI18N
#include <KLocalizedString>
#define TR(ctx, text) i18nc(ctx, text)
#define TR1(ctx, text, a) i18nc(ctx, text, a)
#define TR2(ctx, text, a, b) i18nc(ctx, text, a, b)
#define TRP(ctx, one, many, n) i18ncp(ctx, one, many, n)
#else
#define TR(ctx, text) QStringLiteral(text)
#define TR1(ctx, text, a) QStringLiteral(text).arg(a)
#define TR2(ctx, text, a, b) QStringLiteral(text).arg(a, b)
#define TRP(ctx, one, many, n) ((n) == 1 ? QStringLiteral(one) : QStringLiteral(many)).arg(n)
#endif

namespace ThisPc::Text
{
QString thisPc()
{
    return TR("@title the overview page of Files", "This PC");
}

QString section(Section section)
{
    switch (section) {
    case Section::Folders:
        return TR("@title:group", "Folders");
    case Section::Drives:
        return TR("@title:group", "Drives and devices");
    case Section::Recent:
        break;
    }
    return TR("@title:group", "Recent files");
}

QString home()
{
    return TR("@item the drive that holds the user's files", "Home");
}

QString localDisk()
{
    return TR("@item a drive without a name, as Windows calls it", "Local Disk");
}

QString usbDrive()
{
    return TR("@item a removable drive without a name", "USB drive");
}

QString items(int count)
{
    return TRP("@info number of items in a folder", "%1 item", "%1 items", count);
}

QString freeOf(const QString &free, const QString &total)
{
    return TR2("@info free space, e.g. 410 GB free of 512 GB", "%1 free of %2", free, total);
}

QString readOnly(const QString &rest)
{
    return TR1("@info a drive whose files can't be changed; %1 is its size or free space", "Read-only · %1", rest);
}

QString usb(const QString &rest)
{
    return TR1("@info %1 is the drive's size", "USB drive · %1", rest);
}

QString recent(const QString &folder, const QString &when)
{
    return TR2("@info folder of a recent file and when it changed, e.g. Documents · Today", "%1 · %2", folder, when);
}
} // namespace ThisPc::Text
