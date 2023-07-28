from PyQt5 import QtWidgets, uic

class ep_main_wizard(QtWidgets.QWizard):
    def __init__(self, parent=None):
        super(ep_main_wizard, self).__init__(parent)
        self.ui = uic.loadUi('./gui/ui/main_wizard.ui', self)

    def add_pages(self, pages):
        pass
