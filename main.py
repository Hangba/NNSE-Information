from PyQt5 import QtCore, QtGui, uic, QtWidgets
from threading import Thread
from function import *
import sys


class MainWindow(QtWidgets.QMainWindow):
    #A Class for MainWindow
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi("ui.ui",self)
        self.show()

        self.types = ["instruction","directional","guide"]
        self.status = self.StatusNum.toPlainText()
        #register types

        self.Menu_Online_Ping.triggered.connect(self.ping_thread)
        #ping action
        self.Menu_Online_Send.triggered.connect(self.post_thread)

    def post_thread(self):
        try:
            thread2 = Thread(target=post,args=(2002,self.status))
            thread2.start()
        except Exception as e:
            msg = [f"Network Error: {str(e)}"]


    def ping_thread(self):
        self.statusbar.showMessage("Pinging www.nnzkzs.com.")
        #ping action layer
        msg = [None]
        try:
            thread1 = Thread(target=ping_host,args=("Ping www.nnzkzs.com",msg))
            thread1.start()
            thread1.join()
        except Exception as e:
            msg = [f"Network Error: {str(e)}"]
        box = QtWidgets.QMessageBox()
        box.setText(msg[0])
        #TODO: Optimize the function of getting return value from thread
        box.setWindowTitle("Ping Information")
        box.setIcon(QtWidgets.QMessageBox.Information)
        box.setStandardButtons(QtWidgets.QMessageBox.Ok)
        box.exec_()
        self.statusbar.showMessage("Finished!")
        


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
app.exec_()