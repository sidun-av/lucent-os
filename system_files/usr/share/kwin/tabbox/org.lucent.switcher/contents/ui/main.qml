/*
 Lucent window switcher (Alt+Tab): Windows-style row of thumbnails on a
 Lucent card (radius 20, popup colour, hairline, soft shadow) drawn here, not
 by the Plasma theme, so it looks the same in every KWin setup. Based on
 KWin's Thumbnail Grid switcher.

 SPDX-FileCopyrightText: 2020 Chris Holland <zrenfire@gmail.com>
 SPDX-FileCopyrightText: 2023 Nate Graham <nate@kde.org>
 SPDX-FileCopyrightText: 2026 Lucent OS contributors
 SPDX-License-Identifier: GPL-2.0-or-later
 */

import QtQuick
import QtQuick.Effects
import QtQuick.Layouts
import org.kde.plasma.core as PlasmaCore
import org.kde.kwin as KWin
import org.kde.kirigami as Kirigami

KWin.TabBoxSwitcher {
    id: tabBox

    Instantiator {
        active: tabBox.visible
        delegate: PlasmaCore.Dialog {
            location: PlasmaCore.Types.Floating
            backgroundHints: PlasmaCore.Types.NoBackground
            type: PlasmaCore.Dialog.OnScreenDisplay
            visible: true
            flags: Qt.ToolTip | Qt.X11BypassWindowManagerHint
            x: tabBox.screenGeometry.x + tabBox.screenGeometry.width * 0.5 - dialogMainItem.width * 0.5
            y: tabBox.screenGeometry.y + tabBox.screenGeometry.height * 0.5 - dialogMainItem.height * 0.5

            mainItem: FocusScope {
                id: dialogMainItem
                focus: true

                readonly property real screenFactor: tabBox.screenGeometry.width / tabBox.screenGeometry.height
                readonly property int maxWidth: tabBox.screenGeometry.width * 0.9
                readonly property int columns: Math.max(1, Math.min(grid.count, Math.floor(maxWidth / grid.cellWidth)))
                readonly property int rows: Math.ceil(grid.count / columns)

                readonly property int pad: 40          // room for the shadow
                width: Math.max(grid.cellWidth, columns * grid.cellWidth) + 2 * 14 + 2 * pad
                height: Math.min(rows * grid.cellHeight, tabBox.screenGeometry.height * 0.7) + 2 * 14 + 2 * pad

                RectangularShadow {
                    anchors.fill: card
                    radius: card.radius
                    offset.y: 16
                    blur: 44
                    spread: 0
                    color: Qt.rgba(0.04, 0.06, 0.12, Kirigami.Theme.backgroundColor.hslLightness < 0.5 ? 0.45 : 0.24)
                }
                Rectangle {
                    id: card
                    anchors.fill: parent
                    anchors.margins: dialogMainItem.pad
                    radius: 20
                    color: Qt.rgba(Kirigami.Theme.backgroundColor.r, Kirigami.Theme.backgroundColor.g, Kirigami.Theme.backgroundColor.b, 0.96)
                    border.width: 1
                    border.color: Qt.rgba(Kirigami.Theme.textColor.r, Kirigami.Theme.textColor.g, Kirigami.Theme.textColor.b, 0.10)
                }

                GridView {
                    id: grid
                    anchors.fill: card
                    anchors.margins: 14
                    clip: true
                    focus: true
                    model: tabBox.model
                    currentIndex: tabBox.currentIndex
                    keyNavigationWraps: true
                    highlightMoveDuration: 0
                    interactive: false

                    readonly property int thumbW: 296
                    readonly property int thumbH: Math.round(thumbW / dialogMainItem.screenFactor)
                    cellWidth: thumbW + 28
                    cellHeight: thumbH + 28 + 44

                    delegate: MouseArea {
                        id: item
                        required property int index
                        required property var model
                        width: grid.cellWidth
                        height: grid.cellHeight
                        hoverEnabled: true
                        readonly property bool current: GridView.isCurrentItem
                        Accessible.name: model.caption
                        Accessible.role: Accessible.ListItem
                        onClicked: tabBox.model.activate(index)

                        Rectangle {      // card: hover fill, accent ring when selected
                            anchors.fill: parent
                            anchors.margins: 4
                            radius: 16
                            color: item.current ? Qt.rgba(Kirigami.Theme.highlightColor.r, Kirigami.Theme.highlightColor.g, Kirigami.Theme.highlightColor.b, 0.14)
                                                : (item.containsMouse ? Qt.rgba(Kirigami.Theme.textColor.r, Kirigami.Theme.textColor.g, Kirigami.Theme.textColor.b, 0.06) : "transparent")
                            border.width: item.current ? 2.5 : 0
                            border.color: Kirigami.Theme.highlightColor
                        }

                        Item {
                            id: thumbBox
                            x: 14
                            y: 14
                            width: grid.thumbW
                            height: grid.thumbH

                            KWin.WindowThumbnail {
                                id: thumb
                                anchors.fill: parent
                                wId: item.model.windowId
                                layer.enabled: true
                                layer.effect: MultiEffect {
                                    maskEnabled: true
                                    maskSource: thumbMask
                                    maskThresholdMin: 0.5
                                    maskSpreadAtMin: 1.0
                                }
                            }
                            Rectangle {
                                id: thumbMask
                                anchors.fill: parent
                                radius: 10
                                visible: false
                                layer.enabled: true
                            }
                        }

                        RowLayout {
                            anchors.left: thumbBox.left
                            anchors.right: thumbBox.right
                            anchors.top: thumbBox.bottom
                            anchors.topMargin: 12
                            spacing: 10
                            Kirigami.Icon {
                                Layout.preferredWidth: 32
                                Layout.preferredHeight: 32
                                source: item.model.icon
                            }
                            Text {
                                Layout.fillWidth: true
                                text: item.model.caption
                                color: Kirigami.Theme.textColor
                                font.pointSize: 11
                                font.weight: item.current ? Font.DemiBold : Font.Normal
                                elide: Text.ElideRight
                                textFormat: Text.PlainText
                            }
                        }
                    }

                    onCurrentIndexChanged: tabBox.currentIndex = grid.currentIndex
                }

                Kirigami.PlaceholderMessage {
                    anchors.centerIn: parent
                    width: parent.width - Kirigami.Units.largeSpacing * 2
                    icon.source: "edit-none"
                    text: i18ndc("kwin", "@info:placeholder no entries in the task switcher", "No open windows")
                    visible: grid.count === 0
                }

                Keys.onPressed: event => {
                    if (event.key === Qt.Key_Left) {
                        grid.moveCurrentIndexLeft()
                    } else if (event.key === Qt.Key_Right) {
                        grid.moveCurrentIndexRight()
                    } else if (event.key === Qt.Key_Up) {
                        grid.moveCurrentIndexUp()
                    } else if (event.key === Qt.Key_Down) {
                        grid.moveCurrentIndexDown()
                    } else {
                        return
                    }
                    grid.currentIndexChanged(grid.currentIndex)
                }
            }

            onSceneGraphError: () => {}
        }
    }
}
