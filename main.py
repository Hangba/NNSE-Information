from PyQt5 import QtCore, QtGui, uic, QtWidgets
from PyQt5.QtCore import QObject,pyqtSignal,QThread
from threading import Thread
from function import *
import sys
import zipfile


class MainWindow(QtWidgets.QMainWindow):
    #A Class for MainWindow
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi("ui.ui",self)
        self.show()

        self.types = ["instruction","directional","guide"]
        self.status = self.StatusNum.toPlainText()
        self.currentPath = os.path.dirname(os.path.abspath (inspect.getsourcefile(lambda:0)))
        #register types
        self.ifinitialise = False
        self.Menu_Online_Ping.triggered.connect(self.ping_thread)
        self.Menu_Online_Post.triggered.connect(self.post_thread)
        self.Menu_File_Open.triggered.connect(self.open_offline_file)
        self.schoolCodeSelection.currentIndexChanged.connect(self.choose_school)
        self.getCurrent.clicked.connect(self.get_current_information)
        self.initialisation.clicked.connect(self.initialise_thread)


    def get_current_information(self):
        self.status = self.StatusNum.toPlainText()
        if self.ifinitialise:
            self.statusbar.showMessage("Getting general school data")
            #general school information
            self.get_thread = QThread()
            self.get_worker = GetAll_Worker(self.schoolCodeList[0],self.status,"\\saves\\")
            self.get_worker.moveToThread(self.get_thread)
            self.get_thread.started.connect(self.get_worker.run)
            self.get_worker.finished.connect(self.get_thread.quit)
            self.get_thread.finished.connect(self.get_thread.deleteLater)
            self.get_worker.result.connect(self.get_current_information_slot)
            self.get_thread.start()

        else:
            self.information_box("You haven't initialised!","Error")

    def get_current_information_slot(self,fileName,savePath):
        self.statusbar.showMessage("Finish.")
        self.information_box("Get current registeration data successfully.")
        
        self.open_offline_file(self.currentPath+savePath+fileName+".zip")

    def select_file(self):
        filePath, fileType = QtWidgets.QFileDialog.getOpenFileName(self, "Choose File", os.getcwd(), "Zip Files(*.zip);;All Files (*)")
        self.open_offline_file(filePath)


    def open_offline_file(self,filePath):
        try:
            self.current_file = zipfile.ZipFile(filePath)
            with self.current_file.open("metadata.json") as meta:
                # Get run time in metadata.json, get school list from file names
                runTime = json.load(meta)["runTime"]
                originalList = self.current_file.namelist()
                originalList.remove("metadata.json")
                schoolList = list(map(lambda l:l[0:-5], [l for l in originalList]))
                self.schoolCodeSelection.clear()
                self.schoolCodeSelection.addItems(schoolList)

            self.filePathLabel.setText(filePath)
            self.fileTimeLabel.setText(time.strftime("%Y-%m-%d, %H:%M:%S",time.localtime(runTime)))
            #TODO: load the file into memory

        except KeyError:
            self.information_box("The file can't be parsed.","Error")
        except ValueError as e:
            self.information_box(str(e),"Error")

    def choose_school(self):
        with self.current_file.open(f"{self.schoolCodeSelection.currentText()}.json") as file:
            data = json.load(file)
            self.schoolName.setText(data["schoolName"])
            self.get_current_school()
    
    def initialise_thread(self):
        self.statusbar.showMessage("Initialising...")
        self.init_thread = QThread()
        self.init_worker = Initialise_Worker()
        self.init_worker.moveToThread(self.init_thread)
        self.init_thread.started.connect(self.init_worker.run)
        self.init_worker.finished.connect(self.init_thread.quit)
        self.init_thread.finished.connect(self.init_thread.deleteLater)
        self.init_worker.result.connect(lambda *args: self.initialisation_finish_up(*args))
        self.init_thread.start()

    def initialisation_finish_up(self,schoolCodeList):
        self.ifinitialise = True
        self.schoolCodeList = schoolCodeList
        self.ifInitialised.setText("Initialised.")
        self.statusbar.showMessage("Finish.")
        self.information_box("Initialised successfully.","Information")

    def post_thread(self):
        # Use QThread to avoid being unresponsive
        self.statusbar.showMessage("Sending POST method to API.")
        self.status = self.StatusNum.toPlainText() # refresh status number
        self.thread2 = QThread()
        self.worker2 = Test_Worker(post,2002,self.status,title = "API Availablity")
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
        self.worker1 = Test_Worker(ping_host, title = "Pinging Result")
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

    def get_current_school(self):
        self.output.clear()
        try:
            with self.current_file.open(f"{self.schoolCodeSelection.currentText()}.json") as file:
                res:dict = analyse_data(json.load(file))
                
                self.output.addItem(f"Total Registeration Number: {res['summary']['num']}")
                self.output.addItems([f"{l} : {res['summary']['CombinedScore'][l]}" for l in list(res['summary']['CombinedScore'])]) #
                #CombineScore output
        except KeyError as e:
            self.information_box(f"You haven't selected a school!\n{e}","Error")
            
        
    def information_box(self, information, title = "Information"):
        box = QtWidgets.QMessageBox()
        box.setText(information)
        box.setWindowTitle(title)
        box.setIcon(QtWidgets.QMessageBox.Information)
        box.setStandardButtons(QtWidgets.QMessageBox.Ok)
        box.exec_()

class Test_Worker(QObject):
    # The worker is for Pinging and testing API
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

class Initialise_Worker(QObject):
    result = pyqtSignal(object)
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()

    def run(self):
        schoolCodeList = initialise()
        self.result.emit(schoolCodeList)
        self.finished.emit()

class GetAll_Worker(QObject):
    # For thread getting all information
    result = pyqtSignal(object,object)
    finished = pyqtSignal()

    def __init__(self,schoolCodeList,status,savePath = "\\saves\\"):
        super().__init__()
        self.schoolCodeList = schoolCodeList
        self.status = status
        self.savePath = savePath
        self.time = str(int(time.time()))

    def run(self):
        get_sequence_school_data(self.schoolCodeList,self.status,self.time,self.savePath)
        self.result.emit(self.time,self.savePath)
        self.finished.emit()

app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
app.exec_()