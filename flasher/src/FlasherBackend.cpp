#include "FlasherBackend.h"

#include <QCoreApplication>
#include <QDir>
#include <QFileInfo>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QNetworkReply>
#include <QNetworkRequest>
#include <QProcessEnvironment>
#include <QStandardPaths>
#include <QUrl>
#include <QSaveFile>
#include <QSet>

namespace {
QString runCommand(const QString &program, const QStringList &args)
{
    QProcess process;
    process.start(program, args);
    if (!process.waitForFinished(5000) || process.exitStatus() != QProcess::NormalExit || process.exitCode() != 0)
        return {};
    return QString::fromLocal8Bit(process.readAllStandardOutput()).trimmed();
}

QString canonical(const QString &path)
{
    const QString result = QFileInfo(path).canonicalFilePath();
    return result.isEmpty() ? path : result;
}

QStringList disksForSource(const QString &source)
{
    if (source.isEmpty())
        return {};
    const QString output = runCommand("lsblk", {"-s", "-n", "-p", "-o", "NAME,TYPE", source.section('[', 0, 0)});
    QStringList disks;
    for (const QString &line : output.split('\n', Qt::SkipEmptyParts)) {
        const QStringList parts = line.simplified().split(' ');
        if (parts.size() == 2 && parts.at(1) == "disk")
            disks << canonical(parts.at(0));
    }
    return disks;
}
}

FlasherBackend::FlasherBackend(QObject *parent)
    : QObject(parent)
{
    connect(&m_flashProcess, &QProcess::readyReadStandardOutput, this, [this] {
        const QString chunk = QString::fromLocal8Bit(m_flashProcess.readAllStandardOutput());
        m_flashBuffer += chunk;
        while (m_flashBuffer.contains('\n')) {
            const int end = m_flashBuffer.indexOf('\n');
            const QString line = m_flashBuffer.left(end).trimmed();
            m_flashBuffer.remove(0, end + 1);
            if (line.startsWith("PROGRESS ")) {
                bool ok = false;
                const int value = line.mid(9).toInt(&ok);
                if (ok) setProgress(qBound(0, value, 100));
            } else if (!line.isEmpty()) {
                appendLog(line);
            }
        }
    });
    connect(&m_flashProcess, &QProcess::readyReadStandardError, this, [this] {
        const QString text = QString::fromLocal8Bit(m_flashProcess.readAllStandardError()).trimmed();
        if (!text.isEmpty()) appendLog(text);
    });
    connect(&m_flashProcess, qOverload<int, QProcess::ExitStatus>(&QProcess::finished),
            this, [this](int code, QProcess::ExitStatus status) {
        const QString tail = m_flashBuffer.trimmed();
        if (!tail.isEmpty()) appendLog(tail);
        m_flashBuffer.clear();
        setBusy(false);
        const bool ok = status == QProcess::NormalExit && code == 0;
        const QString message = ok
            ? "The ISO was written and synchronized. Safely eject the USB before booting."
            : QString("Flashing failed or authorization was cancelled (exit code %1).").arg(code);
        appendLog(message);
        emit flashFinished(ok, message);
        refreshDrives();
    });
    refreshDrives();
}

void FlasherBackend::appendLog(const QString &line)
{
    m_logLines.append(line);
    while (m_logLines.size() > 500) m_logLines.removeFirst();
    emit logChanged();
}

void FlasherBackend::setBusy(bool value)
{
    if (m_busy == value) return;
    m_busy = value;
    emit busyChanged();
}

void FlasherBackend::setProgress(int value)
{
    if (m_progress == value) return;
    m_progress = value;
    emit progressChanged();
}

void FlasherBackend::clearLog()
{
    m_logLines.clear();
    emit logChanged();
}

void FlasherBackend::setIsoPath(const QString &path)
{
    const QString local = QUrl(path).isLocalFile() ? QUrl(path).toLocalFile() : path;
    if (!QFileInfo(local).isFile() || !local.endsWith(".iso", Qt::CaseInsensitive)) {
        appendLog("Choose a valid local ISO file.");
        return;
    }
    m_isoPath = QFileInfo(local).absoluteFilePath();
    emit isoPathChanged();
    setProgress(0);
    appendLog("ISO selected: " + m_isoPath);
}

void FlasherBackend::refreshDrives()
{
    const QByteArray raw = runCommand("lsblk", {"-J", "-b", "-p", "-o", "NAME,TYPE,SIZE,TRAN,RM,MODEL,SERIAL,RO"}).toUtf8();
    const QJsonDocument document = QJsonDocument::fromJson(raw);
    if (!document.isObject()) {
        appendLog("Could not read block-device information. Is util-linux (lsblk) installed?");
        return;
    }

    QSet<QString> protectedDisks;
    const QStringList mounts = {"/", "/boot", "/boot/efi", "/efi", "/home", "/var", "/usr", "/opt", "/srv", "/run/archiso/bootmnt"};
    for (const QString &mount : mounts) {
        const QString source = runCommand("findmnt", {"-n", "-r", "-o", "SOURCE", mount}).section('[', 0, 0);
        for (const QString &disk : disksForSource(source))
            protectedDisks.insert(disk);
    }

    QVariantList found;
    const QJsonArray devices = document.object().value("blockdevices").toArray();
    for (const QJsonValue &value : devices) {
        const QJsonObject item = value.toObject();
        const QString path = item.value("name").toString();
        const QString realPath = canonical(path);
        const QString type = item.value("type").toString();
        const QString transport = item.value("tran").toString();
        const bool removable = item.value("rm").toVariant().toString() == "1" || item.value("rm").toBool();
        const bool readOnly = item.value("ro").toVariant().toString() == "1" || item.value("ro").toBool();
        if (type != "disk" || path.isEmpty() || protectedDisks.contains(realPath) ||
            (transport != "usb" && !removable) || readOnly)
            continue;

        const double gib = item.value("size").toVariant().toDouble() / (1024.0 * 1024.0 * 1024.0);
        QString label = QString("%1  |  %2 GiB  |  %3")
            .arg(path).arg(gib, 0, 'f', 1)
            .arg(item.value("model").toString().trimmed().isEmpty() ? "USB drive" : item.value("model").toString().trimmed());
        const QString serial = item.value("serial").toString().trimmed();
        if (!serial.isEmpty()) label += "  |  " + serial;
        found.append(QVariantMap{{"path", path}, {"label", label}});
    }
    m_drives = found;
    emit drivesChanged();
}

QString FlasherBackend::helperPath() const
{
    const QString overridePath = qEnvironmentVariable("POCKETSO_FLASH_HELPER");
    if (!overridePath.isEmpty() && QFileInfo::exists(overridePath)) return overridePath;

    const QString appDir = QCoreApplication::applicationDirPath();
    const QStringList candidates = {
        QDir(appDir).filePath("../libexec/pocketso-flash-root"),
        QDir(appDir).filePath("pocketso-flash-root"),
        "/usr/libexec/pocketso-flash-root",
        "/usr/local/libexec/pocketso-flash-root"
    };
    for (const QString &path : candidates)
        if (QFileInfo(path).isExecutable()) return QFileInfo(path).canonicalFilePath();
    return {};
}

void FlasherBackend::downloadLatest()
{
    if (m_busy || m_downloadReply) return;
    setBusy(true);
    setProgress(0);
    appendLog("Checking the latest Pocketso GitHub release…");

    QNetworkRequest request(QUrl("https://api.github.com/repos/trail-b1az3r/pocketSO/releases/latest"));
    request.setHeader(QNetworkRequest::UserAgentHeader, "Pocketso-Flasher");
    request.setRawHeader("Accept", "application/vnd.github+json");
    m_downloadReply = m_network.get(request);

    connect(m_downloadReply, &QNetworkReply::finished, this, [this] {
        QNetworkReply *reply = m_downloadReply;
        m_downloadReply = nullptr;
        if (!reply) { setBusy(false); return; }
        const QByteArray body = reply->readAll();
        if (reply->error() != QNetworkReply::NoError) {
            const QString message = reply->errorString();
            reply->deleteLater();
            setBusy(false);
            appendLog("Release lookup failed: " + message);
            emit downloadFinished(false, message);
            return;
        }
        const QJsonDocument json = QJsonDocument::fromJson(body);
        QString assetUrl, assetName;
        for (const QJsonValue &assetValue : json.object().value("assets").toArray()) {
            const QJsonObject asset = assetValue.toObject();
            const QString name = asset.value("name").toString();
            if (name.endsWith(".iso", Qt::CaseInsensitive)) {
                assetName = name;
                assetUrl = asset.value("browser_download_url").toString();
                break;
            }
        }
        reply->deleteLater();
        if (assetUrl.isEmpty()) {
            setBusy(false);
            const QString message = "The latest GitHub release has no ISO asset yet. Choose a local ISO or publish an ISO release.";
            appendLog(message);
            emit downloadFinished(false, message);
            return;
        }

        const QString downloads = QStandardPaths::writableLocation(QStandardPaths::DownloadLocation);
        QDir().mkpath(downloads);
        const QString destination = QDir(downloads).filePath(assetName);
        appendLog("Downloading " + assetName + "…");
        QNetworkRequest fileRequest{QUrl(assetUrl)};
        fileRequest.setHeader(QNetworkRequest::UserAgentHeader, "Pocketso-Flasher");
        m_downloadOutput.setFileName(destination);
        if (!m_downloadOutput.open(QIODevice::WriteOnly)) {
            setBusy(false);
            const QString message = "Could not create the ISO download file: " + destination;
            appendLog(message);
            emit downloadFinished(false, message);
            return;
        }
        QNetworkReply *fileReply = m_network.get(fileRequest);
        connect(fileReply, &QNetworkReply::readyRead, this, [this, fileReply] {
            const QByteArray chunk = fileReply->readAll();
            if (m_downloadOutput.write(chunk) != chunk.size()) {
                appendLog("Could not write the ISO download to disk.");
                fileReply->abort();
            }
        });
        connect(fileReply, &QNetworkReply::downloadProgress, this, [this](qint64 received, qint64 total) {
            if (total > 0) setProgress(static_cast<int>(received * 100 / total));
        });
        connect(fileReply, &QNetworkReply::finished, this, [this, fileReply, destination] {
            const QByteArray remaining = fileReply->readAll();
            if (!remaining.isEmpty() && m_downloadOutput.write(remaining) != remaining.size())
                fileReply->abort();
            const auto error = fileReply->error();
            const QString errorText = fileReply->errorString();
            fileReply->deleteLater();
            if (error != QNetworkReply::NoError || !m_downloadOutput.commit()) {
                m_downloadOutput.cancelWriting();
                setBusy(false);
                const QString message = error != QNetworkReply::NoError ? errorText : "Could not finalize the ISO file.";
                appendLog("Download failed: " + message);
                emit downloadFinished(false, message);
                return;
            }
            m_isoPath = destination;
            emit isoPathChanged();
            setProgress(100);
            setBusy(false);
            appendLog("Download complete: " + destination);
            emit downloadFinished(true, destination);
        });
    });
}

void FlasherBackend::flash(const QString &target, const QString &confirmation)
{
    if (m_busy || m_flashProcess.state() != QProcess::NotRunning) return;
    if (m_isoPath.isEmpty() || !QFileInfo(m_isoPath).isFile()) {
        emit flashFinished(false, "Choose or download a Pocketso ISO first.");
        return;
    }
    if (target.isEmpty() || confirmation.trimmed() != target) {
        emit flashFinished(false, "Type the exact selected USB device path to confirm.");
        return;
    }
    const QString helper = helperPath();
    const QString pkexec = QStandardPaths::findExecutable("pkexec");
    if (helper.isEmpty()) {
        emit flashFinished(false, "The C++ USB writer helper is missing. Reinstall Pocketso Flasher with its libexec helper.");
        return;
    }
    if (pkexec.isEmpty()) {
        emit flashFinished(false, "PolicyKit (pkexec) is not installed. Install polkit and a desktop PolicyKit authentication agent.");
        return;
    }

    setBusy(true);
    setProgress(0);
    appendLog("Requesting administrator authorization. Only the selected USB will be erased.");
    m_flashProcess.setProgram(pkexec);
    m_flashProcess.setArguments({helper, m_isoPath, target, confirmation});
    m_flashProcess.start();
    if (!m_flashProcess.waitForStarted(5000)) {
        setBusy(false);
        const QString message = "Could not start pkexec: " + m_flashProcess.errorString();
        appendLog(message);
        emit flashFinished(false, message);
    }
}
