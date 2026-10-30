import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

ApplicationWindow {
    id: window
    width: 900
    height: 720
    minimumWidth: 650
    minimumHeight: 620
    visible: true
    title: "Pocketso Flasher"
    color: "#101410"

    property string selectedTarget: ""

    FileDialog {
        id: isoDialog
        title: "Choose a Pocketso ISO"
        nameFilters: ["ISO images (*.iso)", "All files (*)"]
        onAccepted: Flasher.setIsoPath(selectedFile.toString())
    }

    Connections {
        target: Flasher
        function onFlashFinished(success, message) {
            resultDialog.success = success
            resultDialog.message = message
            resultDialog.open()
        }
        function onDownloadFinished(success, message) {
            if (!success) {
                resultDialog.success = false
                resultDialog.message = message
                resultDialog.open()
            }
        }
    }

    Dialog {
        id: resultDialog
        modal: true
        anchors.centerIn: parent
        width: Math.min(window.width - 48, 480)
        property bool success: false
        property string message: ""
        title: success ? "USB is ready" : "Operation failed"
        standardButtons: Dialog.Ok
        Label {
            width: parent.width
            wrapMode: Text.WordWrap
            text: resultDialog.message
            color: "#e9eee8"
        }
    }

    ScrollView {
        anchors.fill: parent
        contentWidth: availableWidth
        ColumnLayout {
            width: parent.width
            spacing: 22

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 116
                color: "#171e17"
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 30
                    anchors.rightMargin: 30
                    spacing: 18
                    Rectangle {
                        width: 58; height: 58; radius: 15
                        color: "#c5f36a"
                        Text { anchors.centerIn: parent; text: "P"; color: "#111711"; font.pixelSize: 42; font.bold: true }
                    }
                    ColumnLayout {
                        spacing: 3
                        Label { text: "Pocketso Flasher"; color: "#f4f5f2"; font.pixelSize: 27; font.bold: true }
                        Label { text: "Write Pocketso Linux to a USB drive"; color: "#9ba69a"; font.pixelSize: 14 }
                    }
                    Item { Layout.fillWidth: true }
                    Label { text: "NATIVE LINUX"; color: "#c5f36a"; font.pixelSize: 11; font.bold: true }
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 30
                Layout.rightMargin: 30
                spacing: 16

                Label { text: "1. Select an image type"; color: "#c5f36a"; font.pixelSize: 17; font.bold: true }
                ComboBox {
                    id: imageTypeBox
                    Layout.fillWidth: true
                    textRole: "text"
                    valueRole: "value"
                    model: [
                        { text: "Installer ISO — installs Pocketso onto another USB", value: "installer" },
                        { text: "Pocketso Live ISO — boots the desktop without installing", value: "live" }
                    ]
                }
                Rectangle {
                    Layout.fillWidth: true
                    radius: 12
                    color: "#1a211a"
                    border.color: "#303b30"
                    implicitHeight: 100
                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 12
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Label { text: Flasher.isoPath.length ? "ISO selected" : "No ISO selected"; color: "#f4f5f2"; font.bold: true }
                            Label {
                                Layout.fillWidth: true
                                text: Flasher.isoPath.length ? Flasher.isoPath : "Choose a local ISO, or download the selected image type from the latest release."
                                color: "#9ba69a"
                                elide: Text.ElideMiddle
                            }
                        }
                        Button {
                            text: "Choose ISO"
                            onClicked: isoDialog.open()
                        }
                        Button {
                            text: "Download latest"
                            highlighted: true
                            enabled: !Flasher.busy
                            onClicked: Flasher.downloadLatest(imageTypeBox.currentValue)
                        }
                    }
                }

                Label { text: "2. Choose the destination USB"; color: "#c5f36a"; font.pixelSize: 17; font.bold: true }
                RowLayout {
                    Layout.fillWidth: true
                    ComboBox {
                        id: driveBox
                        Layout.fillWidth: true
                        model: Flasher.drives
                        textRole: "label"
                        valueRole: "path"
                        onCurrentValueChanged: window.selectedTarget = currentValue || ""
                        Component.onCompleted: if (count > 0) currentIndex = 0
                    }
                    Button {
                        text: "Refresh"
                        enabled: !Flasher.busy
                        onClicked: Flasher.refreshDrives()
                    }
                }
                Label {
                    Layout.fillWidth: true
                    visible: driveBox.count === 0
                    text: "No eligible USB drives found. Connect a USB drive and refresh. The running system disk is hidden."
                    color: "#d6ad69"
                    wrapMode: Text.WordWrap
                }

                Label { text: "3. Confirm the erase"; color: "#c5f36a"; font.pixelSize: 17; font.bold: true }
                Label {
                    Layout.fillWidth: true
                    text: "Type the exact device path shown above. All data on that USB drive will be destroyed."
                    color: "#aeb7ac"
                    wrapMode: Text.WordWrap
                }
                TextField {
                    id: confirmation
                    Layout.fillWidth: true
                    placeholderText: selectedTarget.length ? "Type " + selectedTarget + " to confirm" : "Select a USB drive first"
                    enabled: selectedTarget.length > 0 && !Flasher.busy
                    selectByMouse: true
                }

                Rectangle {
                    Layout.fillWidth: true
                    radius: 10
                    color: "#30221b"
                    border.color: "#8b5035"
                    implicitHeight: warningText.implicitHeight + 24
                    Label {
                        id: warningText
                        anchors.fill: parent
                        anchors.margins: 12
                        text: "WARNING: The selected USB drive will be completely erased. Double-check its device path and capacity before continuing."
                        color: "#f0b58f"
                        wrapMode: Text.WordWrap
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Label { text: "Writing progress"; color: "#e9eee8"; font.bold: true }
                    Item { Layout.fillWidth: true }
                    Label { text: Flasher.progress + "%"; color: "#c5f36a"; font.family: "monospace" }
                }
                ProgressBar {
                    Layout.fillWidth: true
                    from: 0; to: 100
                    value: Flasher.progress
                }

                Button {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 52
                    text: Flasher.busy ? "Please wait…" : "Flash Pocketso to USB"
                    highlighted: true
                    enabled: !Flasher.busy && Flasher.isoPath.length > 0 && selectedTarget.length > 0 && confirmation.text.trim() === selectedTarget
                    onClicked: {
                        confirmDialog.open()
                    }
                }

                Dialog {
                    id: confirmDialog
                    modal: true
                    anchors.centerIn: parent
                    width: Math.min(window.width - 48, 500)
                    title: "Erase " + window.selectedTarget + "?"
                    standardButtons: Dialog.Cancel | Dialog.Yes
                    Label {
                        width: parent.width
                        wrapMode: Text.WordWrap
                        color: "#e9eee8"
                        text: "This permanently destroys every partition and file on " + window.selectedTarget + ". Continue only if this is the correct USB drive."
                    }
                    onAccepted: Flasher.flash(window.selectedTarget, confirmation.text.trim())
                }

                Label { text: "Activity"; color: "#c5f36a"; font.pixelSize: 17; font.bold: true }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 190
                    radius: 10
                    color: "#0b0f0b"
                    border.color: "#303b30"
                    ScrollView {
                        anchors.fill: parent
                        anchors.margins: 12
                        TextArea {
                            readOnly: true
                            selectByMouse: true
                            text: Flasher.logLines.join("\n")
                            color: "#cbd5c8"
                            font.family: "monospace"
                            font.pixelSize: 12
                            wrapMode: TextEdit.Wrap
                        }
                    }
                }
            }

            Label {
                Layout.fillWidth: true
                Layout.leftMargin: 30
                Layout.rightMargin: 30
                Layout.bottomMargin: 22
                text: "Pocketso Flasher is a normal Linux executable. Administrator access is requested only for the USB-writing helper through PolicyKit."
                color: "#778276"
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
            }
        }
    }
}
