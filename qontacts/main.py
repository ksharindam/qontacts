#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This file is a part of Qontacts Program which is GNU GPLv3 licensed
# Copyright (C) 2026 Arindam Chaudhuri <arindamsoft94@gmail.com>
import os, sys
import platform
 # enable python 2 like import
sys.path.append(os.path.dirname(__file__))

from PyQt5.QtCore import qVersion, Qt, QSize, QBuffer, QIODevice, pyqtSignal, QStandardPaths
from PyQt5.QtGui import QIcon, QImage, QPixmap, QPainter

from PyQt5.QtWidgets import (QApplication, QStyleFactory, QMainWindow, QStatusBar, QDialog, QDialogButtonBox, QWidget, QLabel, QVBoxLayout,
    QGridLayout, QToolButton, QScrollArea, QHBoxLayout, QSizePolicy, QStyleOption,
    QStyle, QLineEdit, QMenu, QFileDialog, QMessageBox
)
from __init__ import __version__, COPYRIGHT_YEAR, AUTHOR_NAME, AUTHOR_EMAIL
from vcard import vCard, Contact
import resources_rc

# container for global variables
class App:
    DATA_DIR = "~/.local/share/Qontacts" # overridden on app start
    profile_pixmap = None
    contacts = []


# this function must be called after calling QApplication.setApplicationName()
def updatePaths():
    App.DATA_DIR = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Qontacts v{__version__}")
        self.setWindowIcon(QIcon(":/icons/qontacts.png"))
        self.resize(450,680)
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.statusbar = QStatusBar(self)
        self.setStatusBar(self.statusbar)

        # toolbar
        self.toolbarLayout = QHBoxLayout()
        self.toolbarLayout.setContentsMargins(0,0,0,0)
        # Menu Button
        self.menuBtn = QToolButton(self.central_widget)
        self.menuBtn.setIcon(QIcon(":/icons/menu.png"))
        self.menuBtn.setIconSize(QSize(22,22))
        self.menuBtn.setToolTip("Main Menu")
        self.menuBtn.setPopupMode(QToolButton.InstantPopup)
        menu = QMenu(self.menuBtn)
        menu.addAction(QIcon(":/icons/help-about.png"), "About", self.showAbout)
        self.menuBtn.setMenu(menu)
        # add contact button
        self.addContactBtn = QToolButton(self.central_widget)
        self.addContactBtn.setIcon(QIcon(":/icons/add.png"))
        self.addContactBtn.setIconSize(QSize(22,22))
        self.addContactBtn.setToolTip("New Contact")
        # search box
        self.searchbox = QLineEdit(self.central_widget)
        self.searchbox.setPlaceholderText("Search Contacts...")
        # quit button
        self.quitBtn = QToolButton(self.central_widget)
        self.quitBtn.setIcon(QIcon(":/icons/quit.png"))
        self.quitBtn.setIconSize(QSize(22,22))
        self.quitBtn.setToolTip("Quit")
        # add widgets to layout
        self.toolbarLayout.addWidget(self.menuBtn)
        self.toolbarLayout.addWidget(self.addContactBtn)
        self.toolbarLayout.addWidget(self.searchbox)
        self.toolbarLayout.addWidget(self.quitBtn)
        # contacts scroll area
        self.scrollArea = QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidget = QWidget(self.scrollArea)
        self.scrollArea.setWidget(self.scrollAreaWidget)
        self.scrollAreaLayout = QHBoxLayout(self.scrollAreaWidget)

        self.layout.addLayout(self.toolbarLayout)
        self.layout.addWidget(self.scrollArea)

        self.addContactBtn.clicked.connect(self.addNewContact)
        self.quitBtn.clicked.connect(self.close)
        self.searchbox.textEdited.connect(self.searchText)
        # show main window
        self.show()
        self.searchbox.setFocus()

        if not os.path.exists(App.DATA_DIR):
            os.makedirs(App.DATA_DIR)
        self.contacts_filename = App.DATA_DIR + "/contacts.vcf"
        try:
            reader = vCard()
            App.contacts = reader.read_file(self.contacts_filename)
        except:
            pass
        # init some variables
        self.contactsContainer = None
        self.selected_widgets = []
        icon = QPixmap(":/icons/qontacts.png")
        App.profile_pixmap = icon.scaled(64,64, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        # display contacts
        App.contacts.sort(key=lambda c: c.name)
        self.showContacts()

    def showContacts(self, contact_indices=None):
        if not contact_indices:# show all
            contact_indices = [i for i in range(len(App.contacts))]
        # remove previous contact widgets
        self.clearContactWidgets()

        self.contactsContainer = QWidget(self.scrollAreaWidget)
        self.scrollAreaLayout.addWidget(self.contactsContainer)

        self.contactsLayout = QVBoxLayout(self.contactsContainer)

        for index in contact_indices:
            item = ContactWidget(index, self.contactsContainer)
            self.contactsLayout.addWidget(item)
            item.editRequested.connect(self.onEditRequested)
            item.deleteRequested.connect(self.onDeleteRequested)
        self.contactsLayout.addStretch()

        self.statusbar.showMessage("Showing %d contacts"%len(contact_indices))

    def contact_widgets(self):
        items = [self.contactsLayout.itemAt(i).widget() for i in range(self.contactsLayout.count())]
        return list(filter(lambda x : isinstance(x, ContactWidget), items))

    def clearContactWidgets(self):
        if not self.contactsContainer:
            return
        self.scrollAreaLayout.removeWidget(self.contactsContainer)
        self.contactsContainer.deleteLater()
        self.contactsContainer = None
        self.selected_widgets.clear()

    def addNewContact(self):
        dlg = ContactEditDialog(self)
        if dlg.exec()==dlg.Accepted:
            contact = dlg.get_contact()
            writer = vCard()
            writer.write_contact(self.contacts_filename, contact)
            App.contacts.append(contact)
            App.contacts.sort(key=lambda c: c.name)
            self.showContacts()

    def onEditRequested(self, contact_widget):
        contact = App.contacts[contact_widget.index]
        dlg = ContactEditDialog(self, contact)
        if dlg.exec()==QDialog.Accepted:
            App.contacts[contact_widget.index] = dlg.get_contact()
            contact_widget.update()
            self.save_all_contacts()

    def onDeleteRequested(self, contact_widget):
        self.selected_widgets = [contact_widget]
        self.delete_selected()

    def delete_selected(self):
        deleted_indices = []
        for contact_widget in self.selected_widgets:
            deleted_indices.append(contact_widget.index)
            self.contactsLayout.removeWidget(contact_widget)
            contact_widget.deleteLater()
        self.selected_widgets.clear()
        # delete from last to first
        deleted_indices.sort(reverse=True)
        for index in deleted_indices:
            App.contacts.pop(index)

        # update indices after deletion
        contact_widgets = self.contact_widgets()
        contact_widgets.sort(key=lambda x:x.index, reverse=True)
        offset = len(deleted_indices)
        new_index = {}
        for widget in contact_widgets:
            while deleted_indices and deleted_indices[0]>=widget.index:
                deleted_indices.pop(0)
                offset -= 1
            if not deleted_indices:
                break
            widget.index -= offset
        self.save_all_contacts()

    def save_all_contacts(self):
        writer = vCard()
        os.remove(self.contacts_filename)
        for contact in App.contacts:
            writer.write_contact(self.contacts_filename, contact)

    def searchText(self, text):
        text = text.lower()
        if not text:
            self.showContacts()
            return
        elif len(text)<3:
            return
        contacts = [(contact,i) for i,contact in enumerate(App.contacts)]
        contacts = list(filter(lambda x : text in x[0].name.lower(), contacts))
        if not contacts:
            self.clearContactWidgets()
            self.statusbar.showMessage("No result found !")
            return
        contacts.sort(key=lambda x : x[0].name.lower().find(text))
        self.showContacts([x[1] for x in contacts])

    def showAbout(self):
        lines = ("<h1>Qontacts</h1>",
            "Simple Contacts Manager<br><br>",
            "Version : %s<br>" % __version__,
            "Qt : %s<br>" % qVersion(),
            "Copyright &copy; %s %s &lt;%s&gt;" % (COPYRIGHT_YEAR, AUTHOR_NAME, AUTHOR_EMAIL))
        QMessageBox.about(self, "About Qontacts", "".join(lines))



class ContactWidget(QWidget):
    editRequested = pyqtSignal(QWidget)
    deleteRequested = pyqtSignal(QWidget)

    def __init__(self, contact_index, parent):
        self.index = contact_index
        QWidget.__init__(self, parent)
        self.setStyleSheet("ContactWidget{background-color: white;}")
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        # add widgets
        layout = QGridLayout(self)
        self.photo = QLabel(self)
        self.photo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.name = QLabel(self)
        self.name.setStyleSheet("QLabel { color: #0000ff;}")
        self.data_widget = QWidget(self)
        self.data_layout = QGridLayout(self.data_widget)
        self.data_layout.setContentsMargins(0,0,0,0)
        #self.data_widgets = []
        # buttons
        self.editBtn = QToolButton(self)
        self.editBtn.setIcon(QIcon(":/icons/edit.png"))
        self.deleteBtn = QToolButton(self)
        self.deleteBtn.setIcon(QIcon(":/icons/delete.png"))
        # add to layout
        layout.addWidget(self.photo, 0,0,2,1)
        layout.addWidget(self.name, 0,1,1,1)
        layout.addWidget(self.editBtn, 0,2,1,1)
        layout.addWidget(self.deleteBtn, 0,3,1,1)
        layout.addWidget(self.data_widget, 1,1,1,3)
        # connect signals
        self.editBtn.clicked.connect(self.edit)
        self.deleteBtn.clicked.connect(self.delete)

        self.update()

    def update(self):
        # remove previous data widgets
        while self.data_layout.count():
            widget = self.data_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        contact = App.contacts[self.index]
        # name
        self.name.setText(contact.name)
        # contact details
        phones = [[v,k] for k,v in contact.phones.items()]
        emails = [["Email",email] for email in contact.emails]
        for i, row in enumerate(phones+emails):
            icon_label = QLabel(self.data_widget)
            icon_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            icon_label.setPixmap(QPixmap(":/icons/%s.png"%row[0].lower()))
            val_label = QLabel(row[1], self.data_widget)
            val_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self.data_layout.addWidget(icon_label, i,0,1,1)
            self.data_layout.addWidget(val_label, i,1,1,1)
        # set photo
        if contact.photo:
            photo = QImage.fromData(contact.photo)
            photo = photo.scaled(64,64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.photo.setPixmap(QPixmap.fromImage(photo))
        else:
            self.photo.setPixmap(App.profile_pixmap)

    def paintEvent(self, paint_ev):
        """ this function is needed, otherwise stylesheet is not applied properly """
        o = QStyleOption()
        o.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, o, p, self)

    def edit(self):
        self.editRequested.emit(self)

    def delete(self):
        self.deleteRequested.emit(self)


class ContactEditDialog(QDialog):
    def __init__(self, parent, contact=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle("Add New Contact")
        self.resize(480,150)

        # contact photo
        self.photoBtn = QToolButton(self)
        self.photoBtn.setIconSize(QSize(128,128))
        self.photoBtn.setIcon(QIcon(":/icons/qontacts.png"))
        self.photoBtn.setPopupMode(QToolButton.InstantPopup)
        menu = QMenu(self.photoBtn)
        menu.addAction("Change Photo", self.changePhoto)
        menu.addAction("Remove Photo", self.removePhoto)
        menu.addAction("Save Photo", self.savePhoto)
        self.photoBtn.setMenu(menu)

        self.nameEdit = QLineEdit(self)
        self.nameEdit.setPlaceholderText("Name")
        # data fields
        self.data_widgets = []
        self.data_layout = QGridLayout()
        self.addFieldBtn = QToolButton(self)
        self.addFieldBtn.setIcon(QIcon(":/icons/add.png"))
        self.addFieldBtn.setToolTip("Add Another Field")
        self.data_layout.addWidget(self.addFieldBtn, 0,2,1,1)
        self.btnBox = QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel, Qt.Horizontal, self)

        self.gridLayout = QGridLayout(self)
        self.gridLayout.addWidget(self.photoBtn, 0,0,2,1)
        self.gridLayout.addWidget(self.nameEdit, 0,1,1,1)
        self.gridLayout.addLayout(self.data_layout, 1,1,1,1)
        self.gridLayout.addWidget(self.btnBox, 4,0,1,3)

        self.addFieldBtn.clicked.connect(self.addDataField)
        self.btnBox.accepted.connect(self.accept)
        self.btnBox.rejected.connect(self.reject)

        self.nameEdit.setFocus()
        self.photo = None
        if contact:
            self.set_contact(contact)
            self.setWindowTitle("Edit Contact")
        if not self.data_widgets:
            self.addDataField()


    def addDataField(self):
        """ add another data field """
        typeBtn = QToolButton(self)
        typeBtn.setPopupMode(QToolButton.InstantPopup)
        menu = QMenu(typeBtn)
        for title in Contact.phone_types:
            action = menu.addAction(QIcon(":/icons/%s.png"%title.lower()), title)
        menu.triggered.connect(self.onTypeSelect)
        typeBtn.setDefaultAction(menu.actions()[0])
        typeBtn.setMenu(menu)
        valueEdit = QLineEdit(self)
        valueEdit.setPlaceholderText("Phone No./Email")
        row = len(self.data_widgets)
        self.data_layout.removeWidget(self.addFieldBtn)
        self.data_layout.addWidget(typeBtn, row,0,1,1)
        self.data_layout.addWidget(valueEdit, row,1,1,1)
        self.data_layout.addWidget(self.addFieldBtn, row,2,1,1)
        self.data_widgets.append([typeBtn, valueEdit])
        return [typeBtn, valueEdit]

    def onTypeSelect(self, action):
        btn = self.sender().parent() # menu is sender of this signal
        btn.setDefaultAction(action)

    def set_contact(self, contact):
        self.nameEdit.setText(contact.name)
        phones = [[v,k] for k,v in contact.phones.items()]
        emails = [["Email",email] for email in contact.emails]
        for typ, val in phones+emails:
            typeBtn, valueEdit = self.addDataField()
            for action in typeBtn.menu().actions():
                if action.text()==typ:
                    typeBtn.setDefaultAction(action)
                    break
            valueEdit.setText(val)
        self.photo = contact.photo
        if self.photo:
            image = QImage.fromData(self.photo)
            image = image.scaled(128,128, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            self.photoBtn.setIcon(QIcon(QPixmap.fromImage(image)))
        else:
            self.photoBtn.setIcon(QIcon(":/icons/qontacts.png"))


    def get_contact(self):
        contact = Contact()
        contact.name = self.nameEdit.text()
        for typeBtn, valueEdit in self.data_widgets:
            typ = typeBtn.defaultAction().text()
            val = valueEdit.text()
            if val:
                if typ=="Email":
                    contact.emails.append(val)
                else:
                    contact.phones[val] = typ
        contact.photo = self.photo
        return contact


    def changePhoto(self):
        filename, filtr = QFileDialog.getOpenFileName(self, "Open File",
                        "", "All Images (*.jpg *.jpeg *.png);;")
        if not filename:
            return
        image = QImage(filename)
        if image.isNull():
            return
        if image.width()>128 or image.height()>128:
            image = image.scaled(128,128, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        buff = QBuffer()
        buff.open(QIODevice.WriteOnly)
        image.save(buff, "JPEG")
        self.photo = buff.buffer().data()# QBuffer -> QByteArray -> bytes
        self.photoBtn.setIcon(QIcon(QPixmap.fromImage(image)))

    def removePhoto(self):
        if self.photo:
            self.photo = None
            self.photoBtn.setIcon(QIcon(":/icons/qontacts.png"))

    def savePhoto(self):
        if self.photo:
            filename = self.nameEdit.text() + ".jpg"
            filename, sel_filter = QFileDialog.getSaveFileName(self, "Save File",
                        filename, "JPEG Image (*.jpg);;")
            if filename:
                with open(filename, "wb") as f:
                    f.write(self.photo)

    def accept(self):
        contact = self.get_contact()
        if not contact.name or (not contact.phones and not contact.emails):
            return
        QDialog.accept(self)



def main():
    app = QApplication(sys.argv)
    #app.setOrganizationName("Arindamsoft")
    app.setApplicationName("Qontacts")
    # use fusion style on Windows platform
    if platform.system()=="Windows" and "Fusion" in QStyleFactory.keys():
        app.setStyle(QStyleFactory.create("Fusion"))
    updatePaths()
    # load window
    App.window = Window()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
