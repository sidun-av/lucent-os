/*
 * thispcnotifier (kded module): keeps an open "This PC" page current.
 *
 * Dolphin re-lists a folder when KDirNotify says something was added to it.
 * thispc:/ has no files to watch, so this module (inside kded, no process of
 * its own) tells Dolphin whenever a drive appears, disappears, is mounted or
 * unmounted: a USB stick shows up on the page as it is plugged in.
 *
 * SPDX-License-Identifier: Apache-2.0
 */
#include <KDEDModule>
#include <KDirNotify>
#include <KPluginFactory>
#include <Solid/Device>
#include <Solid/DeviceNotifier>
#include <Solid/StorageAccess>

#include <QSet>
#include <QTimer>
#include <QUrl>

class ThisPcNotifier : public KDEDModule
{
    Q_OBJECT
public:
    ThisPcNotifier(QObject *parent, const QList<QVariant> &)
        : KDEDModule(parent)
    {
        m_timer.setSingleShot(true);
        m_timer.setInterval(500); // one refresh for a burst of udev events
        connect(&m_timer, &QTimer::timeout, this, [] {
            org::kde::KDirNotify::emitFilesAdded(QUrl(QStringLiteral("thispc:/")));
        });
        auto *notifier = Solid::DeviceNotifier::instance();
        connect(notifier, &Solid::DeviceNotifier::deviceAdded, this, [this](const QString &udi) {
            watch(Solid::Device(udi));
            m_timer.start();
        });
        connect(notifier, &Solid::DeviceNotifier::deviceRemoved, this, [this](const QString &udi) {
            m_watched.remove(udi);
            m_timer.start();
        });
        const QList<Solid::Device> devices = Solid::Device::listFromType(Solid::DeviceInterface::StorageAccess);
        for (const Solid::Device &d : devices)
            watch(d);
    }

private:
    void watch(const Solid::Device &device)
    {
        auto *access = device.as<Solid::StorageAccess>();
        if (!access || m_watched.contains(device.udi()))
            return;
        m_watched.insert(device.udi());
        connect(access, &Solid::StorageAccess::accessibilityChanged, this, [this] {
            m_timer.start();
        });
    }

    QTimer m_timer;
    QSet<QString> m_watched;
};

K_PLUGIN_CLASS_WITH_JSON(ThisPcNotifier, "thispcnotifier.json")

#include "notifier.moc"
