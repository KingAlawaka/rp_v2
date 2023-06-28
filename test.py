import requests

us_server = "35.193.187.55"
eu_server = "35.187.55.49"
asia_server = "35.229.143.238"
north_server = "34.95.2.200"

def getDTType(url):
    response = requests.get(url,verify=False)
    print(response.elapsed.total_seconds())
    dt_type = response.json()['dt_type']
    dt_id = int(response.json()['DT_ID'])
    print(dt_type)
    if dt_type == "n" and dt_id != -1 :
        print("")
    else:
        print("not yet")


getDTType("http://"+us_server+":9006/details")
getDTType("http://"+eu_server+":9006/details")
getDTType("http://"+north_server+":9006/details")
getDTType("http://"+asia_server+":9006/details")