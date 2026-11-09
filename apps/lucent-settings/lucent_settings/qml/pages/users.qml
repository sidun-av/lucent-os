import QtQuick
import QtQuick.Dialogs
import QtQuick.Layouts
import Lucent

Page {
    id: page
    readonly property var st: UsersPage.s
    readonly property string busy: UsersPage.busy
    title: System.tr("Users")
    lead: System.tr("Your name, picture and password. They show on the login screen and in the Start menu.")
    Component.onCompleted: UsersPage.refresh()

    Banner { text: UsersPage.error; onDismissed: UsersPage.clearError() }

    Card {
        Layout.topMargin: Theme.sectionTop
        SettingRow {
            minHeight: 112
            label: page.st.name || ""
            labelPx: Theme.fontH2
            labelWeight: Theme.weightHeading
            sub: (page.st.admin ? System.tr("Administrator") : System.tr("Standard user")) + " · " + (page.st.login || "")
            leading: Avatar { size: 72; source: page.st.icon || ""; initials: page.st.initials || "?" }
        }
        SettingRow {
            label: System.tr("Name")
            sub: System.tr("Shown on the login screen. Your sign-in name stays “{login}”.").replace("{login}", page.st.login || "")
            LTextField {
                id: nameField
                implicitWidth: 300
                text: page.st.realName || ""
                placeholderText: page.st.login || ""
                onAccepted: UsersPage.setName(text)
            }
            LButton {
                text: System.tr("Save")
                enabled: nameField.text.trim() !== "" && nameField.text.trim() !== (page.st.realName || "")
                busy: page.busy === "name"
                onClicked: UsersPage.setName(nameField.text)
            }
        }
        SettingRow {
            label: System.tr("Picture")
            sub: System.tr("A photo, or your initials")
            LButton { text: System.tr("Use initials"); busy: page.busy === "picture"; onClicked: UsersPage.useInitials() }
            LButton { text: System.tr("Choose a photo…"); onClicked: photo.open() }
        }
        SettingRow {
            label: System.tr("Password")
            sub: System.tr("To confirm, you'll be asked for your current password.")
            LButton { text: System.tr("Change…"); busy: page.busy === "password"; onClicked: { pw1.text = ""; pw2.text = ""; pwErr.text = ""; pwDialog.open() } }
        }
    }

    GroupHeader { text: System.tr("More") }
    Card {
        SettingRow {
            label: System.tr("Other people and sign-in options")
            sub: System.tr("Add a user for someone else, automatic sign-in")
            clickable: true
            onClicked: UsersPage.openAdvanced()
            Sym { name: "right"; size: 18; color: Theme.text3 }
        }
    }

    FileDialog {
        id: photo
        title: System.tr("Choose a photo")
        nameFilters: [System.tr("Pictures") + " (*.jpg *.jpeg *.png *.webp)"]
        onAccepted: UsersPage.setPicture(selectedFile.toString())
    }
    LDialog {
        id: pwDialog
        title: System.tr("Change password")
        acceptText: System.tr("Change password")
        acceptEnabled: pw1.text.length > 0 && pw2.text.length > 0
        onAccepted: {
            var problem = UsersPage.setPassword(pw1.text, pw2.text)
            pwErr.text = problem
            if (problem === "") close()
        }
        LTextField { id: pw1; Layout.fillWidth: true; echoMode: TextInput.Password; placeholderText: System.tr("New password") }
        LTextField { id: pw2; Layout.fillWidth: true; echoMode: TextInput.Password; placeholderText: System.tr("New password again"); onAccepted: pwDialog.accepted() }
        LText { id: pwErr; visible: text !== ""; color: Theme.danger; px: Theme.fontSub; Layout.fillWidth: true; wrapMode: Text.WordWrap }
    }
}
