import json
from flask import Flask,jsonify,request,Response
import socket
import random
import requests
from datetime import datetime
import configparser
import platform

app = Flask(__name__)
app.config['DTTSA_IP'] = "host.docker.internal"
hostname = socket.gethostname()
IPAddress = socket.gethostbyname(hostname)
localIP = IPAddress
app.config['local_IP'] = IPAddress
app.config['DT_ID'] = -1 #initially setting value to -1 to indicate that DT is not yet registered. positive value upon registration
app.config['backup_IP'] = ""
#localIP = "172.17.0.1"
#localIP = "host.docker.internal" #only for mac
port_value = "9100"
print(IPAddress)
print(platform.system()) #OS

config = configparser.ConfigParser()
config.read('environment_config.ini')

#DTTSA_SERVER_IP = app.config['DTTSA_IP']

#random DT data generation
organizationList = ['TORG_1','TORG_2','TORG_3','TORG_4','TORG_5','TORG_6']
DTIDList = ['DT_1','DT_2','DT_3','DT_4','DT_5','DT_6']
DTNameList = ['Robotic Arm','Conveyor Belt']
DTDesList = ['Robotic Arm', 'Conveyor Belt']
org_code = organizationList[random.randint(0,5)]
DT_code = DTIDList[random.randint(0,5)]
DT_name = DTNameList[random.randint(0,1)]
DT_Description = DTDesList[random.randint(0,1)]
print(org_code)

#valueholder = "No value set"

@app.route('/')
def index():
    return json.dumps({
        'Organization' : org_code,
        'IP' : localIP 
    })

#check DT internal parameter values
@app.get('/details')
def getValue():
    return json.dumps({
        'IP': localIP,
        'IP': app.config['local_IP'],
        'DTTSA_IP': app.config['DTTSA_IP'],
        'DT_ID': app.config['DT_ID'],
        'Org_code': org_code,
        'DT_code': DT_code,
        'DT_name': DT_name,
        'DT_description': DT_Description
    })

#set DT internal parameter values
@app.route('/setvalue')
def setvalue():
    app.config.update(
        DTTSA_IP = request.args.get('dttsa_ip'),
        local_IP = request.args.get('local_ip')
    )

    return json.dumps({
        'IP': app.config['local_IP'],
        'DTTSA_IP': app.config['DTTSA_IP']
    })

#random value generator for service
@app.get('/getvalues')
def getValues():
    res = [
        {
            "id": random.randint(0,6),
            "org_code": org_code,
            "timestamp": datetime.now()
        } for i in range(10)]
    return {"count": len(res), "values" : res},200

# @app.get('/service1')
# def service1():
#     api_array = [{
#             "URL": "http://"+str(app.config['local_IP'])+"/getvalue",
#             "Description": "getvalue from the DT",
#             "Type": "GET",
#             "Sample_json": {},
#             "User_auth_token": "auth token"
#         },
#         {
#             "URL": "http://"+str(app.config['local_IP'])+"/getvalue",
#             "Description": "getvalues from the DT",
#             "Type": "GET",
#             "Sample_json": {},
#             "User_auth_token": "auth token"
#         }]
#     dictToSend = {
#         "org_code": "TORG_4",
#         "DT_code" : "DT_3",
#         "DT_name": "Turbine",
#         "DT_Description": "Rotary Turbine",
#         "APIs": api_array}
#     return dictToSend

def DTreg():
    api_array = [{
            "URL": "http://"+str(app.config['local_IP'])+":" + str(port_value) +"/getvalues",
            "Description": "getvalues from the DT",
            "Type": "GET",
            "Sample_json": {},
            "User_auth_token": "auth token"
        },
        {
            "URL": "http://"+str(app.config['local_IP'])+":" + str(port_value) +"/send/",
            "Description": "sample post for DT",
            "Type": "POST",
            "Sample_json": '{"msg":"hello","sender":"sender"}',
            "User_auth_token": "auth token"
        }]
    dictToSend = {
        "org_code": org_code,
        "DT_code" : DT_code,
        "DT_name": DT_name,
        "DT_Description": DT_Description,
        "APIs": api_array}
    jsonObject = jsonify(dictToSend)
    res = requests.post('http://'+ app.config['DTTSA_IP'] +':9000/DTReg', json= dictToSend)
    print(res.text)
    return res.text #only get the text part of the response there are more 

@app.post("/send/")
def sendmessage():
    content = request.get_json()
    try:
        message = content['msg']
        sender = content['sender']
        msg = {"status" : "sucess", "data" : f"sample message {message} sender of this message {sender}"}
    except:
        msg = {"status": "Failed"}
    return jsonify(msg),200

@app.get('/dtreg')
def DTregService():
    response = DTreg()
    #print(type(response))
    obj1 = json.loads(response)
    print(obj1[0]["DT_ID"])

    app.config.update(
        DT_ID = obj1[0]["DT_ID"]
    )
    return response

@app.get('/backupreg')
def backupLocationReg():
    app.config.update(
        backup_IP = request.args.get('backupip')
    )
    res = requests.get('http://'+ str(app.config['DTTSA_IP']) +':9000/regbackup?backupip='+str(app.config['backup_IP'])+'&dtid='+ str(app.config['DT_ID']))
    return res.text

def start_server():
    app.run(host='0.0.0.0',port=9100)

def main():
    start_server()

if __name__ == '__main__':
    main()