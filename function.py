import requests
import json
from pythonping import ping
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
        try:
            res=requests.post(url,data=d)
            isInfoAPISuccessful.append(res.json()["success"])
        except:
            isInfoAPISuccessful.append(False)
    info_available = all(isInfoAPISuccessful)

    url2 = "http://www.nnzkzs.com/api/services/app/generalPublicity/GetPublicity"
    #Test for API which is used to get general school information
    try:
        res=requests.post(url2)
        general_list_available = res.json()['success']
    except:
        general_list_available = False

    url3 = "http://www.nnzkzs.com/api/services/app/vocationalPublicity/GetPublicity"
    # Test for API which is used to get vocational school information
    
    try:
        res=requests.post(url3)
        vocational_list_available = res.json()['success']
    except Exception as e:
        vocational_list_available = False

    return \
    f"""Registeration Data API Availablity: {str(info_available)}
    General School Information API Availablity: {str(general_list_available)}
    Vocational School Information API Availablity: {str(vocational_list_available)}"""

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
            data["schoolName"] = json.loads(res.json()["result"])["schoolName"] # Get school name
            data[t] = json.loads(res.json()["result"])["lists"] # Get registeration data            
        except Exception as e:
            print(e)
    return data

def get_save_single_school_data(schoolCode:int,status:int,filepath = "\\"):
    # Get the single school data online and save to {schoolCode}.json
    data = get_single_school_data(schoolCode, status)
    with open(f"{filepath}{schoolCode}.json","w", encoding="utf8") as f:
        json.dump(data,f)

def get_sequence_school_data(schoolList:list,status:int,savePath = "\\saves\\"):
    # Get registeration data of schools in the schoolList and compress them into a zip file {time stamp}.zip
    currentPath = os.path.dirname(os.path.abspath (inspect.getsourcefile(lambda:0)))
    filePath = currentPath+"\\TEMP\\"
    # Make a temporary folder. If it exists, delete the folder and make again.
    if not os.path.exists(filePath):
        os.mkdir(filePath)
    else:
        shutil.rmtree(filePath)
        os.mkdir(filePath)
    
    for sc in schoolList:
        get_save_single_school_data(sc,status,filePath)
    with open(f"{filePath}metadata.json","w",encoding="utf8") as f:
        # create metadata file
        json.dump({"runTime":time.time()},f)
    
    shutil.make_archive(str(int(time.time())), "zip",filePath) # Create zip file
    if not os.path.exists(currentPath+savePath):
        os.mkdir(currentPath+savePath)
    shutil.move(currentPath+"\\"+str(int(time.time()))+".zip", currentPath+savePath)
    shutil.rmtree(filePath) # Delete the temporary folder


def initialise():
    pass

def open_file():
    pass