import requests
import json

# jibun
hostname = "192.168.52.239"
basename = "sensordb"
tablename = "sensor"
changeURL = "/gn/datajson"

POST_URL = f"http://{hostname}{changeURL}"
requestBody = {"sdate1": "2021-10-01", "sdate2": "2021-10-15", "devno": ["1", "2"]}

response = requests.post(POST_URL, data=requestBody)

responseDict = json.loads(response.text)

for record in responseDict["sensorData"]:
    print(record.items())

    for key, value in record.items():
        print(f"key= {key} ,value= {value} ")

    print("-----------")
