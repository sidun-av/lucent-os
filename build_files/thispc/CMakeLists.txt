# Lucent "This PC" (docs/this-pc.md):
#   thispc_core  - what the page lists and how it names it (Qt Core only, tested)
#   kio_thispc   - the KIO worker behind thispc:/ (KF6 KIO + Solid)
#   thispcnotifier - kded module: refresh thispc:/ when drives come and go
# Without KF6 (e.g. on a developer's Mac) only the core and its tests build.
cmake_minimum_required(VERSION 3.20)
project(lucent-thispc LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)

find_package(Qt6 REQUIRED COMPONENTS Core Test)
enable_testing()

add_library(thispc_core STATIC core/core.cpp)
target_include_directories(thispc_core PUBLIC core)
target_link_libraries(thispc_core PUBLIC Qt6::Core)

# Plain-English strings for the tests.
add_library(thispc_text_en STATIC core/text.cpp)
target_link_libraries(thispc_text_en PUBLIC thispc_core)

add_executable(core_test tests/core_test.cpp)
target_link_libraries(core_test PRIVATE thispc_core thispc_text_en Qt6::Test)
add_test(NAME core_test COMMAND core_test)

find_package(KF6KIO QUIET)
if(KF6KIO_FOUND)
    find_package(Qt6 REQUIRED COMPONENTS DBus)
    find_package(KF6 REQUIRED COMPONENTS Solid I18n CoreAddons DBusAddons)
    set_target_properties(thispc_core PROPERTIES POSITION_INDEPENDENT_CODE ON)

    add_library(kio_thispc MODULE worker.cpp core/text.cpp)
    target_compile_definitions(kio_thispc PRIVATE THISPC_KI18N TRANSLATION_DOMAIN="lucent-thispc")
    target_link_libraries(kio_thispc PRIVATE thispc_core Qt6::DBus KF6::KIOCore KF6::Solid KF6::I18n KF6::CoreAddons)
    set_target_properties(kio_thispc PROPERTIES OUTPUT_NAME thispc PREFIX "")
    install(TARGETS kio_thispc LIBRARY DESTINATION ${QT6_INSTALL_PLUGINS}/kf6/kio)

    add_library(thispcnotifier MODULE notifier.cpp)
    target_link_libraries(thispcnotifier PRIVATE KF6::KIOCore KF6::Solid KF6::DBusAddons KF6::CoreAddons)
    set_target_properties(thispcnotifier PROPERTIES PREFIX "")
    install(TARGETS thispcnotifier LIBRARY DESTINATION ${QT6_INSTALL_PLUGINS}/kf6/kded)
endif()
