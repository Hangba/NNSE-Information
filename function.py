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
    types = ["instruction","directional","alter","guide","vocational"]
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
                    continue
                data["schoolName"] = json.loads(res.json()["result"])["schoolName"] # Get school name
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
                return None
            ctn_dict = get_code_to_name_dict()
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

     


def get_save_single_school_data(schoolCode:int,status:int,filepath = "\\", ifvocational = False):
    # Get the single school data online and save to {schoolCode}.json
    data = get_single_school_data(schoolCode, status,ifvocational)
    if data != None and data != {}:
        with open(f"{filepath}{schoolCode}.json","w", encoding="utf8") as f:
            json.dump(data,f)
    else:
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
    for sc in schoolList:
        if bool(signal):
            # update the progress
            signal(schoolList.index(sc)+1)
        

        data = get_save_single_school_data(sc,status,filePath,ifvocational)
        if data != None:

            for t in list(data.keys()):
                if t in types:
                    
                    total[t]+=data[t]  # save all to total.json


    with open(f"{filePath}metadata.json","w",encoding="utf8") as f:
        # create metadata file
        if ifvocational:
            kind = "vocational"
        else:
            kind = "general"
        json.dump({"runTime":time.time(),"status":status,"schoolKind":kind,"schoolNumber":len(schoolList),"schoolList":schoolList},f)
    
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
    types = ["instruction","directional","alter","guide","vocational"]
    total = []
    classification = {t: {} for t in types}
    summary = {}
    for t in types:
        if t in list(school_data.keys()):
            total += school_data[t]
            
            classification[t]["num"] = len(school_data[t])
            # get registeration number 
            
            classification[t]["CombinedScore"] = dict(Counter([l["CombinedScore"] for l in school_data[t]]))
            classification[t]["CombinedScore"] = sort_dict_by_list(classification[t]["CombinedScore"],gradeOrder)
        else:
            classification[t]["num"] = 0
            classification[t]["CombinedScore"] = {}
        # get combine score dictionary

    

    summary["num"] = len(total)
    summary["CombinedScore"] = dict(Counter([l["CombinedScore"] for l in total]))
    summary["CombinedScore"] = sort_dict_by_list(summary["CombinedScore"],gradeOrder)

    return {"summary":summary,"classification":classification,"schoolName":school_data["schoolName"]}

def get_school_code_list(url:str, ifPost = True):
    # get school code list online
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
    general_api = "http://www.nnzkzs.com/api/services/app/generalPublicity/GetPublicity"
    vocational_api = "http://www.nnzkzs.com/api/services/app/vocationalPublicity/GetPublicity"
    filePath = os.path.dirname(os.path.abspath (inspect.getsourcefile(lambda:0))) + "\\Out-of-date Information\\schoolCode.json"
    with open(filePath, "r",encoding="utf8") as file:
        #get school code list online if api is available
        if ifonline:
            if APIAvailablity(general_api, ifPost=False):
                general_list = get_school_code_list(general_api, ifPost=False)
            else:
                code_dict = json.load(file)
                general_list = code_dict["general"]
            if APIAvailablity(vocational_api):
                vocational_list = get_school_code_list(vocational_api)
            else:
                code_dict = json.load(file)
                vocational_list = code_dict["vocational"]
        else:
            code_dict = json.load(file)
            general_list = code_dict["general"]
            vocational_list = code_dict["vocational"]
    
    filePath_order = os.path.dirname(os.path.abspath (inspect.getsourcefile(lambda:0))) + "\\gradeOrder.json"
    with open(filePath_order, "r",encoding="utf8") as file:
        grade_order = json.load(file)
        #get the grade order for sorting

    return general_list,vocational_list,grade_order

def estimate(grade_dict:dict,gradeOrder,ifLinear = True, index = 2):
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
    if ifLinear:
        #The linear score is very close to 1, so the function is needed to normalise it
        return score
    else:
        return score**index

def get_code_to_name_dict():
    dict = {}
    url = "http://www.nnzkzs.com/api/services/app/vocationalProgress/GetProgress"
    url2 = "http://www.nnzkzs.com/api/services/app/generalProgress/GetProgress"
    res = requests.post(url)
    res2 = requests.get(url2)  #general data needs get method
    try:
        if res.status_code==200 and res2.status_code==200:
            list = json.loads(res.json()["result"])["progress"]+json.loads(res2.json()["result"])["progress"]
            for l in list:
                dict[int(l["SchoolCode"])] = l["SchoolName"]
            return dict
        else:
            raise RuntimeWarning
    except RuntimeWarning as e:
        return None

    

def open_file():
    pass

