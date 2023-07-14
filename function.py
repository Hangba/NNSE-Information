import requests
import json
from pythonping import ping
from collections import Counter
import shutil
import time
import os
import inspect
from PyQt5 import QtWidgets
import matplotlib.pyplot as plt
from functools import total_ordering
from dataclasses import dataclass

def information_box(information, title = "Information"):
    box = QtWidgets.QMessageBox()
    box.setText(information)
    box.setWindowTitle(title)
    box.setIcon(QtWidgets.QMessageBox.Information)
    box.setStandardButtons(QtWidgets.QMessageBox.Ok)
    box.exec_()

def ping_host(*args):
    
    ping_result = ping(target="www.nnzkzs.com", count=10, timeout=2)

    return \
    f"""Average Latency: {ping_result.rtt_avg_ms}ms,
    Minimal Latency: {ping_result.rtt_min_ms}ms,
    Maximal Latency: {ping_result.rtt_max_ms}ms,
    Packet Loss: {ping_result.packet_loss}%
    """

def post(schoolCode, status):
    # Test for all APIs

    types = ["instruction","directional","alter","guide","vocational"]
    isInfoAPISuccessful = []

    for t in types:
        d = {'schoolCode':schoolCode,"type":t,"status":status}
        url="http://www.nnzkzs.com/api/services/app/publicityDetail/GetGeneralDetail?schoolCode=%s&type=%s&status=%s"%(str(schoolCode),t,status)
        #Test for API which is used to get detailed registeration data
        isInfoAPISuccessful.append(APIAvailablity(url,d))
    info_available = all(isInfoAPISuccessful)

    
    general_list_available = APIAvailablity("http://www.nnzkzs.com/api/services/app/generalPublicity/GetPublicity", ifPost=False)
    #Test for API which is used to get general school information. The method is Get while in 2021 and 2022 it was Post.

    general_list_available_2 = APIAvailablity("http://www.nnzkzs.com/api/services/app/generalProgress/GetProgress", ifPost=False)
    #Test for API alternative which is used to get general school information

    vocational_list_available = APIAvailablity("http://www.nnzkzs.com/api/services/app/vocationalPublicity/GetPublicity")
    # Test for API which is used to get vocational school information

    vocational_list_available_2 = APIAvailablity("http://www.nnzkzs.com/api/services/app/vocationalProgress/GetProgress")
    # Test for API alternative which is used to get vocational school information

    return f"Registeration Data API Availablity: {str(info_available)}\nGeneral School Information API Availablity: {str(general_list_available)}\nGeneral School Information API Alternative Availablity: {str(general_list_available_2)}\nVocational School Information API Availablity: {str(vocational_list_available)}\nVocational School Information API Alternative Availablity: {str(vocational_list_available_2)}"

def APIAvailablity(url,data = None, ifPost = True):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.157',
               'X-XSRF-TOKEN': 'c3zy7c3jZL5Jd4v2o33R6-eK7ydTMApwODARCPHHjMchJDmjjvUECZJmmz70NS-lpuRbK2Ya1aHi7ScW-GysCTooH9o1',
               'Accept': 'application/json, text/plain, */*',
               'Accept-Encoding': 'gzip, deflate',
               'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
               'Host': 'www.nnzkzs.com',
               'Referer': 'http://www.nnzkzs.com/'
               } # define headers

    try:
        if ifPost:
            res=requests.post(url, data = data, headers = headers)
        else:
            res = requests.get(url, data = data, headers = headers)
        r = res.json()['success']
    except Exception as e:
        print(f"API Error: {e}")
        r = False
    return r

def get_single_school_data(schoolCode:int,status:int,ifvocational = False):
    # Get the single school data online and return it
    # Data structure:{"schoolCode" : schoolCode, "schoolName":schoolName, "instruction" : list...}
    data = dict()
    types = ["instruction","directional","alter","guide"]
    ctn_dict = get_code_to_name_dict()
    if not ifvocational:
        #vocational schools api doesn't need types
        for t in types:
            d = {'schoolCode':schoolCode,"type":t,"status":status}
            url=f"http://www.nnzkzs.com/api/services/app/publicityDetail/GetGeneralDetail?schoolCode={schoolCode}&type={t}&status={status}"
            try:

                res=requests.post(url,data=d)
                if res.status_code == 502:
                    raise BufferError
                if not bool(res.json()["result"]):
                    print(f"The data of school code:{schoolCode},types:{t} is empty! (get_single_school_data)")
                    continue

                data["schoolName"] = ctn_dict[int(json.loads(res.json()["result"])["schoolCode"])] # Get school name
                data[t] = json.loads(res.json()["result"])["lists"] # Get registeration data     
            except TypeError as e:
                print(e)
            except BufferError as e:
                print("get single school data error:",str(e))
                return None
    else:
        url=f"http://www.nnzkzs.com/api/services/app/publicityDetail/GetVocationalDetail?schoolCode={schoolCode}"
        try:
            res=requests.post(url)
            if res.status_code == 502:
                raise BufferError
            if not bool(res.json()["result"]):
                print(f"The data of school code:{schoolCode} is empty!")
                return None
            if bool(ctn_dict):
                data["schoolName"] = ctn_dict[schoolCode] # Get school name
            data["vocational"] = json.loads(res.json()["result"])["lists"] # Get registeration data     
        except TypeError as e:
                print(e)
        except BufferError as e:
                print("get single school data error:",str(e))
                return None
    return data

def pie_chart(data:dict, output_threshold = 0.03):
    # draw a pie chart of the elements whose ratio is bigger than output_threshold 
    # data : {"e1":1,"e2":2}
    fig, ax = plt.subplots()
    summary = sum(list(data.values()))
    show_dict = {}
    ignored_schools = 0
    for item in data.items():
        if item[1]/summary>=output_threshold:
            show_dict[item[0]] = item[1]
        else:
            ignored_schools +=1
        
    
    grade = list(show_dict.keys())
    number = list(show_dict.values())
    ignored_students = summary - sum(number)

    ax.pie(number, labels = grade, autopct='%1.2f%%')
    return ax,ignored_schools,ignored_students

def bar_chart(data:dict):
    # draw a bar chart
    fig, ax = plt.subplots()
    
    school_names = list(data.keys())
    score = list(data.values())
    avg_score = data["Total Data"]
    err = ["{:+}".format(round(sc-avg_score,2)) for sc in score]

    bar_container = ax.bar(school_names,score)
    ax.bar_label(bar_container,err)

    return ax

def get_save_single_school_data(schoolCode:int,status:int,filepath = "\\", ifvocational = False):
    # Get the single school data online and save to {schoolCode}.json
    data = get_single_school_data(schoolCode, status,ifvocational)
    if data != None and data != {}:
        with open(f"{filepath}{schoolCode}.json","w", encoding="utf8") as f:
            json.dump(data,f)
    else:
        print(f"The data of school code:{schoolCode} is empty! (get_save_single_school_data)")
        return None
    return data

def get_sequence_school_data(schoolList:list,status:int,fileName, savePath = "\\saves\\", signal = None,ifvocational = False):
    types = ["instruction","directional","alter","guide","vocational"]
    # Get registeration data of schools in the schoolList and compress them into a zip file {time stamp}.zip
    currentPath = os.path.dirname(os.path.abspath (inspect.getsourcefile(lambda:0)))
    filePath = currentPath+"\\TEMP\\"
    # Make a temporary folder. If it exists, delete the folder and make again.
    if not os.path.exists(filePath):
        os.mkdir(filePath)
    else:
        shutil.rmtree(filePath)
        os.mkdir(filePath)
    
    total = {t: [] for t in types} # don't use dictfromkeys otherwise all the keys are hooked to a single memory
    total["schoolName"] = "Total Data"
    real_school_list = []
    for sc in schoolList:
        if bool(signal):
            # update the progress
            signal(schoolList.index(sc)+1)
        

        data = get_save_single_school_data(sc,status,filePath,ifvocational)
        if data != None:
            real_school_list.append(sc)
            for t in list(data.keys()):
                if t in types:
                    
                    total[t]+=data[t]  # save all to total.json


    with open(f"{filePath}metadata.json","w",encoding="utf8") as f:
        # create metadata file
        if ifvocational:
            kind = "vocational"
        else:
            kind = "general"
        json.dump({"runTime":time.time(),"status":status,"schoolKind":kind,"schoolNumber":len(real_school_list),"schoolList":real_school_list},f)
    
    with open(f"{filePath}Total.json","w",encoding="utf8") as f:
        # create total file
        json.dump(total,f)
    
    shutil.make_archive(fileName, "zip",filePath) # Create zip file
    if not os.path.exists(currentPath+savePath):
        os.mkdir(currentPath+savePath)
    shutil.move(currentPath+"\\"+fileName+".zip", currentPath+savePath)
    shutil.rmtree(filePath) # Delete the temporary folder

def sort_dict_by_list(dict:dict,grade_list:list):
    # sort the dictionary by list and keys
    new_dict = {}
    for l in grade_list:
        if l in list(dict.keys()):
            if dict[l]!=0:
                new_dict[l] = dict[l]
    return new_dict

def analyse_data(school_data,gradeOrder):
    # Get outline
    # summary = {"num":int,"CombinedScore:dict"}
    # student_data {"instruction":[{'Serial': '1', 'Order': '1', 'SumScore': 'A+', 'CombinedScore': '6A+', 'ChineseLevel': 'A+', 'MathLevel': 'A+', 'EnglishLevel': 'A+', 'PhysicsLevel': 'A+', 'ChymistLevel': 'A+', 'PoliticsLevel': 'A+', 'Experiment': 'p'}]}
    types = ["instruction","directional","alter","guide","vocational"]
    order = ["A+","A","B+","B","C+","C","D","E"]
    single_item = ["SumScore","ChineseLevel","MathLevel","EnglishLevel","PhysicsLevel","ChymistLevel","PoliticsLevel"]
    total = []
    classification = {t: {} for t in types}
    summary = {}
    for t in types:
        if t in list(school_data.keys()):
            total += school_data[t]
            
            classification[t]["num"] = len(school_data[t])
            # get registeration number 
            if classification[t]["num"] != 0 :classification[t]["last"] = school_data[t][-1]
            # get the worst grade
            
            classification[t]["CombinedScore"] = sort_dict_by_list(dict(Counter([l["CombinedScore"] for l in school_data[t]])),gradeOrder)

            for item in single_item:
                classification[t][item] = sort_dict_by_list(
                    dict(Counter([l[item] for l in school_data[t]])),order)

        else:
            classification[t]["num"] = 0
            classification[t]["CombinedScore"] = {}
            classification[t]["last"] = {}
        # get combine score dictionary

    

    summary["num"] = len(total)
    for item in single_item:
                summary[item] = sort_dict_by_list(dict(Counter([l[item] for l in total])),order)
                
    summary["CombinedScore"] = sort_dict_by_list(dict(Counter([l["CombinedScore"] for l in total])),gradeOrder)

    return {"summary":summary,"classification":classification,"schoolName":school_data["schoolName"]}

def get_school_code_list(url:str, ifPost = True):
    # get school code list online, now is deserted
    try:
        if ifPost:
            res = requests.post(url)
        else:
            res = requests.get(url)
        list = json.loads(res.json()['result'])["bmgs_main"]
    except json.decoder.JSONDecodeError as e:
        return get_school_code_list(url, ifPost=ifPost)
    return [int(l["SchoolCode"]) for l in list]

def initialise(ifonline = True):
    # get 2 school code online or offline, depends on the api's availablity
    general_api = "http://www.nnzkzs.com/api/services/app/generalProgress/GetProgress"
    vocational_api = "http://www.nnzkzs.com/api/services/app/vocationalProgress/GetProgress"
    filePath = os.path.dirname(os.path.abspath (inspect.getsourcefile(lambda:0))) + "\\resources\\schoolCode.json"
    with open(filePath, "r",encoding="utf8") as file:
        #get school code list online if api is available
        if ifonline:
            if APIAvailablity(general_api, ifPost=False):
                general_list = list(get_code_to_name_dict(1).keys())
            else:
                code_dict = json.load(file)
                general_list = code_dict["general"]
            if APIAvailablity(vocational_api):
                vocational_list = list(get_code_to_name_dict(2).keys())
            else:
                code_dict = json.load(file)
                vocational_list = code_dict["vocational"]
        else:
            code_dict = json.load(file)
            general_list = code_dict["general"]
            vocational_list = code_dict["vocational"]
    
    filePath_order = os.path.dirname(os.path.abspath (inspect.getsourcefile(lambda:0))) + "\\resources\\gradeOrder.json"
    with open(filePath_order, "r",encoding="utf8") as file:
        grade_order = json.load(file)
        #get the grade order for sorting

    return general_list,vocational_list,grade_order

def estimate(grade_dict:dict,gradeOrder,index:float = 2):
    #grade_dict:{"6A+":5,"5A+1A":999}
    #index: normalising constant
    #self.output.addItems([f"{l} : {res['summary']['CombinedScore'][l]}" for l in list(res['summary']['CombinedScore'])])
    score = 0
    num = 0
    for x in list(grade_dict.keys()):
        order = len(gradeOrder) - gradeOrder.index(x)
        score += grade_dict[x]*order
        num += grade_dict[x]
    try:
        score/=num
    except ZeroDivisionError:
        return 0
    score/=len(gradeOrder)

    return score**index

def get_code_to_name_dict(function = 0):
    # function: 0 - all codes; 1 - general schools; 2 - vocational schools
    # GetProgress has the greatest timeliness
    dict = {}
    url = "http://www.nnzkzs.com/api/services/app/vocationalProgress/GetProgress"
    url2 = "http://www.nnzkzs.com/api/services/app/generalProgress/GetProgress"
    res = requests.post(url)
    res2 = requests.get(url2)  #general data needs get method
    try:
        if res.status_code==200 and res2.status_code==200:
            if function == 0:
                list = json.loads(res.json()["result"])["progress"]+json.loads(res2.json()["result"])["progress"]
            elif function == 1:
                list = json.loads(res2.json()["result"])["progress"]
            elif function == 2:
                list = json.loads(res.json()["result"])["progress"]
            else:
                return None
            for l in list:
                dict[int(l["SchoolCode"])] = l["SchoolName"]
            return dict
        else:
            raise RuntimeWarning
    except RuntimeWarning as e:
        return None

@total_ordering
@dataclass
class Grade:
    # use to compare the single grade
    raw: list[int]

    def __eq__(self, other: "Grade") -> bool:
        return self.raw == other.raw
    
    def __gt__(self, other: "Grade") -> bool:
        if self.raw[0] == other.raw[0]:
            slf_gs = [0 for _ in range(10)]
            for g in self.raw:
                slf_gs[g] += 1
            oth_gs= [0 for _ in range(10)]
            for g in other.raw:
                oth_gs[g] += 1
            if slf_gs != oth_gs:
                return slf_gs > oth_gs

            return self.raw < other.raw
        else:
            return self.raw[0] < other.raw[0]


def single_data_to_grade(data:dict) -> Grade:
    # change single grade to grade class 
    l = [data["SumScore"],data["ChineseLevel"],data["MathLevel"],data["EnglishLevel"],data["PhysicsLevel"],data["ChymistLevel"],data["PoliticsLevel"]]
    order = ["A+","A","B+","B","C+","C","D","E"]
    l = [order.index(subject) for subject in l]
    return Grade(l)

def get_total_grade_list(total_data:dict) -> list[Grade]:
    types = ["instruction","directional","alter","guide","vocational"]
    data = []
    transformed_data = []
    for t in types:
        if t in list(total_data.keys()):
            data+=total_data[t]

    for d in data:
        transformed_data.append(single_data_to_grade(d))
    return transformed_data

def get_type_grade_list(data:list) -> list[Grade]:
    # get the grade list of a given 
    transformed_data = []

    for d in data:
        transformed_data.append(single_data_to_grade(d))
    return transformed_data

def get_rank(sorted_data:list[Grade], single_grade:Grade):
    # get the rank number
    if single_grade in sorted_data:
        rank = sorted_data.index(single_grade)+1
        
    else:
        for grade_index in range(len(sorted_data)):
            if grade_index == len(sorted_data)-1:
                rank = len(sorted_data)
                break
            elif sorted_data[grade_index] > single_grade > sorted_data[grade_index+1]:
                rank = grade_index + 2
                break
            elif single_grade > sorted_data[grade_index]:
                rank = 1
                break

    return rank

def get_combined_score(score:Grade):
    order = ["A+","A","B+","B","C+","C","D","E"]
    return_str = f"({order[score.raw[0]]})"
    dictionary = dict(Counter(score.raw[1:]))
    # return without sum score
    return_dict = {}
    # sort by dict values
    for key in sorted(list(dictionary.keys())):
        return_dict[key] = dictionary[key]

    for d in return_dict:
        return_str += f"{return_dict[d]}{order[d]}"
    return return_str

def get_enrol_plan(ifGeneral:bool = True) -> dict:
    def strict_int(str):
        if str!="":
            return int(str)
        else:
            return 0
    return_dict = {}
    plan_types = ["InstPlan","DirPlan","AlterPlan","GuidePlan"]
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.157',
               'X-XSRF-TOKEN': 'c3zy7c3jZL5Jd4v2o33R6-eK7ydTMApwODARCPHHjMchJDmjjvUECZJmmz70NS-lpuRbK2Ya1aHi7ScW-GysCTooH9o1',
               'Accept': 'application/json, text/plain, */*',
               'Accept-Encoding': 'gzip, deflate',
               'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
               'Host': 'www.nnzkzs.com',
               'Referer': 'http://www.nnzkzs.com/'
               } # define headers
    if ifGeneral:
        url = "http://www.nnzkzs.com/api/services/app/generalPublicity/GetPublicity"
        res = requests.get(url,headers=headers).json()
        plans = json.loads(res["result"])["bmgs_main"]
        for plan in plans:
            return_dict[int(plan["SchoolCode"])] = {}
            for t in plan_types:
                return_dict[int(plan["SchoolCode"])][t] = strict_int(plan[t])
    else:
        url = "http://www.nnzkzs.com/api/services/app/vocationalPublicity/GetPublicity"
        res = requests.post(url,headers=headers).json()
        plan = json.loads(res["result"])["bmgs_main"]
        for plan in plans:
            return_dict[int(plan["SchoolCode"])]["countNum"] = strict_int(plan["countNum"])

    return return_dict

def type_to_plan_name(type_name:str):
    types = ["instruction","directional","alter","guide"]
    plan_types = ["InstPlan","DirPlan","AlterPlan","GuidePlan"]

    return plan_types[types.index(type_name)]