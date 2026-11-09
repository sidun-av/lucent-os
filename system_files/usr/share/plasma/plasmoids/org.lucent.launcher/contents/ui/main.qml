/*
    Lucent launcher: the taskbar's start button and the full-screen app
    launcher it opens (docs/mockups/02-launcher). Uses Plasma's own kicker
    backend (app/category models, KRunner search, session actions), so apps,
    search results and power actions behave exactly as in stock Plasma.

    SPDX-License-Identifier: GPL-2.0-or-later
*/
pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts

import org.kde.kirigami as Kirigami
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasmoid
import org.kde.plasma.private.kicker as Kicker

PlasmoidItem {
    id: kicker

    signal reset

    // Like Application Dashboard: no popup of our own, the button is always shown.
    preferredRepresentation: fullRepresentation
    compactRepresentation: null
    fullRepresentation: button

    Plasmoid.icon: "lucent-start"
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground

    readonly property bool dark: Kirigami.ColorUtils.brightnessForColor(Kirigami.Theme.backgroundColor) === Kirigami.ColorUtils.Dark

    Component {
        id: button
        MouseArea {
            id: area
            Layout.minimumWidth: 50
            Layout.preferredWidth: 50
            Layout.maximumWidth: 50
            Layout.fillHeight: true
            hoverEnabled: true
            activeFocusOnTab: true
            Accessible.role: Accessible.Button
            Accessible.name: Plasmoid.title
            Keys.onReturnPressed: dash.toggle()
            Keys.onSpacePressed: dash.toggle()
            onClicked: dash.toggle()

            Rectangle {
                anchors.centerIn: parent
                width: 46
                height: 46
                radius: 13
                color: kicker.dark ? Qt.rgba(1, 1, 1, area.pressed ? 0.14 : 0.08)
                                   : Qt.rgba(1, 1, 1, area.pressed ? 0.9 : 0.6)
                opacity: area.containsMouse || area.pressed || dash.visible ? 1 : 0
                Behavior on opacity { NumberAnimation { duration: Kirigami.Units.shortDuration } }
            }
            Kirigami.Icon {
                anchors.centerIn: parent
                width: 30
                height: 30
                roundToIconSize: false
                source: Plasmoid.icon
            }

            Dashboard {
                id: dash
                visualParent: area
                rootModel: rootModel
                runnerModel: runnerModel
                pinned: Plasmoid.configuration.pinned
                dark: kicker.dark
            }

            Connections {
                target: Plasmoid
                function onActivated() { dash.toggle() }
            }
        }
    }

    Kicker.RootModel {
        id: rootModel
        autoPopulate: false
        appNameFormat: 0          // name only ("Files", not "Dolphin (Files)")
        flat: true
        sorted: true
        showSeparators: false
        showRootSeparator: false
        appletInterface: kicker
        showAllApps: true
        showAllAppsCategorized: false   // one flat A-Z list, not letter groups
        showPowerSession: false         // power actions live behind the power button
        showTopLevelItems: false
        showRecentApps: false
        showRecentDocs: false
        showRecentFolders: false
        highlightNewlyInstalledApps: false

        Component.onCompleted: {
            (favoritesModel as Kicker.KAStatsFavoritesModel).initForClient("org.lucent.launcher.favorites.instance-" + Plasmoid.id)
            systemFavoritesModel.favorites = ["lock-screen", "logout", "suspend", "reboot", "shutdown"]
        }
    }

    Kicker.RunnerModel {
        id: runnerModel
        appletInterface: kicker
        favoritesModel: rootModel.favoritesModel as Kicker.KAStatsFavoritesModel
        mergeResults: true
        runners: ["krunner_services", "krunner_systemsettings", "krunner_sessions",
                  "krunner_powerdevil", "baloosearch", "calculator", "unitconverter"]
    }

    Kicker.ProcessRunner {
        id: processRunner
    }

    Plasmoid.contextualActions: [
        PlasmaCore.Action {
            text: i18nc("@action:inmenu", "Edit Applications…")
            icon.name: "kmenuedit"
            visible: Plasmoid.immutability !== PlasmaCore.Types.SystemImmutable
            onTriggered: processRunner.runMenuEditor()
        }
    ]

    Component.onCompleted: {
        if (Plasmoid.hasOwnProperty("activationTogglesExpanded")) {
            Plasmoid.activationTogglesExpanded = false
        }
        rootModel.refresh()
    }
}
