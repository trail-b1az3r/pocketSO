#pragma once

#include <QObject>
#include <QVariantList>
#include <QStringList>
#include <QProcess>
#include <QNetworkAccessManager>
#include <QSaveFile>
#include <QPointer>

class QNetworkReply;

class FlasherBackend final : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QVariantList drives READ drives NOTIFY drivesChanged)
    Q_PROPERTY(QString isoPath READ isoPath NOTIFY isoPathChanged)
    Q_PROPERTY(int progress READ progress NOTIFY progressChanged)
    Q_PROPERTY(bool busy READ busy NOTIFY busyChanged)
    Q_PROPERTY(QStringList logLines READ logLines NOTIFY logChanged)

public:
    explicit FlasherBackend(QObject *parent = nullptr);

    QVariantList drives() const { return m_drives; }
    QString isoPath() const { return m_isoPath; }
    int progress() const { return m_progress; }
    bool busy() const { return m_busy; }
    QStringList logLines() const { return m_logLines; }

    Q_INVOKABLE void refreshDrives();
    Q_INVOKABLE void setIsoPath(const QString &path);
    Q_INVOKABLE void downloadLatest();
    Q_INVOKABLE void flash(const QString &target, const QString &confirmation);
    Q_INVOKABLE void clearLog();

signals:
    void drivesChanged();
    void isoPathChanged();
    void progressChanged();
    void busyChanged();
    void logChanged();
    void flashFinished(bool success, const QString &message);
    void downloadFinished(bool success, const QString &message);

private:
    void appendLog(const QString &line);
    void setBusy(bool value);
    void setProgress(int value);
    QString helperPath() const;

    QVariantList m_drives;
    QString m_isoPath;
    int m_progress = 0;
    bool m_busy = false;
    QStringList m_logLines;
    QNetworkAccessManager m_network;
    QPointer<QNetworkReply> m_downloadReply;
    QSaveFile m_downloadOutput;
    QProcess m_flashProcess;
    QString m_flashBuffer;
};
