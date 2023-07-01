import requests
import json
from pythonping import ping
from collections import Counter
import shutil
import time
import os
import inspect
from PyQt5 import QtWidgets

def information_box(information, title = "Information"):
    box = QtWidgets.QMessageBox()
    box.setText(information)
    box.setWindowTitle(title)
    box.setIcon(QtWidgets.QMessageBox.Information)
    box.setStandardButtons(QtWidgets.QMessageBox.Ok)
    box.exec_()

def test():
    pass
    """url=f"http://www.nnzkzs.com/api/services/app/publicityDetail/GetGeneralDetail?schoolCode={str(schoolCode)}&type={t}&status={status}"
    res=requests.post(url,data=d)
    print(json.loads(res.json()["result"]))   """
    #with open("test.txt","w") as f:
    #    json.dump(requests.get("http://www.nnzkzs.com/api/services/app/generalPublicity/GetPublicity").json(),f)

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

    types = ["instruction","directional","alter","guide"]
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

def get_single_school_data(schoolCode:int,status:int):
    # Get the single school data online and return it
    # Data structure:{"schoolCode" : schoolCode, "schoolName":schoolName, "instruction" : list...}
    data = dict()
    types = ["instruction","directional","alter","guide"]
    for t in types:
        d = {'schoolCode':schoolCode,"type":t,"status":status}
        url=f"http://www.nnzkzs.com/api/services/app/publicityDetail/GetGeneralDetail?schoolCode={str(schoolCode)}&type={t}&status={status}"
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
        except BufferError:
            return None
    return data

def get_save_single_school_data(schoolCode:int,status:int,filepath = "\\"):
    # Get the single school data online and save to {schoolCode}.json
    data = get_single_school_data(schoolCode, status)
    if data != None and data != {}:
        with open(f"{filepath}{schoolCode}.json","w", encoding="utf8") as f:
            json.dump(data,f)
    else:
        return None
    return data

def get_sequence_school_data(schoolList:list,status:int,fileName, savePath = "\\saves\\"):
    types = ["instruction","directional","alter","guide"]
    # Get registeration data of schools in the schoolList and compress them into a zip file {time stamp}.zip
    currentPath = os.path.dirname(os.path.abspath (inspect.getsourcefile(lambda:0)))
    filePath = currentPath+"\\TEMP\\"
    # Make a temporary folder. If it exists, delete the folder and make again.
    if not os.path.exists(filePath):
        os.mkdir(filePath)
    else:
        shutil.rmtree(filePath)
        os.mkdir(filePath)
    
    total = dict.fromkeys(types,[]) # Summary
    total["schoolName"] = "Total Data"
    for sc in schoolList:
        #TODO: create a new window to show the progress
        #print(schoolList.index(sc)/len(schoolList))  # exporting progress

        data = get_save_single_school_data(sc,status,filePath)
        if data != None:
            for t in types:
                if t in list(data.keys()):
                    print(data.keys())
                    total[t]+=data[t]  # save all to total.json

    with open(f"{filePath}metadata.json","w",encoding="utf8") as f:
        # create metadata file
        json.dump({"runTime":time.time(),"status":status,"schoolNumber":len(schoolList)},f)
    
    with open(f"{filePath}Total.json","w",encoding="utf8") as f:
        # create metadata file
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
    types = ["instruction","directional","alter","guide"]
    total = []
    classification = dict.fromkeys(types,{})
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

    return {"summary":summary,"classification":classification}

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

def initialise():
    # get 2 school code online or offline, depends on the api's availablity
    general_api = "http://www.nnzkzs.com/api/services/app/generalPublicity/GetPublicity"
    vocational_api = "http://www.nnzkzs.com/api/services/app/vocationalPublicity/GetPublicity"
    filePath = os.path.dirname(os.path.abspath (inspect.getsourcefile(lambda:0))) + "\\Out-of-date Information\\schoolCode.json"
    with open(filePath, "r",encoding="utf8") as file:
        #get school code list online if api is available
        code_dict = json.load(file)
        if APIAvailablity(general_api, ifPost=False):
            general_list = get_school_code_list(general_api, ifPost=False)
        else:
            general_list = code_dict["general"]
        if APIAvailablity(vocational_api):
            vocational_list = get_school_code_list(vocational_api)
        else:
            vocational_list = code_dict["vocational"]
    
    filePath_order = os.path.dirname(os.path.abspath (inspect.getsourcefile(lambda:0))) + "\\gradeOrder.json"
    with open(filePath_order, "r",encoding="utf8") as file:
        grade_order = json.load(file)
        #get the grade order for sorting

    return general_list,vocational_list,grade_order
        

def open_file():
    pass