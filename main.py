from PyQt5 import QtCore, QtGui, uic, QtWidgets
from PyQt5.QtCore import QObject,pyqtSignal,QThread
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
        self.Menu_Online_Post.triggered.connect(self.post_thread)

    def post_thread(self):
        self.statusbar.showMessage("Sending POST method to API.")
        self.status = self.StatusNum.toPlainText() # refresh status number
        self.thread2 = QThread()
        self.worker2 = Worker(post,2002,self.status,title = "API Availablity")
        # Move the worker to the thread
        self.worker2.moveToThread(self.thread2)
        # Connect signals and slots
        self.thread2.started.connect(self.worker2.run)
        self.worker2.finished.connect(self.thread2.quit)
        self.worker2.finished.connect(self.worker2.deleteLater)
        self.thread2.finished.connect(self.thread2.deleteLater)
        self.worker2.result.connect(lambda *args: self.information_box(*args))
        # Start the thread
        self.thread2.start()



    def ping_thread(self):
        self.statusbar.showMessage("Pinging www.nnzkzs.com.")
        # Create a QThread object and a worker object
        self.thread1 = QThread()
        self.worker1 = Worker(ping_host, title = "Pinging Result")
        # Move the worker to the thread
        self.worker1.moveToThread(self.thread1)
        # Connect signals and slots
        self.thread1.started.connect(self.worker1.run)
        self.worker1.finished.connect(self.thread1.quit)
        self.worker1.finished.connect(self.statusbar.showMessage)
        self.worker1.finished.connect(self.worker1.deleteLater)
        self.thread1.finished.connect(self.thread1.deleteLater)
        self.worker1.result.connect(lambda *args: self.information_box(*args))
        # Start the thread
        self.thread1.start()
        
        
    def information_box(self, information, title = "Information"):
        box = QtWidgets.QMessageBox()
        box.setText(information)
        box.setWindowTitle(title)
        box.setIcon(QtWidgets.QMessageBox.Information)
        box.setStandardButtons(QtWidgets.QMessageBox.Ok)
        box.exec_()

class Worker(QObject):
    # define a signal that will emit the result
    result = pyqtSignal(object,object)
    finished = pyqtSignal(object)

    def __init__(self,target,*args, title = "Information"):
        super().__init__()
        self.title = title
        self.target = target
        self.args = args

    def run(self):
        # perform the task and emit the result
        try:
            msg = self.target(*self.args)
            self.result.emit(msg,self.title)
        except Exception as e:
            msg = f"Error: {str(e)}"
            self.result.emit(msg,self.title)
        # Emit the finished signal
        self.finished.emit("Finish.")

app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
app.exec_()