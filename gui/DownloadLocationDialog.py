import logging

from PySide6 import QtCore
from PySide6.QtCore import QSize, QStorageInfo, QDir
from PySide6.QtGui import QIcon, QGuiApplication
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QListWidgetItem

import gui_helpers
from gui import ui_DownloadLocationDialog
from utils import resource_path, file_size


class DownloadLocationDialog(ui_DownloadLocationDialog.Ui_Dialog, QDialog):
    def __init__(self, package, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(QIcon(resource_path("assets/gui/icons/downloadlocationdialog.png")))
        self.comboBox.setIconSize(QSize(32, 32))
        self.buttonBox.button(QDialogButtonBox.Ok).setText("Download")

        self.screen = QGuiApplication.primaryScreen()
        self.package = package
        self.selection = None

        self.setWindowTitle(f"Download \"{self.package['display_name']}\"")

        self.comboBox.setItemIcon(0, QIcon(resource_path("assets/gui/icons/browse.png")))
        self.comboBox.setItemData(0, "browse")

        # set required space label
        self.label_required_space.setText(f"**Required Space:** {file_size(self.package['extracted'])}")

        # populate list of extra dirs
        for directory in self.package["extra_directories"]:
            if not directory.startswith("/apps"):
                item = QListWidgetItem()
                item.setText(directory)
                item.setIcon(QIcon(resource_path("assets/gui/icons/directory.png")))
                self.listWidget.addItem(item)

        # set default selection
        drives = QStorageInfo().mountedVolumes()
        i = 1  # start at 1 because first item is select path
        for drive in drives:
            if not drive.isRoot():
                apps_exists = QDir(drive.rootPath() + "/apps").exists()
                if apps_exists:
                    self.comboBox.addItem(f"{drive.displayName()}\nRecommended! Found apps directory!")
                    self.comboBox.setItemIcon(i, QIcon(resource_path("assets/gui/icons/sdcard.png")))
                else:
                    self.comboBox.addItem(f"{drive.displayName()}\nUnknown. An apps folder will be created.")
                    self.comboBox.setItemIcon(i, QIcon(resource_path("assets/gui/icons/disk.png")))
                self.comboBox.setItemData(i, {"drive": drive, "appsdir": apps_exists})
                i += 1

        if gui_helpers.settings.value("download/device"):
            for i in range(self.comboBox.count()):
                if self.comboBox.itemData(i) == "browse":
                    if gui_helpers.settings.value("download/device") == "browse":
                        self.comboBox.setCurrentIndex(i)
                    else:
                        continue
                elif gui_helpers.settings.value("download/device") == self.comboBox.itemData(i)["drive"].device():
                    self.comboBox.setCurrentIndex(i)

        self.comboBox.currentIndexChanged.connect(self.combobox_index_changed)
        self.combobox_index_changed()

    def combobox_index_changed(self):
        if self.comboBox.currentData() == "browse":
            self.listWidget.hide()
            self.label_2.hide()
            self.checkBox.setChecked(False)
            self.label_available_space.setVisible(False)
        else:
            # set available space label
            self.label_available_space.setVisible(True)
            self.label_available_space.setText(
                f"**Available Space:** {file_size(self.comboBox.currentData()['drive'].bytesFree())}")
            if gui_helpers.settings.value("download/device") == self.comboBox.currentData()["drive"].device():
                self.checkBox.setChecked(True)
            else:
                self.checkBox.setChecked(False)
            if self.listWidget.count() > 0:
                self.listWidget.show()
                self.label_2.show()
            else:
                self.listWidget.hide()
                self.label_2.hide()
        QtCore.QTimer.singleShot(0, self.adjust_size)

    def adjust_size(self):
        self.resize(QSize(400, self.minimumSizeHint().height()))

    def accept(self):
        self.selection = self.comboBox.currentData()
        # save selection if checkbox is checked
        if self.checkBox.isChecked():
            if self.selection == "browse":
                device = "browse"
            else:
                device = self.selection["drive"].device()

            # save device id
            gui_helpers.settings.setValue("download/device", device)
            gui_helpers.settings.sync()
            logging.debug(f"Saved {device} to setting `download/device`")
        super().accept()
