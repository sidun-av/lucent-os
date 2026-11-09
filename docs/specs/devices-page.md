# Settings > Devices: spec

Status: spec for the Settings owner, 2026-11-09. Backend implemented:
`lucent-devices` (`system_files/usr/lib/lucent/lucent_devices/`). This
spec does not touch `apps/lucent-settings/`.

## Why

When something doesn't work on Windows, people open Device Manager. It has
the right information (every device, its driver, a yellow mark on a
problem) but shows it as a tree of chipset jargon. Lucent's page keeps the
information and changes the tone: say first whether everything works,
list problems first with one clear thing to do, and keep the chipset out
of sight unless it is the problem.

## Where

A **Devices** entry in the Settings sidebar, directly below "Bluetooth &
devices" (icon: a chip or a monitor with a checkmark). "Bluetooth &
devices" stays about pairing and peripherals; Devices is about whether the
hardware works. Search terms: "device manager", "drivers", "hardware",
"диспетчер устройств", "драйверы", "оборудование". The Windows name
matters: someone typing "device manager" must land here.

## Data

`lucent-devices --json` (no root needed, no network, about 0.1 s). The
page calls it when opened and when the user presses Refresh; it does not
poll. Schema 1:

```json
{
  "schema": 1,
  "summary": {"total": 14, "working": 10, "needs_driver": 1, "problem": 3, "unused": 2, "system": 3},
  "kernel_log": {"readable": true, "source": "journal"},
  "devices": [
    {
      "id": "pci:0000:00:02.0", "syspath": "/sys/devices/pci0000:00/0000:00:02.0", "bus": "pci",
      "group": "display", "name": "Alder Lake-P GT2 [Iris Xe Graphics]", "vendor": "Intel Corporation",
      "ids": {"vendor": "8086", "device": "46a6"},
      "driver": "i915", "drivers": ["i915"],
      "status": "problem",
      "problems": [{"code": "firmware_missing", "file": "i915/adlp_dmc.bin", "error": -2, "present": false}],
      "firmware": [{"file": "i915/adlp_dmc.bin", "error": -2, "fatal": true, "present": false}],
      "notes": [], "system": false, "hint": null
    }
  ]
}
```

- `group`: `wifi`, `ethernet`, `bluetooth`, `sound`, `display`, `camera`,
  `input`, `storage`, `other` (this is also the display order).
- `status`: `working`, `needs_driver`, `problem`, `unused`. Devices come
  sorted: problems, then needs a driver, then working, then unused; within
  that by group and name.
- `problems[].code`: `no_driver`, `firmware_missing`, `firmware_failed`,
  `probe_failed`, `switched_off`.
- `hint`: `broadcom-wl` for a Broadcom Wi-Fi chip only Broadcom's driver
  supports (see [../drivers.md](../drivers.md)); replaces the generic
  no-driver text.
- `notes`: `turned_off` (the radio is off in software: the user's own
  choice, not a problem).
- `system`: chipset parts (SMBus, I2C controllers and the like). Hidden
  unless they have a problem or "Show all devices" is on.
- `summary.total` counts what the page shows by default: everything that
  is not `system` and not `unused`, plus any problem.
- `kernel_log.readable: false` means firmware failures could not be
  checked (the user is not in `wheel`); say so, never claim "all working"
  on firmware grounds.
- Exit status 1 means "needs attention"; it is not an error.

## Layout (Pebble Drift)

Same shell as Settings > Appearance (`04-settings.png`): page title,
one-line description, cards on the window surface.

1. **Title** "Devices", description "The hardware in this PC and whether
   it works."
2. **Summary card** (one row, large): a 40 px status glyph on the left
   (`--status-success` check when everything works, `--status-warning`
   when something needs attention, never red for the page as a whole), the
   summary sentence in 20 px semibold, and on the right a quiet
   **Refresh** button. Below the sentence, in `--text-secondary`, the
   no-log notice when `kernel_log.readable` is false.
3. **Needs attention card**, only when there is something: one row per
   problem device, in API order. Each row: group icon, device name
   (16 px, primary), vendor (secondary), a status chip (`--status-warning`
   soft fill for "Needs a driver" and "Has a problem"), then two lines:
   what is wrong (primary text) and what to do (secondary text). Rows have
   a **Details** disclosure (see below) and, where it applies, one action
   button on the right (see "Actions").
4. **One card per group** that has devices, in group order, two columns
   on wide windows like Appearance's "Accent color / Comfort" pair. Each
   row: icon, name, vendor, and on the right a small status: a
   `--status-success` dot and "Working", or "Turned off" in tertiary text.
   No driver names in the row. A device with a problem appears only in the
   Needs attention card, not again in its group.
5. **Footer row**: a "Show all devices" switch (includes `system` and
   `unused`), and "Copy details", which copies `lucent-devices` plain text
   (`lucent-devices --all`) for a help request.

**Details** (disclosure in any row, sunken well): Driver (or "No driver"),
Device ID (`8086:46a6`), Connected by (PCI / USB / built-in), and for
firmware entries the file name. These are the Device Manager facts, one
click away, never in the first view.

Empty, error states: if `lucent-devices` exits with status 2 or isn't
installed, show the summary card with "Couldn't list devices." and the
Refresh button.

No ads, no "recommended drivers" store, no telemetry: the page reads local
data and offers only the actions below.

## Actions

| Situation | Button | What it does |
| --- | --- | --- |
| `switched_off` | none | Text only: the user must flip a switch. |
| `firmware_missing`, `firmware_failed`, `no_driver` | **Check for updates** | Opens Settings > Updates. |
| `probe_failed` | **Restart** | The normal restart confirmation. |
| `hint: broadcom-wl` | none (for now) | Text only. If the owner adds an opt-in driver later, it becomes "Use Broadcom's driver" (docs/drivers.md). |
| NVIDIA GPU, working with `nouveau` | none (for now) | A future `lucent-os-nvidia` switch would add a quiet "Use NVIDIA's driver (better for games)" row in the Display card; not part of this spec. |

## Strings

English is the primary text; Russian is the translation. The same strings
are in `lucent_devices/strings.py`, which the plain-text output uses; keep
both in step. `{n}`, `{k}`, `{file}`, `{driver}`, `{error}` are
placeholders.

| Key | English | Russian |
| --- | --- | --- |
| page.title | Devices | Устройства |
| page.description | The hardware in this PC and whether it works. | Оборудование этого компьютера и его состояние. |
| summary_ok | All {n} devices are working. | Все устройства работают ({n}). |
| summary_ok_1 | The only device is working. | Единственное устройство работает. |
| summary_attention | {k} of {n} devices need attention. | Устройств, требующих внимания: {k} из {n}. |
| summary_attention_1 | 1 of {n} devices needs attention. | Устройств, требующих внимания: 1 из {n}. |
| summary_error | Couldn't list devices. | Не удалось получить список устройств. |
| no_log | Couldn't read the system log, so firmware problems can't be shown. | Не удалось прочитать системный журнал, поэтому проблемы с микропрограммами не показаны. |
| card.attention | Needs attention | Требуют внимания |
| status.working | Working | Работает |
| status.needs_driver | Needs a driver | Нужен драйвер |
| status.problem | Has a problem | Есть проблема |
| status.unused | Not in use | Не используется |
| note.turned_off | Turned off | Выключено |
| group.wifi | Wi-Fi | Wi-Fi |
| group.ethernet | Wired network | Проводная сеть |
| group.bluetooth | Bluetooth | Bluetooth |
| group.sound | Sound | Звук |
| group.display | Display and graphics | Экран и видеокарта |
| group.camera | Camera | Камера |
| group.input | Keyboard, mouse and touchpad | Клавиатура, мышь и тачпад |
| group.storage | Disks and storage | Диски и накопители |
| group.other | Other devices | Другие устройства |
| problem.no_driver | Lucent has no driver for this device. | В Lucent нет драйвера для этого устройства. |
| do.no_driver | Install updates: new versions of Lucent add drivers. A USB adapter that works with Linux is the quickest fix. | Установите обновления: в новых версиях Lucent появляются драйверы. Быстрее всего поможет USB-адаптер, который работает с Linux. |
| problem.broadcom-wl | This Broadcom Wi-Fi chip only works with Broadcom's own driver, which Lucent doesn't include yet. | Этот Wi-Fi-чип Broadcom работает только с собственным драйвером Broadcom, которого пока нет в Lucent. |
| do.broadcom-wl | Use a wired connection or a USB Wi-Fi adapter for now. | Пока подключитесь по проводу или через USB-адаптер Wi-Fi. |
| problem.firmware_missing | A file it needs to start is missing ({file}). | Не найден файл, который нужен ему для запуска ({file}). |
| do.firmware_missing | Install updates and restart. If it still doesn't work, this device may be newer than this version of Lucent. | Установите обновления и перезагрузите компьютер. Если не поможет, возможно, устройство новее этой версии Lucent. |
| problem.firmware_failed | Its firmware didn't load ({file}). | Не загрузилась его микропрограмма ({file}). |
| do.firmware_failed | Restart the computer. If it happens again, install updates. | Перезагрузите компьютер. Если повторится, установите обновления. |
| problem.probe_failed | Its driver couldn't start it ({driver}, error {error}). | Драйвер не смог его запустить ({driver}, ошибка {error}). |
| do.probe_failed | Restart the computer. If it keeps happening, install updates. | Перезагрузите компьютер. Если повторяется, установите обновления. |
| problem.switched_off | It's turned off by a switch or key on the computer. | Оно выключено переключателем или клавишей на компьютере. |
| do.switched_off | Look for a Wi-Fi or airplane-mode switch, or a key with an antenna icon (often Fn with an F key). | Найдите переключатель Wi-Fi или режима полёта либо клавишу со значком антенны (часто вместе с Fn). |
| unused.hint | No driver is loaded for it; programs can use it directly. | Драйвер для него не загружен; программы могут работать с ним напрямую. |
| driver | Driver: {driver} | Драйвер: {driver} |
| no_driver_bound | No driver | Нет драйвера |
| details.device_id | Device ID | Код устройства |
| details.connected_by | Connected by | Подключение |
| details.bus.pci | Built in (PCI) | Встроенное (PCI) |
| details.bus.usb | USB | USB |
| details.bus.other | Built in | Встроенное |
| details.firmware | Firmware file | Файл микропрограммы |
| action.refresh | Refresh | Обновить |
| action.updates | Check for updates | Проверить обновления |
| action.restart | Restart | Перезагрузить |
| action.details | Details | Подробности |
| action.copy | Copy details | Скопировать сведения |
| action.copied | Copied | Скопировано |
| toggle.show_all | Show all devices | Показать все устройства |
| toggle.show_all.sub | Includes chipset parts that need no attention | Включая компоненты чипсета, которые не требуют внимания |

Russian avoids number agreement ("{k} из {n}" after a colon, "({n})")
so one form works for every number.

## Acceptance

- On a PC where everything works the page shows one card that says "All
  N devices are working." and the group cards; nothing yellow.
- Unplugging a USB device and pressing Refresh removes it.
- `LANG=ru_RU.UTF-8`: every visible string is Russian; device names stay
  as the hwdb gives them.
- The page never shows a driver name, PCI ID or firmware file outside
  Details, except inside the "what is wrong" sentence, where the file name
  is what a helper needs.
- Checked against `lucent-devices`' fixtures (`tests/devices/fixtures/`):
  the constructed laptop shows 4 rows in Needs attention in this order:
  RTL8852BE (problem), AX211 Bluetooth (problem), Iris Xe (problem),
  BCM4352 (needs a driver).
