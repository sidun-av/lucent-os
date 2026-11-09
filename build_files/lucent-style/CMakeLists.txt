# Lucent widget style: a thin QProxyStyle over Kvantum (see lucentstyle.cpp).
cmake_minimum_required(VERSION 3.20)
project(lucentstyle LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_AUTOMOC ON)
find_package(Qt6 REQUIRED COMPONENTS Core Gui Widgets)
add_library(lucentstyle MODULE lucentstyle.cpp)
target_link_libraries(lucentstyle PRIVATE Qt6::Core Qt6::Gui Qt6::Widgets)
install(TARGETS lucentstyle LIBRARY DESTINATION ${QT6_INSTALL_PLUGINS}/styles)
