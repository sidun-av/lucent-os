"""English strings (primary) and their Russian translation.

The same strings are the final copy for the Settings "Devices" page
(docs/specs/devices-page.md); keep the two in step.
"""

STRINGS = {
    "en": {
        "summary_ok": "All {n} devices are working.",
        "summary_ok_1": "The only device is working.",
        "summary_attention": "{k} of {n} devices need attention.",
        "summary_attention_1": "1 of {n} devices needs attention.",
        "no_log": "Couldn't read the system log, so firmware problems can't be shown.",
        "status.working": "Working",
        "status.needs_driver": "Needs a driver",
        "status.problem": "Has a problem",
        "status.unused": "Not in use",
        "group.wifi": "Wi-Fi",
        "group.ethernet": "Wired network",
        "group.bluetooth": "Bluetooth",
        "group.sound": "Sound",
        "group.display": "Display and graphics",
        "group.camera": "Camera",
        "group.input": "Keyboard, mouse and touchpad",
        "group.storage": "Disks and storage",
        "group.other": "Other devices",
        "driver": "Driver: {driver}",
        "no_driver_bound": "No driver",
        "note.turned_off": "Turned off",
        "problem.no_driver": "Lucent has no driver for this device.",
        "do.no_driver": "Install updates: new versions of Lucent add drivers. A USB adapter that works with Linux is the quickest fix.",
        "problem.broadcom-wl": "This Broadcom Wi-Fi chip only works with Broadcom's own driver, which Lucent doesn't include yet.",
        "do.broadcom-wl": "Use a wired connection or a USB Wi-Fi adapter for now.",
        "problem.firmware_missing": "A file it needs to start is missing ({file}).",
        "do.firmware_missing": "Install updates and restart. If it still doesn't work, this device may be newer than this version of Lucent.",
        "problem.firmware_failed": "Its firmware didn't load ({file}).",
        "do.firmware_failed": "Restart the computer. If it happens again, install updates.",
        "problem.probe_failed": "Its driver couldn't start it ({driver}, error {error}).",
        "do.probe_failed": "Restart the computer. If it keeps happening, install updates.",
        "problem.switched_off": "It's turned off by a switch or key on the computer.",
        "do.switched_off": "Look for a Wi-Fi or airplane-mode switch, or a key with an antenna icon (often Fn with an F key).",
        "unused.hint": "No driver is loaded for it; programs can use it directly.",
        "hidden": "{n} system parts are not shown (lucent-devices --all).",
    },
    "ru": {
        "summary_ok": "Все устройства работают ({n}).",
        "summary_ok_1": "Единственное устройство работает.",
        "summary_attention": "Устройств, требующих внимания: {k} из {n}.",
        "summary_attention_1": "Устройств, требующих внимания: 1 из {n}.",
        "no_log": "Не удалось прочитать системный журнал, поэтому проблемы с микропрограммами не показаны.",
        "status.working": "Работает",
        "status.needs_driver": "Нужен драйвер",
        "status.problem": "Есть проблема",
        "status.unused": "Не используется",
        "group.wifi": "Wi-Fi",
        "group.ethernet": "Проводная сеть",
        "group.bluetooth": "Bluetooth",
        "group.sound": "Звук",
        "group.display": "Экран и видеокарта",
        "group.camera": "Камера",
        "group.input": "Клавиатура, мышь и тачпад",
        "group.storage": "Диски и накопители",
        "group.other": "Другие устройства",
        "driver": "Драйвер: {driver}",
        "no_driver_bound": "Нет драйвера",
        "note.turned_off": "Выключено",
        "problem.no_driver": "В Lucent нет драйвера для этого устройства.",
        "do.no_driver": "Установите обновления: в новых версиях Lucent появляются драйверы. Быстрее всего поможет USB-адаптер, который работает с Linux.",
        "problem.broadcom-wl": "Этот Wi-Fi-чип Broadcom работает только с собственным драйвером Broadcom, которого пока нет в Lucent.",
        "do.broadcom-wl": "Пока подключитесь по проводу или через USB-адаптер Wi-Fi.",
        "problem.firmware_missing": "Не найден файл, который нужен ему для запуска ({file}).",
        "do.firmware_missing": "Установите обновления и перезагрузите компьютер. Если не поможет, возможно, устройство новее этой версии Lucent.",
        "problem.firmware_failed": "Не загрузилась его микропрограмма ({file}).",
        "do.firmware_failed": "Перезагрузите компьютер. Если повторится, установите обновления.",
        "problem.probe_failed": "Драйвер не смог его запустить ({driver}, ошибка {error}).",
        "do.probe_failed": "Перезагрузите компьютер. Если повторяется, установите обновления.",
        "problem.switched_off": "Оно выключено переключателем или клавишей на компьютере.",
        "do.switched_off": "Найдите переключатель Wi-Fi или режима полёта либо клавишу со значком антенны (часто вместе с Fn).",
        "unused.hint": "Драйвер для него не загружен; программы могут работать с ним напрямую.",
        "hidden": "Системные компоненты не показаны: {n} (lucent-devices --all).",
    },
}


def pick_lang(env) -> str:
    for key in ("LC_ALL", "LC_MESSAGES", "LANGUAGE", "LANG"):
        v = env.get(key)
        if v:
            return "ru" if v.split(":")[0].lower().startswith("ru") else "en"
    return "en"


def t(lang, key, **kw):
    table = STRINGS.get(lang, STRINGS["en"])
    return table.get(key, STRINGS["en"][key]).format(**kw)
