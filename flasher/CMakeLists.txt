cmake_minimum_required(VERSION 3.21)
project(PocketsoFlasher VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)

find_package(Qt6 6.4 REQUIRED COMPONENTS Core Gui Qml Quick QuickControls2 Network)

qt_add_executable(PocketsoFlasher
    src/main.cpp
    src/FlasherBackend.cpp
    src/FlasherBackend.h
)

qt_add_qml_module(PocketsoFlasher
    URI Pocketso.Flasher
    VERSION 1.0
    QML_FILES qml/Main.qml
)

target_link_libraries(PocketsoFlasher PRIVATE
    Qt6::Core Qt6::Gui Qt6::Qml Qt6::Quick Qt6::QuickControls2 Qt6::Network
)

qt_add_executable(pocketso-flash-root
    src/flash_root.cpp
)
target_link_libraries(pocketso-flash-root PRIVATE Qt6::Core)

include(GNUInstallDirs)
install(TARGETS PocketsoFlasher RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR})
install(TARGETS pocketso-flash-root RUNTIME DESTINATION ${CMAKE_INSTALL_LIBEXECDIR})
install(FILES packaging/pocketso-flasher.desktop DESTINATION ${CMAKE_INSTALL_DATADIR}/applications)
install(FILES packaging/pocketso-flasher.svg DESTINATION ${CMAKE_INSTALL_DATADIR}/icons/hicolor/scalable/apps)
install(FILES packaging/org.pocketso.flasher.policy DESTINATION ${CMAKE_INSTALL_DATADIR}/polkit-1/actions)
