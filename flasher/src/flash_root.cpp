#include <QCoreApplication>
#include <QFileInfo>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QProcess>
#include <QSet>
#include <QTextStream>
#include <unistd.h>
#include <QRegularExpression>
#include <QStringList>

#include <cstdio>

static QString command(const QString &program, const QStringList &args, int timeout = 10000)
{
    QProcess process;
    process.start(program, args);
    if (!process.waitForFinished(timeout) || process.exitStatus() != QProcess::NormalExit || process.exitCode() != 0)
        return {};
    return QString::fromLocal8Bit(process.readAllStandardOutput()).trimmed();
}

static int fail(const QString &message, int code = 2)
{
    QTextStream(stderr) << "ERROR: " << message << Qt::endl;
    return code;
}

static QStringList disksForSource(const QString &source)
{
    if (source.isEmpty()) return {};
    const QString out = command("lsblk", {"-s", "-n", "-p", "-o", "NAME,TYPE", source.section('[', 0, 0)});
    QStringList disks;
    for (const QString &line : out.split('\n', Qt::SkipEmptyParts)) {
        const QStringList parts = line.simplified().split(' ');
        if (parts.size() == 2 && parts.at(1) == "disk")
            disks << QFileInfo(parts.at(0)).canonicalFilePath();
    }
    return disks;
}

int main(int argc, char *argv[])
{
    QCoreApplication app(argc, argv);
    if (geteuid() != 0) return fail("Administrator authorization is required.");
    if (argc != 4) return fail("Invalid arguments.");

    const QString iso = QFileInfo(QString::fromLocal8Bit(argv[1])).canonicalFilePath();
    const QString targetInput = QString::fromLocal8Bit(argv[2]);
    const QString confirmation = QString::fromLocal8Bit(argv[3]);
    if (iso.isEmpty() || !QFileInfo(iso).isFile() || !iso.endsWith(".iso", Qt::CaseInsensitive))
        return fail("ISO file is missing or invalid.");
    if (targetInput != confirmation || !targetInput.startsWith("/dev/"))
        return fail("Device path confirmation does not match.");

    const QString target = QFileInfo(targetInput).canonicalFilePath();
    const QJsonDocument diskJson = QJsonDocument::fromJson(command("lsblk", {"-J", "-b", "-d", "-o", "NAME,PATH,TYPE,SIZE,TRAN,RM,RO", target}).toUtf8());
    const QJsonArray devices = diskJson.object().value("blockdevices").toArray();
    if (devices.size() != 1) return fail("Could not identify exactly one target disk.");
    const QJsonObject disk = devices.first().toObject();
    if (disk.value("type").toString() != "disk") return fail("Select a whole USB disk, not a partition.");
    const QString transport = disk.value("tran").toString();
    const bool removable = disk.value("rm").toVariant().toString() == "1" || disk.value("rm").toBool();
    const bool readOnly = disk.value("ro").toVariant().toString() == "1" || disk.value("ro").toBool();
    if (transport != "usb" && !removable) return fail("Safety block: target is not identified as USB/removable.");
    if (readOnly) return fail("Target disk is read-only.");

    QSet<QString> protectedDisks;
    const QStringList mounts = {"/", "/boot", "/boot/efi", "/efi", "/home", "/var", "/usr", "/opt", "/srv", "/run/archiso/bootmnt"};
    for (const QString &mount : mounts) {
        const QString source = command("findmnt", {"-n", "-r", "-o", "SOURCE", mount});
        for (const QString &device : disksForSource(source)) protectedDisks.insert(device);
    }
    if (protectedDisks.contains(target)) return fail("Safety block: refusing to overwrite the running system disk.");

    bool sizeOk = false;
    const qint64 diskSize = disk.value("size").toVariant().toLongLong(&sizeOk);
    const qint64 isoSize = QFileInfo(iso).size();
    if (!sizeOk || isoSize <= 0 || isoSize > diskSize) return fail("ISO does not fit on the selected USB drive.");

    QTextStream(stdout) << "Target: " << target << " (" << diskSize << " bytes)" << Qt::endl;
    QTextStream(stdout) << "Unmounting partitions on the USB drive…" << Qt::endl;
    const QStringList names = command("lsblk", {"-lnpo", "NAME", target}).split('\n', Qt::SkipEmptyParts);
    for (int i = 1; i < names.size(); ++i) {
        QProcess unmount;
        unmount.start("umount", {names.at(i)});
        unmount.waitForFinished(10000);
    }
    const QString mountPoints = command("lsblk", {"-nrpo", "MOUNTPOINT", target});
    if (!mountPoints.isEmpty()) return fail("One or more USB partitions remain mounted; no data was written.");

    QTextStream(stdout) << "Writing ISO. Do not unplug the USB drive." << Qt::endl;
    QProcess writer;
    writer.setProgram("dd");
    writer.setReadChannel(QProcess::StandardError);
    writer.setArguments({"if=" + iso, "of=" + target, "bs=4M", "status=progress", "conv=fsync"});
    writer.start();
    if (!writer.waitForStarted(5000)) return fail("Could not start dd.");
    QByteArray pending;
    while (writer.state() != QProcess::NotRunning) {
        writer.waitForReadyRead(250);
        pending += writer.readAllStandardError();
        int split = -1;
        while ((split = pending.indexOf('\r')) >= 0 || (split = pending.indexOf('\n')) >= 0) {
            const QByteArray line = pending.left(split).trimmed();
            pending.remove(0, split + 1);
            if (line.isEmpty()) continue;
            QTextStream(stdout) << line << Qt::endl;
            static const QRegularExpression bytesPattern("^(\\d+)\\s+bytes");
            const auto match = bytesPattern.match(QString::fromLocal8Bit(line));
            if (match.hasMatch()) {
                const qint64 written = match.captured(1).toLongLong();
                const int percent = qBound(0, static_cast<int>(written * 100 / isoSize), 100);
                QTextStream(stdout) << "PROGRESS " << percent << Qt::endl;
            }
        }
    }
    writer.waitForFinished(-1);
    pending += writer.readAllStandardError();
    if (writer.exitStatus() != QProcess::NormalExit || writer.exitCode() != 0)
        return fail(QString("dd failed: %1").arg(QString::fromLocal8Bit(pending)), writer.exitCode() ? writer.exitCode() : 1);

    QProcess sync;
    sync.start("sync");
    if (!sync.waitForFinished(-1) || sync.exitCode() != 0) return fail("sync failed after writing the ISO.", 1);
    QTextStream(stdout) << "SUCCESS: ISO written and disk cache synchronized." << Qt::endl;
    return 0;
}
