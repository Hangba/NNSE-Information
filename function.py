import requests
import json
from pythonping import ping


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
    #Test for API which is used to get vocational school information
    try:
        res=requests.post(url3)
        vocational_list_available = res.json()['success']
    except Exception as e:
        vocational_list_available = False

    return \
    f"""Registeration Data API Availablity: {str(info_available)}
    General School Information API Availablity: {str(general_list_available)}
    Vocational School Information API Availablity: {str(vocational_list_available)}"""

    


def initialize():
    pass