from PyQt5 import QtCore, QtGui, uic, QtWidgets
from PyQt5.QtCore import QObject,pyqtSignal,QThread
from PyQt5.QtCore import Qt
from function import *
import sys
import zipfile
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.pylab


class MainWindow(QtWidgets.QMainWindow):
    #A Class for MainWindow
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi("ui.ui",self)

        #load settings
        self.setting_window = SettingWindow(self)
        self.settings = self.setting_window.load_setting()
        self.update_setting()

        self.setWindowFlags(Qt.CustomizeWindowHint|Qt.WindowMinimizeButtonHint|Qt.WindowCloseButtonHint)
        self.setFixedSize(self.width(), self.height())
        # fix window size
        self.show()
        self.types = ["instruction","directional","alter","guide","vocational"]
        self.single_item_names = ["Sum Score","Chinese","Math","English","Physics","Chemistry","Politics & History"]
        self.single_item = ["SumScore","ChineseLevel","MathLevel","EnglishLevel","PhysicsLevel","ChymistLevel","PoliticsLevel"]
        self.status = self.StatusNum.toPlainText()
        self.currentPath = os.path.dirname(os.path.abspath (inspect.getsourcefile(lambda:0)))
        #register types
        self.ifinitialise = False
        self.ifopenfile = False
        self.default_font = QtGui.QFont("Consolas", 14)
        #self.icon = QtGui.QIcon("")
        matplotlib.rcParams["font.sans-serif"] = ["Dengxian", "Consolas"]

        self.Menu_Online_Ping.triggered.connect(self.ping_thread)
        self.Menu_Online_Post.triggered.connect(self.post_thread)
        self.Menu_File_Open.triggered.connect(self.select_file)
        self.actionExport_as_Excel_File.triggered.connect(self.export_as_excel)
        self.setting.triggered.connect(self.open_setting_window)
        self.about.triggered.connect(self.about_window)
        self.gradeDistribution.triggered.connect(self.grade_distribution)
        self.schoolDistribution.triggered.connect(self.school_distribution)
        self.estimation_chart.triggered.connect(self.draw_estimation_chart)

        self.schoolCodeSelection.currentIndexChanged.connect(self.choose_school)
        self.getCurrent.clicked.connect(self.get_current_information)
        self.initialisation.clicked.connect(self.initialise_thread)
        self.loopStart.clicked.connect(self.circulate_thread)
        self.loopStop.clicked.connect(self.stop_circulating)
        
    def draw_estimation_chart(self):
        # draw a bar chart of estimation score
        try:
            
            if not self.ifopenfile:
                raise RuntimeWarning
            
            estimation_score_dict = {}
            for fileName in self.realschoolList:
                with self.current_file.open(f"{fileName}.json") as file:
                    res:dict = analyse_data(json.load(file),self.gradeOrder)
                    estimation_score_dict[res["schoolName"]] = estimate(
                        res["summary"]["CombinedScore"],self.gradeOrder,self.settings["estimation_index"])
            self.estimation_chart = bar_chart(estimation_score_dict)
            avg_score = estimation_score_dict["Total Data"]
            self.estimation_chart.set_title("Estimation Score of {}\nAverage Score:{:.3f}".format(res["schoolName"],avg_score))
            # self.estimation_chart.xaxis.
            #if sum(list(estimation_score_dict.values()))/len(list(estimation_score_dict.values()))>=0.2:
            #    self.estimation_chart.set_ylim(bottom=0,top=1)
            plt.xticks(rotation = 90, fontsize = 8)
            plt.show()
            
                
        except RuntimeWarning:
            self.information_box(f"You haven't opened a file!","Error")

    def grade_distribution(self):
        # get the pie chart of a same grade distribution
        try:

            distribution = {}

            if not self.ifopenfile:
                raise RuntimeWarning
            target_grade, ifsuccess = QtWidgets.QInputDialog.getText(self,"Input Grade","Please input a valid grade.")

            if not ifsuccess:
                raise NotImplementedError("Process was canceled")
            
            if target_grade not in self.gradeOrder:
                raise RuntimeError
            
            file_list = self.realschoolList.copy()
            file_list.remove("Total")

            number = 0

            for fileName in file_list:
                with self.current_file.open(f"{fileName}.json") as file:
                    
                    res:dict = analyse_data(json.load(file),self.gradeOrder)
                    if target_grade in list(res["summary"]["CombinedScore"].keys()):
                        distribution[res["schoolName"]] = res["summary"]["CombinedScore"][target_grade]
                        number+=res["summary"]["CombinedScore"][target_grade]
            distribution = {f"{k} ({v}/{number})" : v for k,v in distribution.items()}
            self.grade_distribution_chart,ig_school,ig_stu = pie_chart(distribution,self.settings["distribution_1_threshold"])
            self.grade_distribution_chart.set_title(f"School Distribution of {target_grade}\n({ig_school} school(s) is(are) omitted. {ig_stu} student(s) is(are) omitted.)")
            plt.show()
                
        except RuntimeWarning:
            self.information_box(f"You haven't opened a file!","Error")
        except KeyError as e:
            self.information_box(f"You haven't selected a school!\n{e}","Error")
        except NotImplementedError:
            # user canceled the process
            pass
        except RuntimeError:
            self.information_box("The grade is invalid!","Error")

    def school_distribution(self):
        # get the pie chart of grade distribution in a single school
        if self.ifopenfile:  
            try:
                with self.current_file.open(f"{self.schoolCodeSelection.currentText()}.json") as file:
                    res:dict = analyse_data(json.load(file),self.gradeOrder)
                    self.school_distribution_chart,ig_grade,ig_stu= pie_chart(res["summary"]["CombinedScore"],self.settings["distribution_2_threshold"])
                    self.school_distribution_chart.set_title(
                        f"Grade Distrubution of {res['schoolName']}\n({ig_grade} grade(s) is(are) omitted. {ig_stu} student(s) is(are) omitted.)")
                    plt.show()

            except KeyError as e:
                self.information_box(f"You haven't selected a school!\n{e}","Error")
        else:
            self.information_box(f"You haven't opened a file!","Error")

    def get_current_information(self):
        self.status = self.StatusNum.toPlainText()
        
        if self.ifinitialise:
            self.create_dialog_window()
            # Determining whether to initialize
            self.get_thread = QThread()
            if self.isGeneral.isChecked():
            #general school information
                self.statusbar.showMessage("Getting general schools' registeration data.")
                self.get_worker = GetAll_Worker(self.schoolCodeList[0],self.status,"\\saves\\",False)
            else:
                self.statusbar.showMessage("Getting vocational schools' registeration data.")
                self.get_worker = GetAll_Worker(self.schoolCodeList[1],self.status,"\\saves\\",True)

            self.get_worker.moveToThread(self.get_thread)
            self.get_thread.started.connect(self.get_worker.run)
            self.get_worker.finished.connect(self.get_thread.quit)
            self.get_thread.finished.connect(self.get_thread.deleteLater)
            self.get_worker.result.connect(self.get_current_information_slot)
            self.get_worker.update.connect(self.update_progress)
            self.get_thread.start()
        else:
            self.information_box("You haven't initialised!","Error")

    def get_current_information_slot(self,fileName,savePath):
        self.statusbar.showMessage("Finish.")
        self.open_offline_file(self.currentPath+savePath+fileName+".zip")
        if len(self.realschoolList)-1==0:
            self.information_box(f"Getting current registeration data failed.","Error")
            return 0
        if self.isGeneral.isChecked():
            
            num = len(self.schoolCodeList[0])
        else:
            num = len(self.schoolCodeList[1])
        lack = num - len(self.realschoolList) + 1
        if lack == 0:
            self.information_box(f"Get current registeration data successfully.{len(self.realschoolList) - 1}/{num}")
        else:
            self.information_box(f"Get current registeration data incompletely successfully.{len(self.realschoolList) - 1}/{num}")

    def select_file(self):
        if self.ifinitialise:
            filePath, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Choose File", os.getcwd(), "Zip Files(*.zip);;All Files (*.*)")
            self.open_offline_file(filePath)
        else:
            self.information_box("You haven't initialised!","Error")

    def open_offline_file(self,filePath):
        try:
            self.current_file = zipfile.ZipFile(filePath)
            with self.current_file.open("metadata.json") as meta:
                # Get run time in metadata.json, get school list from file names
                originalList = self.current_file.namelist()
                originalList.remove("metadata.json")
                self.realschoolList = list(map(lambda l:l[0:-5], [l for l in originalList])) # the school exists actually, include Total.json
                if len(self.realschoolList)-1 == 0:
                    #empty data
                    self.current_file.close()
                    raise RuntimeWarning
                runTime = json.load(meta)["runTime"]
                
                self.schoolCodeSelection.clear()
                self.schoolCodeSelection.addItems(self.realschoolList)
                self.ifopenfile = True

            self.filePathLabel.setText(filePath)
            self.fileTimeLabel.setText(time.strftime("%Y-%m-%d, %H:%M:%S",time.localtime(runTime)))

        except KeyError:
            self.information_box("The file can't be parsed.","Error")
        except ValueError as e:
            self.information_box(str(e),"Error")
        except RuntimeWarning:
            #if no school is in data
            os.remove(filePath)
            return 0 

    def choose_school(self):
        if self.schoolCodeSelection.currentText()!="":
            #Reopening another file when one is already open will cause the ComboBox to call this function, resulting in an error
            with self.current_file.open(f"{self.schoolCodeSelection.currentText()}.json") as file:
                data = json.load(file)
                if "schoolName" in list(data.keys()):
                    self.schoolName.setText(data["schoolName"])
                else:
                    self.schoolName.setText("This school's name doesn't exist.")
                
                self.get_current_school()
    
    def initialise_thread(self):
        try:
            self.statusbar.showMessage("Initialising...")
            self.init_thread = QThread()
            self.init_worker = Initialise_Worker(self.settings["init_online"])
            self.init_worker.moveToThread(self.init_thread)
            self.init_thread.started.connect(self.init_worker.run)
            self.init_worker.finished.connect(self.init_thread.quit)
            self.init_thread.finished.connect(self.init_thread.deleteLater)
            self.init_worker.fail.connect(self.information_box)
            self.init_worker.result.connect(lambda *args: self.initialisation_slot(*args))
            self.init_thread.start()
        except json.decoder.JSONDecodeError:
            self.information_box("Initialisation failed. Please check your network and don't use proxy.","Error")

    def initialisation_slot(self,schoolCodeList):
        self.ifinitialise = True
        self.schoolCodeList = schoolCodeList[0:2]
        self.gradeOrder = schoolCodeList[2]
        self.ifInitialised.setText("Initialised.")
        self.initialisation.setEnabled(False)
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

    def circulate_thread(self):
        self.status = self.StatusNum.toPlainText()
        self.interval = self.Interval.toPlainText()
        if self.ifinitialise:
        # use for start threading
            self.statusbar.showMessage("Start circulating.")
            self.circulate_threading= QThread()

            if self.isGeneral.isChecked():
                #general school information
                self.circulate_worker =Circulate_Worker(self.schoolCodeList[0],self.interval,self.status,"\\saves\\")
            else:
                self.circulate_worker = Circulate_Worker(self.schoolCodeList[1],self.interval,self.status,"\\saves\\")

            self.circulate_worker.moveToThread(self.circulate_threading)
            self.circulate_threading.started.connect(self.circulate_worker.run)
            self.circulate_worker.finished.connect(self.circulate_threading.quit)
            self.circulate_worker.finished.connect(self.circulate_worker.deleteLater)
            self.circulate_worker.update.connect(self.update_counter)
            self.circulate_threading.finished.connect(self.circulate_threading.deleteLater)
            self.circulate_threading.start()
        else:
            self.information_box("You haven't initialised!","Error")
        
    def stop_circulating(self):
        # stop circulating proactively
        if hasattr(self,"circulate_worker"):
            self.circulate_worker.running = False
        else:
            self.information_box("You haven't started circulating!","Error")

    def update_counter(self,num):
        self.counter.setText(str(num))

    def update_progress(self,value):
        self.progressBar.setValue(value)
        if value > self.progressBar.maximum():
            self.progressBar.close()

    def create_dialog_window(self):
        self.progressBar = QtWidgets.QProgressDialog(self,flags=Qt.WindowMaximizeButtonHint | Qt.MSWindowsFixedSizeDialogHint | Qt.WindowMinimizeButtonHint)
        self.progressBar.setWindowTitle("Progress")
        self.progressBar.setFixedSize(350,80)
        self.progressBar.setLabelText("Getting current data...")
        self.progressBar.setMinimumDuration(5)  # confirm that the progress dialog must appear
        self.progressBar.setWindowModality(Qt.NonModal)
        self.progressBar.show()
        if self.isGeneral.isChecked():
            self.progressBar.setRange(0,len(self.schoolCodeList[0]))
        else:
            self.progressBar.setRange(0,len(self.schoolCodeList[1])) 
        self.progressBar.setValue(0)
        self.progressBar.setFont(self.default_font)

        button = QtWidgets.QPushButton(self.progressBar)
        button.hide()
        button.setEnabled(False)
        self.progressBar.setCancelButton(button)
        button.hide()
        # hide the original cancel button

        self.progressBar.show()
    
    def get_current_school(self):
        #display the detail in the list box
        self.output.clear()
        try:
            with self.current_file.open(f"{self.schoolCodeSelection.currentText()}.json") as file:
                res:dict = analyse_data(json.load(file),self.gradeOrder)
                number = res["summary"]["num"]

                summary_score = estimate(res['summary']['CombinedScore'],self.gradeOrder,self.settings["estimation_index"])
                
                self.output.addItem(f"Total Registeration Number: {res['summary']['num']}")
                self.output.addItem(f"Estimated Score:{round(summary_score,4)}")
                self.output.addItem("-- Detailed Combined Grade --")
                self.output.addItems([f"{l} : {res['summary']['CombinedScore'][l]}  ({res['summary']['CombinedScore'][l]/number:.2%})" for l in list(res['summary']['CombinedScore'])]) 
                #CombineScore output
                self.output:QtWidgets.QListView.additem("") # add an empty line
                # individual subject output
                for i in range(len(self.settings["detailed_subject"])):
                    if self.settings["detailed_subject"][i]:
                        self.output.addItem(f"-- {self.single_item_names[i]} --")
                        self.output.addItems([f"{l} : {res['summary'][self.single_item[i]][l]}  ({res['summary'][self.single_item[i]][l]/number:.2%})" 
                                              for l in list(res['summary'][self.single_item[i]])]) 
                
        except KeyError as e:
            self.information_box(f"You haven't selected a school!\n{e}","Error")

    def export_as_excel(self):
        if self.ifopenfile:
            from openpyxl import Workbook
            filePath = os.path.dirname(os.path.abspath (inspect.getsourcefile(lambda:0)))
            save, ftype = QtWidgets.QFileDialog.getSaveFileName(self, 'Save as Excel File', filePath, "Excel File (*.xlsx)")
            wb = Workbook()
            wb_activated = wb.active
            wb_activated.append(["Export time stamp:",str(int(time.time()))])
            
            
            for s in self.realschoolList:
                with self.current_file.open(f"{s}.json") as file:
                    res:dict = analyse_data(json.load(file),self.gradeOrder)
                    wb_activated.append(["School code", s])
                    wb_activated.append(["School name", res["schoolName"]])
                    for l in res['summary']['CombinedScore']:
                        wb_activated.append([l,res['summary']['CombinedScore'][l]])

                    wb_activated.append([])

            wb.save(save)
            self.information_box("Save successfully.")
        else:
            self.information_box("You haven't opened a file.","Error")
      
    def open_setting_window(self):
        self.setting_window.show()

    def about_window(self):
        self.information_box("Author: HangbaSteve\nSupport Link: https://github.com/Hangba/NNSE-Information","About")
        
    def information_box(self, information, title = "Information"):
        box = QtWidgets.QMessageBox()
        box.setText(information)
        box.setWindowTitle(title)
        box.setIcon(QtWidgets.QMessageBox.Information)
        box.setStandardButtons(QtWidgets.QMessageBox.Ok)
        box.exec_()

    def update_setting(self):
        self.settings = self.setting_window.setting
        self.status = self.StatusNum.toPlainText()

class SettingWindow(QtWidgets.QDialog):
    #A Class for setting window
    def __init__(self,MainWindow:MainWindow):
        super(SettingWindow, self).__init__()
        uic.loadUi("settings.ui",self)
        self.MainWindow = MainWindow
        self.apply.clicked.connect(self.save_setting)
        self.cancel.clicked.connect(self.close)
        self.single_item = ["SumScore","ChineseLevel","MathLevel","EnglishLevel","PhysicsLevel","ChymistLevel","PoliticsLevel"]
        
        self.subjects_checkbox:list[QtWidgets.QCheckBox] = [self.sum_l,self.chinese_l,self.math_l,self.english_l,self.physics_l,self.chemistry_l,self.politics_l]



    def save_setting(self):
        self.setting = {}
        with open("settings.json","w") as file:
            
            self.setting["init_online"] = self.init_net.checkState()
            try:
                self.setting["distribution_1_threshold"] = float(self.grade_d_thre.text())
                self.setting["distribution_2_threshold"] = float(self.school_d_thre.text())
                self.setting["estimation_index"] = float(self.est_index.text())
                self.setting["detailed_subject"] = [c.checkState() for c in self.subjects_checkbox]

                json.dump(self.setting,file)
                self.MainWindow.update_setting()
                self.information_box("Applied Successfully!")
                self.close()
            except ValueError:
                self.information_box("Input Error!","Error")
                return None
            
        return self.setting

    def load_setting(self):
        with open("settings.json","r") as file:
            self.setting = json.load(file)
            for c in range(len(self.subjects_checkbox)):
                self.subjects_checkbox[c].setChecked(self.setting["detailed_subject"][c])
            self.init_net.setChecked(self.setting["init_online"])
            self.grade_d_thre.setText(str(self.setting["distribution_1_threshold"]))
            self.school_d_thre.setText(str(self.setting["distribution_2_threshold"]))
            self.est_index.setText(str(self.setting["estimation_index"]))

        return self.setting

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

class Circulate_Worker(QObject):
    # The worker is for circulating
    finished = pyqtSignal()
    update = pyqtSignal(object)

    def __init__(self,schoolCodeList,interval,status,savePath = "\\saves\\"):
        super().__init__()
        self.schoolCodeList = schoolCodeList
        self.status = status
        self.savePath = savePath
        self.running = True
        self.interval = interval

    def run(self):
        try:
            counter = 0
            while self.running:
                current_time = str(int(time.time()))
                get_sequence_school_data(self.schoolCodeList,self.status,current_time,self.savePath)
                counter+=1
                self.update.emit(counter)
                time.sleep(int(self.interval))
                
            self.finished.emit()

        except Exception as e:
            print(f"Circulating error: {e}")
        # Emit the finished signal
        self.finished.emit()

class Initialise_Worker(QObject):
    result = pyqtSignal(object)
    finished = pyqtSignal()
    fail = pyqtSignal(object,object)

    def __init__(self,ifonline = True):
        super().__init__()
        self.ifonline = ifonline

    def run(self):
        try:
            schoolCodeList = initialise(self.ifonline)
            self.result.emit(schoolCodeList)
            self.finished.emit()
        except json.decoder.JSONDecodeError:
            self.fail.emit("Initialisation failed. Please check your network and don't use proxy.","Error")
        finally:
            self.finished.emit()
        

class GetAll_Worker(QObject):
    # For thread getting all information
    result = pyqtSignal(object,object)
    update = pyqtSignal(object)
    finished = pyqtSignal()

    def __init__(self,schoolCodeList,status,savePath = "\\saves\\",ifvocational = False):
        super().__init__()
        self.schoolCodeList = schoolCodeList
        self.status = status
        self.savePath = savePath
        self.time = str(int(time.time()))
        self.ifvocational = ifvocational

    def run(self):
        get_sequence_school_data(self.schoolCodeList,self.status,self.time,self.savePath,self.update.emit,self.ifvocational)
        self.result.emit(self.time,self.savePath)
        self.finished.emit()

app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
app.exec_()