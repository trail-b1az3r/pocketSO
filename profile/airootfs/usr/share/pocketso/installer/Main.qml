import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

ApplicationWindow {
    id: window
    visible: true
    width: 940
    height: 760
    minimumWidth: 760
    minimumHeight: 650
    title: "Pocketso USB Installer"
    color: "#10141d"

    property string selectedDrive: ""
    property var driveItems: []
    property bool installing: false

    Connections {
        target: installer
        function onDrivesChanged(payload) {
            window.driveItems = JSON.parse(payload)
            driveBox.currentIndex = -1
            window.selectedDrive = ""
        }
        function onLogLine(line) {
            logArea.text += line + "\n"
            logArea.cursorPosition = logArea.length
            statusText.text = line
        }
        function onInstallFinished(message) {
            statusText.text = message
            resultDialog.title = "Installation complete"
            resultDialog.text = message
            resultDialog.open()
        }
        function onInstallFailed(message) {
            statusText.text = message
            errorDialog.text = message
            errorDialog.open()
        }
        function onBusyChanged(value) {
            window.installing = value
        }
    }

    Dialog {
        id: resultDialog
        modal: true
        anchors.centerIn: parent
        width: Math.min(window.width - 48, 560)
        title: "Installation complete"
        standardButtons: Dialog.Ok
        property string text: ""
        contentItem: Label { text: resultDialog.text; wrapMode: Text.WordWrap; color: "#e6edf7" }
    }
    Dialog {
        id: errorDialog
        modal: true
        anchors.centerIn: parent
        width: Math.min(window.width - 48, 560)
        title: "Cannot continue"
        standardButtons: Dialog.Ok
        property string text: ""
        contentItem: Label { text: errorDialog.text; wrapMode: Text.WordWrap; color: "#e6edf7" }
    }

    ScrollView {
        anchors.fill: parent
        anchors.margins: 24
        clip: true

        ColumnLayout {
            width: Math.max(implicitWidth, window.width - 72)
            spacing: 18

            RowLayout {
                Layout.fillWidth: true
                spacing: 14
                Rectangle {
                    width: 54; height: 54; radius: 14
                    color: "#25334a"
                    Label { anchors.centerIn: parent; text: "P"; color: "#8ec5ff"; font.pixelSize: 30; font.bold: true }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    Label { text: "Pocketso USB Installer"; color: "#f4f7fb"; font.pixelSize: 26; font.bold: true }
                    Label { text: "Install a persistent Pocketso system onto a separate USB drive"; color: "#9eacc0"; font.pixelSize: 13 }
                }
                Button { text: "Refresh drives"; enabled: !window.installing; onClicked: installer.refreshDrives() }
            }

            Rectangle {
                Layout.fillWidth: true
                radius: 12
                color: "#392a1b"
                border.color: "#8d6330"
                implicitHeight: warningText.implicitHeight + 28
                Label {
                    id: warningText
                    anchors.fill: parent
                    anchors.margins: 14
                    wrapMode: Text.WordWrap
                    color: "#ffd9a3"
                    text: "WARNING: The selected USB drive will be completely erased. The installer USB and detected internal system disks are excluded. Back up the destination before continuing. A separate drive of at least 30 GB is required."
                }
            }

            GroupBox {
                Layout.fillWidth: true
                title: "1. Destination drive"
                label: Label { text: parent.title; color: "#c5d5e9"; font.bold: true }
                background: Rectangle { color: "#171e2a"; radius: 12; border.color: "#2c394d" }
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 8
                    ComboBox {
                        id: driveBox
                        Layout.fillWidth: true
                        textRole: "label"
                        valueRole: "path"
                        model: window.driveItems
                        enabled: !window.installing
                        onActivated: {
                            window.selectedDrive = window.driveItems[currentIndex].path
                            confirmField.text = ""
                        }
                    }
                    Label {
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        color: "#94a5bc"
                        text: window.driveItems.length === 0
                              ? "No eligible USB drives found. Connect a second USB drive (30 GB or larger), then refresh."
                              : "Only USB/removable drives are listed. The installer source drive is filtered out."
                    }
                    Label { text: "Type the exact device path to confirm erasure:"; color: "#c5d5e9" }
                    TextField {
                        id: confirmField
                        Layout.fillWidth: true
                        placeholderText: window.selectedDrive || "/dev/sdX"
                        enabled: !window.installing && window.selectedDrive.length > 0
                        selectByMouse: true
                    }
                }
            }

            GroupBox {
                Layout.fillWidth: true
                title: "2. Pocketso setup"
                label: Label { text: parent.title; color: "#c5d5e9"; font.bold: true }
                background: Rectangle { color: "#171e2a"; radius: 12; border.color: "#2c394d" }
                GridLayout {
                    anchors.fill: parent
                    columns: 2
                    columnSpacing: 18
                    rowSpacing: 10
                    Label { text: "Desktop environment"; color: "#c5d5e9" }
                    ComboBox {
                        id: desktopBox
                        Layout.fillWidth: true
                        model: [
                            { text: "MATE (lighter)", value: "mate" },
                            { text: "KDE Plasma", value: "kde" },
                            { text: "Both MATE and KDE", value: "both" }
                        ]
                        textRole: "text"
                        valueRole: "value"
                        enabled: !window.installing
                    }
                    Label { text: "Username"; color: "#c5d5e9" }
                    TextField {
                        id: usernameField
                        Layout.fillWidth: true
                        text: "pocketso"
                        placeholderText: "lowercase username"
                        enabled: !window.installing
                    }
                    Label { text: "Password"; color: "#c5d5e9" }
                    TextField {
                        id: passwordField
                        Layout.fillWidth: true
                        echoMode: TextInput.Password
                        placeholderText: "10+ characters; no colon"
                        enabled: !window.installing
                    }
                    Label { text: "Confirm password"; color: "#c5d5e9" }
                    TextField {
                        id: passwordConfirmField
                        Layout.fillWidth: true
                        echoMode: TextInput.Password
                        placeholderText: "Enter the password again"
                        enabled: !window.installing
                    }
                }
            }

            GroupBox {
                Layout.fillWidth: true
                title: "3. Install"
                label: Label { text: parent.title; color: "#c5d5e9"; font.bold: true }
                background: Rectangle { color: "#171e2a"; radius: 12; border.color: "#2c394d" }
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 10
                    Label {
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        color: "#9eacc0"
                        text: "Requires an internet connection to download Arch packages. The installer creates a GPT layout, installs a persistent ext4 system, and configures GRUB for BIOS and UEFI without modifying host firmware NVRAM."
                    }
                    Button {
                        Layout.fillWidth: true
                        text: window.installing ? "Installing Pocketso…" : "Erase drive and install Pocketso"
                        enabled: !window.installing && window.selectedDrive.length > 0
                                 && confirmField.text === window.selectedDrive
                                 && passwordField.text.length >= 10
                                 && passwordField.text === passwordConfirmField.text
                        highlighted: true
                        onClicked: {
                            installer.startInstall(
                                window.selectedDrive,
                                desktopBox.currentValue,
                                usernameField.text,
                                passwordField.text,
                                passwordConfirmField.text,
                                confirmField.text
                            )
                            passwordField.text = ""
                            passwordConfirmField.text = ""
                        }
                    }
                    ProgressBar {
                        Layout.fillWidth: true
                        indeterminate: window.installing
                        visible: window.installing
                    }
                    Label {
                        id: statusText
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        color: "#a8c8ef"
                        text: "Ready. Select a destination drive to begin."
                    }
                }
            }

            GroupBox {
                Layout.fillWidth: true
                title: "Installer log"
                label: Label { text: parent.title; color: "#c5d5e9"; font.bold: true }
                background: Rectangle { color: "#171e2a"; radius: 12; border.color: "#2c394d" }
                TextArea {
                    id: logArea
                    width: parent.width
                    readOnly: true
                    wrapMode: TextEdit.Wrap
                    color: "#c8d5e6"
                    selectedTextColor: "#ffffff"
                    selectionColor: "#365b87"
                    background: Rectangle { color: "#0c1119"; radius: 8 }
                    text: "Drive detection ready.\n"
                }
            }
        }
    }
}
