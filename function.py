import requests
from pythonping import ping


def ping_host(ThreadName, msg):
    
    ping_result = ping(target="www.nnzkzs.com", count=10, timeout=2)

    msg[0]= f"""{ThreadName}
    Average Latency: {ping_result.rtt_avg_ms}ms,
    Minimal Latency: {ping_result.rtt_min_ms}ms,
    Maximal Latency: {ping_result.rtt_max_ms}ms,
    Packet Loss: {ping_result.packet_loss}%
    """

def post(schoolCode, status):
    types = ["instruction","directional","guide"]
    js = []
    for t in types:
        d = {'schoolCode':schoolCode,"type":t,"status":status}
        url="http://www.nnzkzs.com/api/services/app/publicityDetail/GetGeneralDetail?schoolCode=%s&type=%s&status=4"%(str(schoolCode),t)
        res=requests.post(url,data=d)
        js.append(res.json())
    with open("test.txt","w") as f:
        f.write(str(js))


def initialize():
    pass