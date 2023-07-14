from PyQt5 import QtGui, uic, QtWidgets
from PyQt5.QtCore import QObject,pyqtSignal,QThread,Qt
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
        uic.loadUi("resources\\ui.ui",self)
        self.icon = QtGui.QIcon("resources\\ico.ico")
        self.setWindowIcon(self.icon)
        
        #load settings
        self.setting_window = SettingWindow(self)
        self.series_window = SeriesWindow(self)
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
        self.series.triggered.connect(self.open_series_window)
        self.school_rank.triggered.connect(self.open_input_window)
        self.estimate_school.triggered.connect(self.estimate_admission_school)

        self.schoolCodeSelection.currentIndexChanged.connect(self.choose_school)
        self.getCurrent.clicked.connect(self.get_current_information)
        self.initialisation.clicked.connect(self.initialise_thread)
        self.loopStart.clicked.connect(self.circulate_thread)
        self.loopStop.clicked.connect(self.stop_circulating)
        
    def estimate_admission_school(self):
        try:
            if not self.ifopenfile:
                raise RuntimeWarning
            
            self.enrol_plan = get_enrol_plan()
            self.ctn_list = get_code_to_name_dict()
            information_box("School recommendations are for reference only, and the author is not responsible if blind use of the software results in failed enrolment.\n学校推荐仅供参考，若盲目使用该软件导致报名失败，作者不负任何责任。")
            self.school_estimate_window = SchoolEstimateWindow(self)
            uic.loadUi("resources\\school_estimate.ui",self.school_estimate_window)
            self.school_estimate_window.init_ui()
            self.school_estimate_window.show()
            self.school_estimate_window.submit.clicked.connect(self.estimate_all_school)
            
        except RuntimeWarning:
            self.information_box(f"You haven't opened a file!","Error")

    def estimate_single_school(self,grade:Grade,schoolCode:int,type:str):
        try:
            with self.current_file.open(f"{schoolCode}.json") as f:
                data = json.load(f)
                if type not in list(data.keys()):
                    raise RuntimeWarning
                else:
                    grade_list = get_type_grade_list(data[type])
                    return get_rank(grade_list,grade)
        except RuntimeWarning:
            # the type doesn't exist
            return -1

    def estimate_all_school(self):
        school_categorise = {"impossible":[],"risky":[],"mediocre":[],"safe":[]}
        selected_type = self.school_estimate_window.get_option()
        l = self.realschoolList.copy()
        l.remove("Total")
        for schoolCode in l:
            rank = self.estimate_single_school(self.school_estimate_window.current_grade(),schoolCode,selected_type)
            if rank > 0:
                number = self.enrol_plan[int(schoolCode)][type_to_plan_name(selected_type)]
                print(rank,number)
                if not number == 0:
                    rank_rate = rank/number
                else:
                    rank_rate = 1
                schoolCode = int(schoolCode)
                if rank_rate>=0.99:
                    school_categorise["impossible"].append(self.ctn_list[schoolCode])
                elif 0.9<=rank_rate<0.99:
                    school_categorise["risky"].append(self.ctn_list[schoolCode])
                elif 0.7<=rank_rate<0.9:
                    school_categorise["mediocre"].append(self.ctn_list[schoolCode])
                else:
                    school_categorise["safe"].append(self.ctn_list[schoolCode])

        wrap = "\n"
        print(school_categorise)
        information_box(f"Risky schools:\n{wrap.join(school_categorise['risky'])}\nMediocre schools:{wrap.join(school_categorise['mediocre'])}")

    def open_input_window(self):
        try:
            if not self.ifopenfile:
                raise RuntimeWarning
            
            self.grade_input_window = GradeInputWindow(self)
            uic.loadUi("resources\\grade_input.ui",self.grade_input_window)
            self.grade_input_window.submit.clicked.connect(self.grade_input_window.get_rank)
            self.grade_input_window.init_ui()
            self.grade_input_window.show()
            
        except RuntimeWarning:
            self.information_box(f"You haven't opened a file!","Error")
            
    def get_school_rank(self,single_grade:Grade):
        # a window to show the rank in current school
        if bool(self.schoolCodeSelection.currentText()):

            with self.current_file.open(f"{self.schoolCodeSelection.currentText()}.json") as file:
                
                data = json.load(file)
                sorted_data = get_total_grade_list(data)
                sorted_data.sort(reverse=True)
                rank = get_rank(sorted_data, single_grade)
                information_box(f"Your ranking in {data['schoolName']} is {rank}/{len(sorted_data)}")  
                        
        else:
            information_box("You haven't selected a school!")            

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
            self.estimation_bar_chart = bar_chart(estimation_score_dict)
            avg_score = estimation_score_dict["Total Data"]
            self.estimation_bar_chart.set_title("Estimation Score of {}\nAverage Score:{:.3f}".format(res["schoolName"],avg_score))
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
            
            dialog = QtWidgets.QInputDialog(self)
            dialog.setFont(self.default_font)
            dialog.setWindowIcon(self.icon)

            target_grade, ifsuccess = dialog.getText(self,"Input Grade","Please input a valid grade.")

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
            self.grade_distribution_chart,ig_school,ig_stu = pie_chart(distribution,self.settings["distribution_school_threshold"])
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
                    self.school_distribution_chart,ig_grade,ig_stu= pie_chart(res["summary"]["CombinedScore"],self.settings["distribution_grade_threshold"])
                    self.school_distribution_chart.set_title(
                        f"Grade Distrubution of {res['schoolName']}\n({ig_grade} grade(s) is(are) omitted. {ig_stu} student(s) is(are) omitted.)")
                    plt.show()

            except KeyError as e:
                self.information_box(f"You haven't selected a school!\n{e}","Error")
        else:
            self.information_box(f"You haven't opened a file!","Error")

    def open_series_window(self):
        if self.ifinitialise:
            self.series_window.show()
        else:
            self.information_box("You must initialise the software first!","Error")

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
            self.information_box("You must initialise the software first!","Error")

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
            filePath, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Choose a File", os.getcwd(), "Zip Files(*.zip);;All Files (*.*)")
            if bool(filePath):
                self.open_offline_file(filePath)
        else:
            self.information_box("You must initialise the software first!","Error")

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
            self.number.setText(str(len(self.realschoolList)-1))
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
            self.getCurrent.setEnabled(False)

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
            self.information_box("You must initialise the software first!","Error")
        
    def stop_circulating(self):
        # stop circulating proactively
        if hasattr(self,"circulate_worker"):
            self.circulate_worker.running = False
            self.getCurrent.setEnabled(True)
        else:
            self.information_box("You haven't started circulating!","Error")

    def update_counter(self,num):
        self.counter.setText(str(num))

    def update_progress(self,value):
        self.progressBar.setValue(value)
        if value > self.progressBar.maximum():
            self.progressBar.close()

    def create_dialog_window(self):
        # Show the progress of getting current information

        self.progressBar = QtWidgets.QProgressDialog(self,flags=Qt.WindowMaximizeButtonHint | Qt.MSWindowsFixedSizeDialogHint | Qt.WindowMinimizeButtonHint)
        self.progressBar.setWindowTitle("Progress")
        self.progressBar.setWindowIcon(self.icon)
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
                self.output.addItem(" ") # add an empty line
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
        self.information_box(
            "Author: HangbaSteve\nEmail: hangbamaybe@gmail.com\nSupport Link: https://github.com/Hangba/NNSE-Information\n\"Every perverse person has his prison. (NNSZWST)\"","About")
        
    def information_box(self, information, title = "Information"):
        box = QtWidgets.QMessageBox()
        box.setText(information)
        box.setWindowTitle(title)
        box.setWindowIcon(self.icon)
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
        uic.loadUi("resources\\settings.ui",self)
        self.MainWindow = MainWindow
        self.icon = QtGui.QIcon("resources\\ico.ico")
        self.setWindowIcon(self.icon)
        self.apply.clicked.connect(self.save_setting)
        self.cancel.clicked.connect(self.close)
        self.single_item = ["SumScore","ChineseLevel","MathLevel","EnglishLevel","PhysicsLevel","ChymistLevel","PoliticsLevel"]
        
        self.subjects_checkbox:list[QtWidgets.QCheckBox] = [self.sum_l,self.chinese_l,self.math_l,self.english_l,self.physics_l,self.chemistry_l,self.politics_l]

    def save_setting(self):
        self.setting = {}
        with open("settings.json","w") as file:
            
            self.setting["init_online"] = self.init_net.checkState()
            try:
                self.setting["distribution_grade_threshold"] = float(self.grade_d_thre.text())
                self.setting["distribution_school_threshold"] = float(self.school_d_thre.text())
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
            self.grade_d_thre.setText(str(self.setting["distribution_grade_threshold"]))
            self.school_d_thre.setText(str(self.setting["distribution_school_threshold"]))
            self.est_index.setText(str(self.setting["estimation_index"]))

        return self.setting

    def information_box(self, information, title = "Information"):
        box = QtWidgets.QMessageBox()
        box.setText(information)
        box.setWindowTitle(title)
        box.setWindowIcon(self.icon)
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

class SeriesWindow(QtWidgets.QDialog):

    def __init__(self,MainWindow:MainWindow):
        super(SeriesWindow, self).__init__()
        uic.loadUi("resources\\series.ui",self)
        self.MainWindow = MainWindow
        self.filepaths = []
        self.icon = MainWindow.icon
        self.setWindowIcon(self.icon)
        self.ctn_list = get_code_to_name_dict()
        self.output:QtWidgets.QListWidget
        self.ifload = False

        # connections
        self.add.clicked.connect(self.add_files)
        self.deletion.clicked.connect(self.delete_selection)
        self.clear.clicked.connect(self.clear_list)
        self.load.clicked.connect(self.load_files)
        self.analyse.clicked.connect(self.analyse_data)

        self.comboBox.currentIndexChanged.connect(self.choose_school)

    def add_files(self):
        # add files to list and class attributes
        filepaths, _ = QtWidgets.QFileDialog.getOpenFileNames(self,"Choose Files", os.getcwd(), "Zip Files(*.zip);;All Files (*.*)")
        # returns a list of absolute path
        for path in filepaths:
            if path not in self.filepaths:
                self.filepaths.append(path)

        filenames = [os.path.basename(path) for path in self.filepaths]
        self.output.clear()
        self.output.addItems(filenames)
        self.ifload = False
        
    def delete_selection(self):
        
        selected = self.output.selectedIndexes()
        if bool(selected):
            line = self.output.selectedIndexes()[0].row()
            self.output.takeItem(line)
            del self.filepaths[line]
            self.ifload = False
        else:
            self.MainWindow.information_box("You haven't selected a file!","Error")

    def clear_list(self):
        self.filepaths = []
        self.output.clear()
        self.general_radio:QtWidgets.QRadioButton
        self.ifload = False

    def load_files(self):
        self.timelist = []
        self.schoolList = [] # test if all schools are the same

        try:
            if not bool(self.filepaths):
                raise RuntimeWarning
            
            if self.general_radio.isChecked():
                # confirm the school kind
                self.schoolKind = "general"
            else:
                self.schoolKind = "vocational"
            
            for filepath in self.filepaths:

                file = zipfile.ZipFile(filepath)
                current_file = file.open("metadata.json")
                metadata = json.load(current_file)

                if metadata["schoolKind"] != self.schoolKind:
                    continue

                self.timelist.append(metadata["runTime"])
                self.schoolList.append(metadata["schoolList"])
            
            if self.schoolList.count(self.schoolList[0]) != len(self.schoolList):
                raise RuntimeError
            # test for school list
            self.schoolList:list[str] = [str(schoolCode) for schoolCode in self.schoolList[0]]

            maxRunTime = time.strftime("%Y-%m-%d, %H:%M:%S",time.localtime(max(self.timelist)))
            minRunTime = time.strftime("%Y-%m-%d, %H:%M:%S",time.localtime(min(self.timelist)))
            
            self.comboBox.addItems(self.schoolList)
            self.comboBox.addItem("Total")

            self.time1.setText(minRunTime)
            self.time2.setText(maxRunTime)
            self.ifload = True

        except RuntimeWarning:
            self.MainWindow.information_box("You haven't selected files!","Error")
        except RuntimeError:
            # the school lists are not the same
            self.MainWindow.information_box("The files have different school list.","Error")

    def choose_school(self):
        if bool(self.comboBox.currentText()):
            if self.comboBox.currentText() == "Total":
                self.school_name = "Total Data"
                self.school_name_label.setText(self.school_name)
                self.current_code = "Total"
            else:
                self.current_code:int = int(self.comboBox.currentText())
                self.school_name = self.ctn_list[self.current_code]
                self.school_name_label.setText(self.school_name)

    def analyse_data(self):
        if self.ifload:
            self.time_to_path_dict = {}
            self.school_data = {}
            self.timelist = []

            for filepath in self.filepaths:
                zfile = zipfile.ZipFile(filepath)
                runtime = json.load(zfile.open("metadata.json"))["runTime"]
                file = zfile.open(f"{self.current_code}.json")

                self.school_data[runtime] = json.load(file)
                self.time_to_path_dict[runtime] = filepath
                self.timelist.append(runtime)
                file.close()

            self.seriesAnalyseWindow = Series_Analyse_Window(self.MainWindow,self)
            self.seriesAnalyseWindow.show()

class Series_Analyse_Window(QtWidgets.QDialog):

    def __init__(self,MainWindow:MainWindow,SeriesWindow:SeriesWindow):
        super(Series_Analyse_Window, self).__init__()
        uic.loadUi("resources\\series_analysis.ui",self)
        self.MainWindow = MainWindow
        self.seriesWindow = SeriesWindow
        self.setWindowIcon(self.MainWindow.icon)

        self.rank_trend.clicked.connect(self.rank_trend_folding_line)
        self.sum_trend.clicked.connect(self.sum_folding_line)
        self.score_trend.clicked.connect(self.estimation_folding_line)

    def rank_trend_folding_line(self):
        dialog = QtWidgets.QInputDialog(self.MainWindow)
        dialog.setFont(self.MainWindow.default_font)
        dialog.setWindowIcon(self.MainWindow.icon)

        try:
            target_grade, ifsuccess = dialog.getText(self.MainWindow,"Input Grade","Please input a valid grade.")
            if not ifsuccess:
                raise NotImplementedError
            
            if target_grade not in self.MainWindow.gradeOrder:
                raise RuntimeError
            
            self.seriesWindow.timelist.sort()
            relative_timelist = [str(round(t - self.seriesWindow.timelist[0],2)) for t in self.seriesWindow.timelist]
            # get the relative time to show 
            res_list = []
            for t in self.seriesWindow.timelist:
                res:dict = analyse_data(self.seriesWindow.school_data[t],self.MainWindow.gradeOrder)
                if target_grade not in list(res["summary"]["CombinedScore"].keys()):
                    res["summary"]["CombinedScore"][target_grade] = 0
                else: res_list.append(res["summary"]["CombinedScore"][target_grade])
            
            fig, ax = plt.subplots()
            ax.plot(relative_timelist,res_list)
            ax.set_title(f"{target_grade} Students Distributed in {self.seriesWindow.school_name}")
            ax.set_xlabel("Relative Time")
            ax.set_ylabel("Student Number")
            for a, b in zip(relative_timelist, res_list):
                # show data label
                ax.text(a,b,str(b))
            plt.show()
            
        except NotImplementedError:
            pass
        
        except RuntimeError:
            self.MainWindow.information_box("The grade is invalid!","Error")

    def sum_folding_line(self):
            
        self.seriesWindow.timelist.sort()
        relative_timelist = [str(round(t - self.seriesWindow.timelist[0],2)) for t in self.seriesWindow.timelist]
        # get the relative time to show 
        res_list = []
        for t in self.seriesWindow.timelist:
            res:dict = analyse_data(self.seriesWindow.school_data[t],self.MainWindow.gradeOrder)

            res_list.append(res["summary"]["num"])
        
        fig, ax = plt.subplots()
        ax.plot(relative_timelist,res_list)
        ax.set_title(f"Sum Enrolling Number in {self.seriesWindow.school_name}")
        ax.set_xlabel("Relative Time")
        ax.set_ylabel("Student Number")
        for a, b in zip(relative_timelist, res_list):
            # show data label
            ax.text(a,b,str(b))
        plt.show()

    def estimation_folding_line(self):
            
        self.seriesWindow.timelist.sort()
        relative_timelist = [str(round(t - self.seriesWindow.timelist[0],2)) for t in self.seriesWindow.timelist]
        # get the relative time to show 
        res_list = []
        for t in self.seriesWindow.timelist:
            res:dict = analyse_data(self.seriesWindow.school_data[t],self.MainWindow.gradeOrder)

            res_list.append(estimate(res["summary"]["CombinedScore"],self.MainWindow.gradeOrder,self.MainWindow.settings["estimation_index"]))
        
        fig, ax = plt.subplots()
        ax.plot(relative_timelist,res_list)
        ax.set_title(f"Estimation Score in {self.seriesWindow.school_name}")
        ax.set_xlabel("Relative Time")
        ax.set_ylabel("Score")
        for a, b in zip(relative_timelist, res_list):
            # show data label
            ax.text(a,b,str(round(b,2)))
        plt.show()

class GradeInputWindow(QtWidgets.QDialog):
    def __init__(self,MainWindow:MainWindow):
        super(GradeInputWindow, self).__init__()
        self.MainWindow = MainWindow
        self.setWindowIcon(self.MainWindow.icon)

    def init_ui(self):
        self.order = ["A+","A","B+","B","C+","C","D","E"]
        self.single_item = ["SumScore","ChineseLevel","MathLevel","EnglishLevel","PhysicsLevel","ChymistLevel","PoliticsLevel"]
        
        self.sum.addItems(self.order)
        self.chinese.addItems(self.order)
        self.maths.addItems(self.order)
        self.english.addItems(self.order)
        self.physics.addItems(self.order)
        self.chemistry.addItems(self.order)
        self.politics.addItems(self.order)

        self.sum.currentIndexChanged.connect(self.refresh_combined_score)
        self.chinese.currentIndexChanged.connect(self.refresh_combined_score)
        self.maths.currentIndexChanged.connect(self.refresh_combined_score)
        self.english.currentIndexChanged.connect(self.refresh_combined_score)
        self.physics.currentIndexChanged.connect(self.refresh_combined_score)
        self.chemistry.currentIndexChanged.connect(self.refresh_combined_score)
        self.politics.currentIndexChanged.connect(self.refresh_combined_score)
    
    def get_rank(self):
        
        single_grade = self.current_grade()
        self.MainWindow.get_school_rank(single_grade)

    def refresh_combined_score(self):
        self.combinedscore_display.setText("Combined Score: " + get_combined_score(self.current_grade()))

    
    def current_grade(self) -> Grade:
        #return current grade as class Grade
        try:
            single_grade = {}

            grades = [self.sum.currentText(),
                            self.chinese.currentText(),
                            self.maths.currentText(),
                            self.english.currentText(),
                            self.physics.currentText(),
                            self.chemistry.currentText(),
                            self.politics.currentText()]
            
            for i in range(len(self.single_item)): single_grade[self.single_item[i]] = grades[i]

            for grade in list(single_grade.values()):
                if grade not in self.order:
                    raise RuntimeError
                
            return single_data_to_grade(single_grade)

        except RuntimeError:
            self.MainWindow.information_box("The grade is not valid! Please input correct grade.", "Error")

class SchoolEstimateWindow(GradeInputWindow):

    def __init__(self, MainWindow: MainWindow):
        super(SchoolEstimateWindow,self).__init__(MainWindow)
        
        self.MainWindow = MainWindow
        self.setWindowIcon(self.MainWindow.icon)

    def get_option(self):
        r = ""
        if self.radioButton.isChecked():
            r = "instruction"
        elif self.radioButton_2.isChecked():
            r = "directional"
        elif self.radioButton_3.isChecked():
            r = "alter"
        elif self.radioButton_4.isChecked():
            r = "guide"
        elif self.radioButton_5.isChecked():
            r = "vocational"
        return r
    
app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
app.exec_()