#include "FlasherBackend.h"

#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include <QQuickStyle>

int main(int argc, char *argv[])
{
    QGuiApplication app(argc, argv);
    QGuiApplication::setApplicationName("Pocketso Flasher");
    QGuiApplication::setOrganizationName("Pocketso");

    QQuickStyle::setStyle("Basic");

    FlasherBackend flasher;
    QQmlApplicationEngine engine;
    engine.rootContext()->setContextProperty("Flasher", &flasher);
    engine.loadFromModule("Pocketso.Flasher", "Main");

    if (engine.rootObjects().isEmpty())
        return 1;
    return app.exec();
}
