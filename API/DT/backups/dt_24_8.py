import json
from flask import Flask,jsonify,request,Response,render_template
import socket
import random
import requests
from datetime import datetime
import configparser
import platform
from argparse import ArgumentParser
import os
import sqlite3

app = Flask(__name__)

#DT setup
#app.config['DTTSA_IP'] = "host.docker.internal" #default localhost execution for container based execution need to set using setvalues
hostname = socket.gethostname()
IPAddress = socket.gethostbyname(hostname)
localIP = IPAddress
app.config['local_IP'] = IPAddress
app.config['DT_ID'] = -1 #initially setting value to -1 to indicate that DT is not yet registered. positive value upon registration
app.config['backup_IP'] = "" #no initial backup server will be deploy
#localIP = "172.17.0.1"
#localIP = "host.docker.internal" #only for mac
port_value = "9100"
print(IPAddress)
print(platform.system()) #OS

#config = configparser.ConfigParser()
#config.read('environment_config.ini')

#DTTSA_SERVER_IP = app.config['DTTSA_IP']

#random DT data generation
organizationList = ['TORG_1','TORG_2','TORG_3','TORG_4','TORG_5','TORG_6'] #env 
DTIDList = ['DT_1','DT_2','DT_3','DT_4','DT_5','DT_6'] #env
DTNameList = ['Robotic Arm','Conveyor Belt'] #env
DTDesList = ['Robotic Arm', 'Conveyor Belt'] #env

#get values from env variables
if os.environ.get('org_code') is None:
    org_code = organizationList[random.randint(0,5)]
else:
    org_code = os.environ['org_code']

if os.environ.get('dt_code') is None:
    DT_code = DTIDList[random.randint(0,5)]
else:
    DT_code = os.environ['dt_code']

if os.environ.get('dt_name') is None:
    DT_name = DTNameList[random.randint(0,1)]
else:
    DT_name = os.environ['dt_name']

if os.environ.get('dt_desc') is None:
    DT_Description = DTDesList[random.randint(0,1)]
else:
    DT_Description = os.environ['dt_desc']

if os.environ.get('dttsa_IP') is None:
    app.config['DTTSA_IP'] = "host.docker.internal"
else:
    app.config['DTTSA_IP'] = os.environ['dttsa_IP']

if os.environ.get('num_iterations') is None:
    num_iterations = 10
else:
    num_iterations = os.environ['num_iterations']

if os.environ.get('num_dts') is None:
    num_DTs = 10
else:
    num_DTs = os.environ['num_dts']

if os.environ.get('CDT_goal') is None:
    CDT_goal = "max"
else:
    CDT_goal = os.environ['CDT_goal']

if os.environ.get('dt_type') is None:
    dt_type = "n" # n= normal, m= malicious, c=changing
else:
    dt_type = os.environ['dt_type']

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def readDB():
    conn = get_db_connection()
    posts = conn.execute('select * from test_tbl').fetchall()
    conn.close()
    #print(posts)
    for p in posts:
        print(p['created'])
    return posts


#print(org_code)

#if os.environ.get()
#DT_code = DTIDList[random.randint(0,5)]
##DT_name = DTNameList[random.randint(0,1)]
#DT_Description = DTDesList[random.randint(0,1)]
#print(org_code)

#valueholder = "No value set"

@app.route('/')
def index():
    posts = readDB()
    return render_template('index.html',posts=posts,org_code=org_code,IP=localIP)
    # return json.dumps({
    #     'Organization' : org_code,
    #     'IP' : localIP 
    #     # 'test_val' : os.environ['test_val'],
    #     # 'test_val2' : os.environ['test_val2']
    # })

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
@app.route('/setvalues')
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

def createDB():
    connection = sqlite3.connect('database.db')

    with open('schema.sql') as f:
        connection.executescript(f.read())
    
    cur = connection.cursor()

    cur.execute("insert into test_tbl (title,content) values (?,?)",("first post","first content"))
    cur.execute("insert into test_tbl (title,content) values (?,?)",("second post","second content"))

    connection.commit()
    connection.close()

def start_server(args):
    # app.config['test_val'] = args.a
    # app.config['test_val2'] = args.b
    app.run(host='0.0.0.0',port=9100)

def main(args):
    createDB()
    start_server(args)

if __name__ == '__main__':
    # parser = ArgumentParser()
    # parser.add_argument('-a')
    # parser.add_argument('-b')
    # args = parser.parse_args()
    args = ""
    main(args)