import sys
from PyQt5 import QtWidgets

from gui import ep_main_wizard
from gui.steps import ep_step_load_single_file

from core.datareader import abf_data

if __name__ == '__main__':
    

    file_list = [r'D:\XX_Temp\abf_temp\21517050 eEPSC.abf',
                 r'D:\XX_Temp\abf_temp\21517055 mEPSC.abf',
                 r'D:\XX_Temp\abf_temp\21517056 sucrose trigger.abf']

    #for file in file_list:
    #    data = abf_data(r'D:\XX_Temp\abf_temp\21517050 eEPSC.abf').get_data()
    #   print(data)


    app = QtWidgets.QApplication(sys.argv)
    m = ep_main_wizard()
    step = ep_step_load_single_file()
    #m.addPage(QtWidgets.QWizardPage())
    
    m.addPage(step)
    #m.restart()
    m.show()
    app.exec_()

    pass
