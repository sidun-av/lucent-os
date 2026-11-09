# org.lucent.chrome: one header row for Lucent's own apps (Settings, Store).
# The app window is frameless; this QML module gives it what KWin's decoration
# would: a KWin-drawn shadow (KWindowShadow, the org_kde_kwin_shadow protocol),
# the window-button order from kwinrc (live), and QML pieces for the buttons,
# dragging, double-click to maximise and resizing at the edges.
cmake_minimum_required(VERSION 3.20)
project(lucent-chrome LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)

find_package(Qt6 REQUIRED COMPONENTS Core Gui DBus Qml Quick)
find_package(KF6WindowSystem REQUIRED)
find_package(KF6Config REQUIRED)

add_library(lucentchromeplugin MODULE plugin.cpp windowframe.cpp shadow.cpp glyph.cpp)
target_link_libraries(lucentchromeplugin PRIVATE Qt6::Gui Qt6::DBus Qt6::Qml Qt6::Quick KF6::WindowSystem KF6::ConfigCore)

set(QMLDIR "${CMAKE_INSTALL_PREFIX}/lib64/qt6/qml/org/lucent/chrome" CACHE PATH "where the QML module goes")
install(TARGETS lucentchromeplugin DESTINATION ${QMLDIR})
install(FILES qmldir WindowButtons.qml WindowButton.qml HeaderDragArea.qml ResizeHandles.qml WindowBackground.qml DESTINATION ${QMLDIR})

# The shadow tiles are plain Qt: test them without a compositor.
find_package(Qt6 COMPONENTS Test)
if(Qt6Test_FOUND)
    enable_testing()
    add_executable(shadow_test tests/shadow_test.cpp shadow.cpp)
    target_include_directories(shadow_test PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
    target_link_libraries(shadow_test PRIVATE Qt6::Gui Qt6::Test)
    add_test(NAME shadow_test COMMAND shadow_test)
endif()
