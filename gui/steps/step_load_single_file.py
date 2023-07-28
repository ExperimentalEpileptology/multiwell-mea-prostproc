from .step import ep_step

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QFileDialog

from core.datareader import abf_data


class ep_step_load_single_file(ep_step):
    def __init__(self, parent=None):
        super(ep_step_load_single_file, self).__init__(parent)

        # Define interactions
        self.ui.browse.clicked.connect(self.on_browse)
        self.ui.filename.textChanged.connect(self.on_filename_changed)

        self.data_file = None
        self.data = None
    
    @pyqtSlot()
    def on_browse(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setDirectory(r'D:\XX_Temp\abf_temp')
        file_dialog.setNameFilters(['ABF files (*.abf)'])

        if file_dialog.exec_():
            filename = file_dialog.selectedFiles()
            self.ui.filename.setText(filename[0].replace('/', '\\'))

    @pyqtSlot(str)
    def on_filename_changed(self, new_filename: str):
        try:
            self.data_file = abf_data(new_filename)
        except NotImplementedError as e:
            self._set_filestatus(f'Could not read file ({str(e)})', False)
            return
        
        self._set_filestatus(f'OK', True)
        self.data = self.data_file.get_data()

        self.ui.fileinfo_protocol.setText(self.data.protocol)
        self.ui.fileinfo_sweepcount.setText(str(self.data.sweep_count))
        self.ui.fileinfo_channelcount.setText(str(self.data.channel_count))
        self.ui.fileinfo_timestamp.setText(self.data.timestamp)
        self.ui.quickplot.plot(self.data)

    
    def _set_filestatus(self, text: str, status: bool):
        self.ui.fileinfo_status.setText(text)
        if status:
            self.ui.fileinfo_status.setStyleSheet('QLabel { color : green; }')
        else:
            self.ui.fileinfo_status.setStyleSheet('QLabel { color : red; }')