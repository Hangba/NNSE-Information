import requests
import json
from pythonping import ping
from collections import Counter
import shutil
import time
import os
import inspect


def ping_host(*args):
    
    ping_result = ping(target="www.nnzkzs.com", count=10, timeout=2)

    return \
    f"""Average Latency: {ping_result.rtt_avg_ms}ms,
    Minimal Latency: {ping_result.rtt_min_ms}ms,
    Maximal Latency: {ping_result.rtt_max_ms}ms,
    Packet Loss: {ping_result.packet_loss}%
    """

def post(schoolCode, status):
    types = ["instruction","directional","guide"]
    isInfoAPISuccessful = []
    for t in types:
        d = {'schoolCode':schoolCode,"type":t,"status":status}
        url="http://www.nnzkzs.com/api/services/app/publicityDetail/GetGeneralDetail?schoolCode=%s&type=%s&status=4"%(str(schoolCode),t)
        #Test for API which is used to get detailed registeration data
        isInfoAPISuccessful.append(APIAvailablity(url,d))
    info_available = all(isInfoAPISuccessful)

    
    general_list_available = APIAvailablity("http://www.nnzkzs.com/api/services/app/generalPublicity/GetPublicity")
    #Test for API which is used to get general school information

    vocational_list_available = APIAvailablity("http://www.nnzkzs.com/api/services/app/vocationalPublicity/GetPublicity")
    # Test for API which is used to get vocational school information

    return f"Registeration Data API Availablity: {str(info_available)}\nGeneral School Information API Availablity: {str(general_list_available)}\nVocational School Information API Availablity: {str(vocational_list_available)}"

def APIAvailablity(url,data = None):
    try:
        res=requests.post(url,data = data)
        r = res.json()['success']
    except Exception as e:
        r = False
    return r

def get_single_school_data(schoolCode:int,status:int):
    # Get the single school data online and return it
    # Data structure:{"schoolCode" : schoolCode, "schoolName":schoolName, "instruction" : list...}
    data = dict()
    types = ["instruction","directional","guide"]
    for t in types:
        d = {'schoolCode':schoolCode,"type":t,"status":status}
        url=f"http://www.nnzkzs.com/api/services/app/publicityDetail/GetGeneralDetail?schoolCode={str(schoolCode)}&type={t}&status={status}"
        try:
            res=requests.post(url,data=d)
            if not bool(res.json()["result"]):
                continue
            data["schoolName"] = json.loads(res.json()["result"])["schoolName"] # Get school name
            data[t] = json.loads(res.json()["result"])["lists"] # Get registeration data            
        except TypeError as e:
            print(e)
    return data

def get_save_single_school_data(schoolCode:int,status:int,filepath = "\\"):
    # Get the single school data online and save to {schoolCode}.json
    data = get_single_school_data(schoolCode, status)
    with open(f"{filepath}{schoolCode}.json","w", encoding="utf8") as f:
        json.dump(data,f)
    return data

def get_sequence_school_data(schoolList:list,status:int,fileName, savePath = "\\saves\\"):
    types = ["instruction","directional","guide"]
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
        #print(schoolList.index(sc)/len(schoolList))  #out put progress
        data = get_save_single_school_data(sc,status,filePath)
        for t in types:
            if t in list(data.keys()):
                total[t]+=data[t]  # save all to total.json

    with open(f"{filePath}metadata.json","w",encoding="utf8") as f:
        # create metadata file
        json.dump({"runTime":time.time()},f)
    
    with open(f"{filePath}Total.json","w",encoding="utf8") as f:
        # create metadata file
        json.dump(total,f)
    
    shutil.make_archive(fileName, "zip",filePath) # Create zip file
    if not os.path.exists(currentPath+savePath):
        os.mkdir(currentPath+savePath)
    shutil.move(currentPath+"\\"+fileName+".zip", currentPath+savePath)
    shutil.rmtree(filePath) # Delete the temporary folder

def analyse_data(school_data):
    # Get outline
    types = ["instruction","directional","guide"]
    total = []
    classification = dict.fromkeys(types,{})
    summary = {}
    for t in types:
        if t in list(school_data.keys()):
            total += school_data[t]
            
            classification[t]["num"] = len(school_data[t])
            # get registeration number 
            
            classification[t]["CombinedScore"] = Counter([l["CombinedScore"] for l in school_data[t]])
        else:
            classification[t]["num"] = 0
            classification[t]["CombinedScore"] = {}
        # get combine score dictionary

    summary["num"] = len(total)
    summary["CombinedScore"] = Counter([l["CombinedScore"] for l in total])

    return {"summary":summary,"classification":classification}

def get_school_code_list(url:str):
    # get school code list online
    try:
        res = requests.post(url)
        list = json.loads(res.json()['result'])["bmgs_main"]
    except json.RequestsJSONDecodeError as e:
        return get_school_code_list(url)
    return [int(l["SchoolCode"]) for l in list]

def initialise():
    # get 2 school code online or offline, depends on the api's availablity
    general_api = "http://www.nnzkzs.com/api/services/app/generalPublicity/GetPublicity"
    vocational_api = "http://www.nnzkzs.com/api/services/app/vocationalPublicity/GetPublicity"
    filePath = os.path.dirname(os.path.abspath (inspect.getsourcefile(lambda:0))) + "\\Out-of-date Information\\schoolCode.json"
    with open(filePath, "r",encoding="utf8") as file:
        code_dict = json.load(file)
        if APIAvailablity(general_api):
            general_list = get_school_code_list(general_api)
        else:
            general_list = code_dict["general"]
        if APIAvailablity(vocational_api):
            vocational_list = get_school_code_list(vocational_api)
        else:
            vocational_list = code_dict["vocational"]

    return general_list,vocational_list
        

def open_file():
    pass