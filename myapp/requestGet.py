import requests

# jibun
hostname = "192.168.52.239"
basename = "sensordb"
tablename = "sensor"
changeURL = "/gn/datalist"

GET_URL = f"http://{hostname}{changeURL}"
response = requests.get(GET_URL)

print(response.text)
