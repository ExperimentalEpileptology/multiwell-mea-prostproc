from PyQt5 import QtWidgets, uic
import os

#from helper_widgets import ep_quickplot

class ep_step(QtWidgets.QWizardPage):
    def __init__(self, parent=None):
        super(ep_step, self).__init__(parent)
        print(os.path.join(os.path.dirname(__file__), f'../ui/{"_".join(self.__class__.__name__.split("_")[1:])}.ui'))
        self.ui = uic.loadUi(os.path.join(os.path.dirname(__file__), f'../ui/{"_".join(self.__class__.__name__.split("_")[1:])}.ui'),
                    baseinstance=self,
                    package='gui.steps')

        self.needed_inputs = []
        self.provided_outputs = []
