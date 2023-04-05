from cProfile import label
import json
from this import d
from time import sleep
from flask import Flask,jsonify,request,Response,render_template,make_response
import socket
import random
import requests
from datetime import datetime
import configparser
import platform
from argparse import ArgumentParser
import os
import sqlite3
from dt_db import DBHelper
from simulation import Simulation
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import re
from flask_apscheduler import APScheduler
import statistics
import sys


app = Flask(__name__)



#DT setup
hostname = socket.gethostname()
IPAddress = socket.gethostbyname(hostname)
localIP = IPAddress
app.config['local_IP'] = IPAddress
app.config['DT_ID'] = -1 #initially setting value to -1 to indicate that DT is not yet registered. positive value upon registration
app.config['backup_IP'] = "" #no initial backup server will be deploy
app.config['port'] = 9100
app.config['getinID'] = -1
app.config['getoutID'] = -1
app.config['postinID'] = -1
app.config['postoutID'] = -1
app.config['dt_reg_state'] = False
app.config['sub_in_state'] = False
app.config['send_sub_DTTSA_state'] = False
app.config['dt_type'] = "n"
app.config['evaluation_msg'] = "n"
URL_pattern_regex = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,4})')
#traffic_delay = 1 #delay function to mimic network traffic


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
    app.config['DTTSA_IP'] =  "127.0.0.1"#"host.docker.internal"
else:
    app.config['DTTSA_IP'] = os.environ['dttsa_IP']

if os.environ.get('num_iterations') is None:
    num_iterations = 10
else:
    num_iterations = os.environ['num_iterations']

if os.environ.get('num_dts') is None:
    num_DTs = 12
else:
    num_DTs = os.environ['num_dts']

if os.environ.get('CDT_goal') is None:
    CDT_goal = "min"
else:
    CDT_goal = os.environ['CDT_goal']

if os.environ.get('dt_type') is None:
    dt_types = ['n','m','c']
    app.config.update(
        dt_type = random.choice(dt_types)
    )
    # n= normal, m= malicious, c=changing
else:
    dt_type = os.environ['dt_type']

#support objects
dbHelper = DBHelper()
simHelper = Simulation(num_iterations,num_DTs,CDT_goal,app.config['dt_type'])
numVariables,num_internal_variable,num_external_variable,formula,externalVarLocations = simHelper.generateFormula()
valueRanges = simHelper.generateRandomValueRanges()
scheduler = APScheduler()
scheduler.init_app(app)

def getInternalSubs():
    subList = dbHelper.getSubscriptionInfo("i")
    subs = [
        {
            "id": sub[0],
            "direction": sub[1],
            "req_type": sub[2],
            "DT_ID": sub[3],
            "API_ID": sub[4],
            "url": sub[5],
            "formula_position": sub[6]
        } for sub in subList]
    return subs

def getExternalSubs():
    subList = dbHelper.getSubscriptionInfo("e")
    subs = [
        {
            "id": sub[0],
            "direction": sub[1],
            "req_type": sub[2],
            "DT_ID": sub[3],
            "API_ID": sub[4],
            "url": sub[5]
        } for sub in subList]
    return subs

@app.get('/getsublist')
def getSavedSubList():
    typeofSubs = request.args.get('type') #i for internal. e for external
    if typeofSubs == "i":
        subs = getInternalSubs()
    else:
        subs = getExternalSubs()
    return {"Total records": len(subs),"subList":subs}

@app.get('/genVal')
def testGenValue():
    r = generateValue()
    return str(r)

def findMax(l):
    temp_max = l[0]
    for n in l:
        if n > temp_max:
            temp_max = n
    return temp_max

def findMin(l):
    temp_min = l[0]
    for n in l:
        if n < temp_min:
            temp_min = n
    return temp_min

def generateValue():
    normalDT_value_selection_limit = 5
    changingDT_value_selection_limit = 2
    if app.config['dt_type'] == "m":
        min = random.randint(1,10)
        max = random.randint(min,min+10)
        value = random.randint(min,max)
    else:
        if len(valueRanges) == 1:
            valueList = []
            for i  in range(normalDT_value_selection_limit):
                valueList.append(simHelper.generateValue(valueRanges[0][0],valueRanges[0][1]))
            if len(valueList) > 0:
                if CDT_goal == "max":
                    value = findMax(valueList)
                else:
                    value = findMin(valueList)
            else:
                value = -1
        elif len(valueRanges) > 1:
            selectRange = random.randint(0,len(valueRanges)-1)
            valueList = []
            for i in range(changingDT_value_selection_limit):
                valueList.append(simHelper.generateValue(valueRanges[selectRange][0],valueRanges[selectRange][1]))
                #print(valueList)
            #print(valueList)
            if len(valueList)>0:
                if CDT_goal == "max":
                    value = findMax(valueList)
                else:
                    value = findMin(valueList)
            else:
                value = -1
    return value

def delayResponse():
    if app.config['dt_type'] == "c":
        v = random.randint(1,4) #1,4 no delay 2,3 delay
        if v== 1 or v==4:
            return False
        else:
            return True
    elif app.config['dt_type'] == "n":
        v = random.randint(1,4) #1,2,4 no delay 3 delay
        if v== 1 or v==4 or v == 2:
            return False
        else:
            return True
    else:
        return True

def delayTime():
    m_min = 2
    m_max = 4
    c_min = 1
    c_max = 2
    n_min = 1
    n_max = 1
    if app.config['dt_type'] == "m":
        return random.randint(m_min,m_max)
    elif app.config['dt_type'] == "c":
        return random.randint(c_min,c_max)
    else:
        return random.randint(n_min,n_max)

def DTreg(GET_in_URL,GET_out_URL,POST_out_URL,POST_in_URL):
    api_array = [{
            "URL": GET_in_URL,
            "Description": "[GET][IN]",
            "Type": "GET",
            "Sample_json": {},
            "User_auth_token": "auth token"
        },
        {
            "URL": GET_out_URL,
            "Description": "[GET][OUT]",
            "Type": "GET",
            "Sample_json": {},
            "User_auth_token": "auth token"
        },
        {
            "URL": POST_out_URL,
            "Description": "[POST][OUT]",
            "Type": "POST",
            "Sample_json": '{"value": -111111111,"DT_ID" : -111111111,"API_ID" : -111111111}',
            "User_auth_token": "auth token"
        },
        {
            "URL": POST_in_URL,
            "Description": "[POST][IN]",
            "Type": "POST",
            "Sample_json": '{"value": -111111111,"DT_ID" : -111111111,"API_ID" : -111111111}',
            "User_auth_token": "auth token"
        }]
    dictToSend = {
        "org_code": org_code,
        "DT_code" : DT_code,
        "DT_name": DT_name,
        "DT_Description": DT_Description,
        "DT_IP": "http://"+str(app.config['local_IP'])+":" + str(app.config['port']),
        "APIs": api_array}
    jsonObject = jsonify(dictToSend)
    res = requests.post('http://'+ app.config['DTTSA_IP'] +':9000/DTReg', json= dictToSend)
    #print(res.text)
    return res.text #only get the text part of the response there are more

@app.get('/getformula')
def getFormulaDetails():
    return {
        "Num var":numVariables,
        "Num In var":num_internal_variable,
        "Num Out var":num_external_variable,
        "Formula":formula
    }


@app.get('/dtreg')
def DTregService():
    GET_in_URL = "http://"+str(app.config['local_IP'])+":" + str(app.config['port']) +"/getvalue/"
    GET_out_URL = "http://"+str(app.config['local_IP'])+":" + str(app.config['port']) +"/sendvalue"
    POST_out_URL = "http://"+str(app.config['local_IP'])+":" + str(app.config['port']) +"/sendpost/"
    POST_in_URL = "http://"+str(app.config['local_IP'])+":" + str(app.config['port']) +"/getpost/"
    if app.config['DT_ID'] == -1:
        response = DTreg(GET_in_URL,GET_out_URL,POST_out_URL,POST_in_URL)
        #print(type(response))
        obj1 = json.loads(response)
        #print(obj1[0]["DT_ID"])

        app.config.update(
            DT_ID = obj1[0]["DT_ID"]
        )
        APIs = requests.get('http://'+ app.config['DTTSA_IP'] +':9000/getownapis?dt_id='+str(app.config['DT_ID']))
        #print(APIs.text)
        #jsonObj = json.loads(APIs.json())
        #print(APIs.json()['APIs'])
        apiList = APIs.json()['APIs']

        #print(APIs.text[0]['APIs'])
        # jsonresponse = json.loads(APIs.decode('utf-8'))
        
        for api in apiList:
            #data = json.load(api)
            if api['URL'] == GET_in_URL:
                app.config.update(
                    getinID = api['API_ID']
                )
            elif api['URL'] == GET_out_URL:
                app.config.update(
                    getoutID = api['API_ID']
                )
            elif api['URL'] == POST_out_URL:
                app.config.update(
                    postoutID = api['API_ID']
                )
            else:
                app.config.update(
                    postinID = api['API_ID']
                )
    else:
        response = {"DT_ID": "All ready registed","status": "Failed"},400
    return response

#allow other DTs to register their service subscriptions
@app.route('/sub')
def recordExternalSub():
    subDT_ID = request.args.get('dt_id')    #DT ID of the External DT
    subAPI_ID = int(request.args.get('api_id'))  #API ID of the subscribing API
    subReq_type = request.args.get('req')   #request type
    subURL = request.args.get('url')        #URL need to response
    #print(type(app.config['getinID']))
    #print(type(subAPI_ID))
    if app.config['getinID'] != -1 and app.config['getoutID'] != -1 and app.config['postinID'] != -1 and app.config['postoutID'] != -1:
        if subAPI_ID in (app.config['getinID'],app.config['getoutID'],app.config['postinID'],app.config['postoutID']):
            dbHelper.addExternalSub(subReq_type,subDT_ID,subAPI_ID,subURL)
            response = {"msg": "Subscribed successfully","status": "Success"},200
        else:
            response = {"msg": "API ID is not in the range of DTs possible APIs","status": "Failed"},400
    else:
        response = {"msg": "DT, APIs did not have IDs","status": "Failed"},400
    return response

#based on the DT formula subscribe to external DT APIs for formula calculations
@app.route('/subin')
def recordInternalSub():
    # "Num var":numVariables,
    #     "Num In var":num_internal_variable,
    #     "Num Out var":num_external_variable,
    #     "Formula":formula
    APIs = requests.get('http://'+ app.config['DTTSA_IP'] +':9000/getapis?dt_id='+str(app.config['DT_ID']))
        #print(APIs.text)
        #jsonObj = json.loads(APIs.json())
    #print(APIs.json()['APIs'])
    try:
        apiList = APIs.json()['APIs']
        #print("API List Len: ", len(apiList))
        #print(apiList[2]['URL'])
        for varLocation in externalVarLocations:
            #selectedIndex = random.randint(0,len(apiList))
            selectedIndex = random.choice(apiList)
            dbHelper.addInternalSub(selectedIndex['type'],selectedIndex['DT_ID'],selectedIndex['API_ID'],selectedIndex['URL'],varLocation)
            # dbHelper.addInternalSub(apiList[selectedIndex]['type'],apiList[selectedIndex]['DT_ID'],apiList[selectedIndex]['API_ID'],apiList[selectedIndex]['URL'],varLocation)
            temp_DT_IP = URL_pattern_regex.search(selectedIndex['URL'])[0]
            #temp_DT_IP = URL_pattern_regex.search(apiList[selectedIndex]['URL'])[0]
            if selectedIndex['type'] == 'POST':
                url = "http://"+str(app.config['local_IP'])+":" + str(app.config['port']) +"/getpost/"
            else:
                url = selectedIndex['URL']
            
            res = requests.get('http://'+ temp_DT_IP +'/sub?dt_id='+ str(app.config['DT_ID'])+'&api_id='+ str(selectedIndex['API_ID'])+'&url='+url+'&req='+selectedIndex['type'])
            #res = requests.get('http://'+ temp_DT_IP +'/sub?dt_id='+ str(app.config['DT_ID'])+'&api_id='+ str(apiList[selectedIndex]['API_ID'])+'&url='+url+'&req='+apiList[selectedIndex]['type'])
            #print(apiList[selectedIndex][''])
        # for api in apiList:
        #         #data = json.load(api)
        #     print
        #print(formula)
        res = {"msg": "Sucess"}
        return make_response(res,200)
    except Exception as e:
        res = {"msg": "No APIs yet"}
        return make_response(res,400)

def value(c):
    if c == '$':
        return generateValue()
    else:
        return     

def calculatevalues(v1,v2,operator):
    if operator == '+':
        total = v1 + v2               
    elif operator == '-':
        total = v1 - v2            
    elif operator == '*':
        total = v1 * v2          
    else:
        total = v1 / v2
    return total
    
@app.route('/cal')
def calculateFormula():
    allSubGETRequests = dbHelper.getInternalGETSubs()
    #print(allSubGETRequests)
    for sub in allSubGETRequests:
        res = requests.get(sub[5]+"?dt_id"+str(app.config['DT_ID']))
        data  = json.loads(res.text)
        dbHelper.insertQoSTbl(sub[3],sub[4],res.elapsed.total_seconds())
        #print (data)
        dbHelper.insertDataTbl("GET",data['DT_ID'],data['API_ID'],data['value'])
        #print(res.text)
    allInternalSubs = dbHelper.getSubscriptionInfo("i")
    # for a in allInternalSubs:
    #     print(a['DT_ID'])
    internalSubValues = []
    internalDTGenValues = []
    internalUsedSubValues = []
    for internalSub in allInternalSubs:
        data = dbHelper.getvaluesToCalculate(internalSub['DT_ID'],internalSub['API_ID'])
        for d in data:
            #print(d['value'])
            internalSubValues.append({'ID': d['id'],'value': d['value']})
        #print(internalSubValues)
    formulaCalculatedValue = -1111111 #this will indicate still not calculated
    if num_external_variable == len(internalSubValues):
        
        internalSubValuesCounter = 0
        for i in range(2, len(formula) - 1):
            v1 = 0
            v2 = 0
            if i == 2:
                if formula[i] == "$":
                    v1 = generateValue()
                    internalDTGenValues.append({'pos': i, 'val': v1 })
                else:
                    v1 = int(internalSubValues[internalSubValuesCounter]["value"])
                    internalUsedSubValues.append({'pos': i, 'val': v1 })
                    internalSubValuesCounter = internalSubValuesCounter + 1
                
                if formula[i+2] == "$":
                    v2 = generateValue()
                    internalDTGenValues.append({'pos': i+2, 'val': v2 })
                else:
                    v2 = int(internalSubValues[internalSubValuesCounter]["value"])
                    internalUsedSubValues.append({'pos': i+2, 'val': v2 })
                    internalSubValuesCounter = internalSubValuesCounter + 1
                #print(str(v1),str(v2),formula[i + 1])
                formulaCalculatedValue = calculatevalues(v1,v2,formula[i + 1])         
            if i >= 5:
                if i % 2 != 0:
                    if formula[i+1] == "$":
                        v1 = generateValue()
                        internalDTGenValues.append({'pos': i+1, 'val': v1 })
                    else:
                        v1 = int(internalSubValues[internalSubValuesCounter]["value"])
                        internalSubValuesCounter = internalSubValuesCounter + 1
                        internalUsedSubValues.append({'pos': i+1, 'val': v1 })
                    #print(str(formulaCalculatedValue),str(v1),formula[i])
                    formulaCalculatedValue = calculatevalues(formulaCalculatedValue,v1,formula[i])
    for i in internalSubValues:
        dbHelper.updateDataTable(i["ID"])
    for_id = dbHelper.addFormulaCalculation(str(formula),formulaCalculatedValue)
    for i in internalDTGenValues:
        dbHelper.addDTGenData(for_id,i["pos"],i["val"])
        dbHelper.addCalValueData(for_id,i["pos"],i["val"],"i")
    for i in internalUsedSubValues:
        dbHelper.addCalValueData(for_id,i["pos"],i["val"],"e")
    #print(internalDTGenValues)                
    #return str(formulaCalculatedValue)
    res = {"msg": str(formulaCalculatedValue)}
    return make_response(res,200)

@app.route('/sendothers')
def sendValuesToOtherDTs():
    res = {"status" : "success", "msg" : "No POST subscribers"}
    allPOSTSubs = dbHelper.getExternalPOSTSubs()
    if len(allPOSTSubs) > 0:
        for sub in allPOSTSubs:
            value = generateValue()
            msgToSend = {
            "value": value,
            "DT_ID": app.config['DT_ID'],
            "API_ID": app.config['postoutID']
            }
            jsonObj = jsonify(msgToSend)
            tempURL = sub[5]
            sub_dt_id = sub[3]
            res = requests.post(tempURL,json=msgToSend)
            dbHelper.insertQoSTbl(sub_dt_id,99,res.elapsed.total_seconds())
            dbHelper.addTransaction("DT: "+ str(app.config['DT_ID'])+ " API_ID: "+ str(app.config['postoutID']) + "send value to " + res.text)
            dbHelper.insertDataSentTbl('POST',sub_dt_id,str(app.config['postoutID']),value)
            res = res.text
    return make_response(res,200)

@app.route('/')
def index():
    #posts = readDB()
    #getInternalSubs()
    #getExternalSubs()
    allTransRecords = dbHelper.getAllTransactionTbl()
    allDataRecords = dbHelper.getAllDataTbl()
    allQoSData = dbHelper.getQoSDataForDT()
    # data = [
    #     (100,343),
    #     (200,143),
    #     (300,743),
    #     (400,343),
    #     (500,243),
    #     (600,843),
    #     (700,343)
    # ]
    #d = dbHelper.getSampleDataforGraph()
    d = dbHelper.getFormulaCalTbl()
    data = []
    for i in d:
        data.append(tuple(i))
    #print(data)
    labels = [row[0] for row in data]
    values = [row[1] for row in data]

    d2 = dbHelper.getDataSentTbl()
    data2 = []
    for i in d2:
        data2.append(tuple(i))
    labels2 = [row[0] for row in data2]
    values2 = [row[1] for row in data2]
    # print("______")
    # print(labels2)
    # print(values2)
    # valpos = dbHelper.getFormulaValuePositions()
    # formulaCalLabelList = []
    # formulaCalValueList = []
    # pos=[]
    # for v in valpos:
    #     data2 = []
    #     a = dbHelper.getFormulaValuesByPos(v[0])
    #     for b in a:
    #         data2.append(tuple(b))
    #     formulaCalLabelList.append([row[0] for row in data2])
    #     formulaCalValueList.append([row[1] for row in data2])
    #     pos.append(v[0])
    
    # print(formulaCalLabelList)
    # print(formulaCalValueList)

    
    return render_template('index.html',allQoSData=allQoSData,labels2=labels2,values2=values2,evaluation=app.config['evaluation_msg'],labels=labels,values=values,allDataRecords=allDataRecords, allTransRecords=allTransRecords,org_code=org_code,IP=app.config['local_IP'],dt_id=app.config['DT_ID'])

    #return render_template('index.html',evaluation=app.config['evaluation_msg'],pos=pos,formulaCalValueList=formulaCalValueList,formulaCalLabelList=formulaCalLabelList[0],labels=labels,values=values,allDataRecords=allDataRecords, allTransRecords=allTransRecords,org_code=org_code,IP=app.config['local_IP'],dt_id=app.config['DT_ID'])
    #return render_template('index.html',posts=posts,org_code=org_code,IP=localIP)
    #return json.dumps({"msg":"Hello"})

@app.route('/details')
def details():
    dbHelper.addTransaction("/detalis called")
    return json.dumps({
        'Organization' : org_code,
        'IP' : localIP,
        'DT_name' : DT_name,
        'DT_Description' : DT_Description,
        'DT_ID':app.config['DT_ID'],
        'DT_IP': "http://"+str(app.config['local_IP'])+":" + str(app.config['port']),
        'DTTSA_IP': app.config['DTTSA_IP'],
        'num_iterations' : num_iterations,
        'num_DTs': num_DTs,
        'CDT_goal': CDT_goal,
        'dt_type': app.config['dt_type'],
        'GET_IN':app.config['getinID'],
        'GET_OUT':app.config['getoutID'],
        'POST_IN':app.config['postinID'],
        'POST_OUT':app.config['postoutID']
    })

#set DT internal parameter values
#/setvalues?dttsa_ip=127.0.0.1&local_ip=127.0.0.1
@app.route('/setvalues')
def setvalue():
    app.config.update(
        DTTSA_IP = request.args.get('dttsa_ip'),
        local_IP = request.args.get('local_ip')
    )

    return json.dumps({
        'IP': app.config['local_IP'],
        'DTTSA_IP': app.config['DTTSA_IP'],
        'GET_IN':app.config['getinID'],
        'GET_OUT':app.config['getoutID'],
        'POST_IN':app.config['postinID'],
        'POST_OUT':app.config['postoutID']
    })

def createResponseHeaders(resObj):
    resObj.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    resObj.headers['Content-Security-Policy'] = "default-src 'self'"
    resObj.headers['X-Content-Type-Options'] = 'nosniff'
    resObj.headers['X-Frame-Options'] = 'SAMEORIGIN'
    resObj.headers['X-XSS-Protection'] = '1; mode=block'
    resObj.headers['Server'] = 'ASD'
    return resObj

'''
[POST][IN]
Allowing others to send values using POST
'''
@app.post("/getpost/")
def submitvalue():
    content = request.get_json()
    print(request.headers)
    if delayResponse():
        sleep(delayTime())
    try:
        value = content['value']
        senderDT = content['DT_ID']
        API_ID = content ['API_ID']
        try:
            int(value)
            int(senderDT)
            int(API_ID)
        except:
            msg = {"status": "Failed"}
            payload = msg
            res = make_response(jsonify(payload),406)
            # res.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            # res.headers['Content-Security-Policy'] = "default-src 'self'"
            # res.headers['X-Content-Type-Options'] = 'nosniff'
            # res.headers['X-Frame-Options'] = 'SAMEORIGIN'
            # res.headers['X-XSS-Protection'] = '1; mode=block'
            # res.headers['Server'] = 'ASD'
            res = createResponseHeaders(res)
            return res
        
        dbHelper.insertDataTbl('POST',senderDT,API_ID,value)
        msg = {"status" : "success", "msg" : f"received {value} from sender  {senderDT} using API {API_ID}"}
        payload = msg
        if 'access_token' in request.headers:
            res = make_response(jsonify(payload),200)#200
        else:
            res = make_response(jsonify(payload),406)#200
        # res.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        # res.headers['Content-Security-Policy'] = "default-src 'self'"
        # res.headers['X-Content-Type-Options'] = 'nosniff'
        # res.headers['X-Frame-Options'] = 'SAMEORIGIN'
        # res.headers['X-XSS-Protection'] = '1; mode=block'
        # res.headers['Server'] = 'ASD'
        #res = make_response(jsonify(payload),200)
        res = createResponseHeaders(res)
        return res
    except:
        msg = {"status": "Failed"}
        payload = msg
        res = make_response(jsonify(payload),406)
        # res.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        # res.headers['Content-Security-Policy'] = "default-src 'self'"
        # res.headers['X-Content-Type-Options'] = 'nosniff'
        # res.headers['X-Frame-Options'] = 'SAMEORIGIN'
        # res.headers['X-XSS-Protection'] = '1; mode=block'
        # res.headers['Server'] = 'ASD'
        res = createResponseHeaders(res)
        return res

'''
[POST][OUT]
Make a post to DT2.
'''
@app.get("/sendpost/")
def postother():
    if delayResponse():
        sleep(delayTime())
    msgToSend = {
        "value": generateValue(),
        "DT_ID": app.config['DT_ID'],
        "API_ID": app.config['postoutID']
    }
    jsonObj = jsonify(msgToSend)
    tempURL = "http://127.0.0.1:9100/getpost/"
    res = requests.post(tempURL,json=msgToSend)
    return make_response(res.text,200)


'''
[GET][In]
DT1 will request DT2 to send a value. 
Response will carry the value for calculation
serviceURL will be DT2 IP+Service
'''
@app.get("/getvalue/")
def getvalue():
    if delayResponse():
        sleep(delayTime())
    #getServiceURL = dbHelper.getServiceURL() 
    getServiceURL = "http://"+str(app.config['local_IP'])+":" + str(app.config['port'])+"/sendvalue"
    res = requests.get(getServiceURL)
    #get the values from the res and store in the data tbl
    #security improvement test
    payload = res.text
    res = make_response(jsonify(payload),200)
    res.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    res.headers['Content-Security-Policy'] = "default-src 'self'"
    res.headers['X-Content-Type-Options'] = 'nosniff'
    res.headers['X-Frame-Options'] = 'SAMEORIGIN'
    res.headers['X-XSS-Protection'] = '1; mode=block'
    res.headers['Server'] = 'ASD'
    return res

'''
[GET][OUT]
Opposite of /getvalue/
Accept request from DT2, response with a value for DT2
'''
#allow others to send a get request and get a value [GET][external]
@app.get("/sendvalue")
def sendvalue():
    # if len(valueRanges) == 1:
    #     value = simHelper.generateValue(valueRanges[0][0],valueRanges[0][1])
    # elif len(valueRanges) > 1:
    #     selectRange = random.randint(0,len(valueRanges)-1)
    #     value = simHelper.generateValue(valueRanges[selectRange][0],valueRanges[selectRange][1])
    if delayResponse():
        sleep(delayTime())
    senderDT_ID = request.args.get('dt_id')
    if senderDT_ID == "":
        senderDT_ID = -111111111
    value = generateValue()
    dbHelper.insertDataSentTbl('GET',senderDT_ID,app.config['getoutID'],value)
    res = make_response(jsonify({"value": value, "DT_ID" : app.config['DT_ID'], "API_ID": app.config['getoutID']}),200)
    res.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    res.headers['Content-Security-Policy'] = "default-src 'self'"
    res.headers['X-Content-Type-Options'] = 'nosniff'
    res.headers['X-Frame-Options'] = 'SAMEORIGIN'
    res.headers['X-XSS-Protection'] = '1; mode=block'
    return res
    #multiple range array index outbound check

#@app.get("/std")
def calculateStdev():
    try:
        connectedDTs = dbHelper.getConnectedDTs()
        for c in connectedDTs:
            #print(c[0])
            values = dbHelper.getAllValuesFromDT(c[0])
            val = []
            for v in  values:
                val.append(v[0])
            #print(values[0]["value"])
            stdValue = round(statistics.stdev(val),3)
            dbHelper.addStdevValue(str(c[0]),stdValue)
            print("DT ID ", str(c[0])," STDEV ", str(stdValue))
    except Exception as e:
        print("calculateStdev ",str(e))
    return "okay"

def calculateQoSStdev():
    try:
        connectedDTs = dbHelper.getConnectedQoSDTs()
        for c in connectedDTs:
            #print(c[0])
            values = dbHelper.getQoSFromDT(c[0])
            val = []
            for v in  values:
                val.append(v[0])
            #print(values[0]["value"])
            stdValue = round(statistics.stdev(val),3)
            dbHelper.addQoSStdevValue(str(c[0]),stdValue)
            print("QoS DT ID ", str(c[0])," STDEV ", str(stdValue))
    except Exception as e:
        print("calculateStdev ",str(e))
    return "okay"

@app.get("/final")
def genFinal():
    generateFinalValues()
    return "okay"

def generateFinalValues():
    qos_connectedDTs = dbHelper.getConnectedQoSDTs()
    connectedDTs = dbHelper.getConnectedDTs()
    resQoS = []
    for c in qos_connectedDTs:
        qos_values = dbHelper.getQoSFromDT(c[0])
        val = []
        for v in qos_values:
            val.append(v[0])
        stdValue = round(statistics.stdev(val),4)
        dbHelper.addFinalValueTbl(str(c[0]),'QoS',stdValue,str(min(val)),str(max(val)),str(round(statistics.mean(val),3)))
        # resQoS.append("DT_ID "+str(c[0])+" QoS STD: "+str(stdValue))
        # resQoS.append("DT_ID "+str(c[0])+" QoS min: "+str(min(val)))
        # resQoS.append("DT_ID "+str(c[0])+" QoS max: "+str(max(val)))
        # resQoS.append("DT_ID "+str(c[0])+" QoS avg: "+str(round(statistics.mean(val),3)))
    resDTValues = []
    for c in connectedDTs:
        dt_values = dbHelper.getAllValuesFromDT(c[0])
        val = []
        for v in dt_values:
            val.append(v[0])
        stdValue = round(statistics.stdev(val),4)
        dbHelper.addFinalValueTbl(str(c[0]),'Values',stdValue,str(min(val)),str(max(val)),str(round(statistics.mean(val),3)))
        # resDTValues.append("DT_ID "+str(c[0])+" Val STD: "+str(stdValue))
        # resDTValues.append("DT_ID "+str(c[0])+" Val min: "+str(min(val)))
        # resDTValues.append("DT_ID "+str(c[0])+" Val max: "+str(max(val)))
        # resDTValues.append("DT_ID "+str(c[0])+" Val avg: "+str(round(statistics.mean(val),3)))
    
    formula_final_values = dbHelper.getFormulaCalTbl()
    temp = []
    res_formula_values=[]
    for v in formula_final_values:
        temp.append(v[1])
    stdValue = round(statistics.stdev(temp),4)
    dbHelper.addFinalValueTbl(app.config['DT_ID'],'Final',stdValue,str(min(temp)),str(max(temp)),str(round(statistics.mean(temp),3)))



    # res_formula_values.append("Final Val STD: "+str(stdValue))
    # res_formula_values.append("Final Val min: "+str(min(temp)))
    # res_formula_values.append("Final Val max: "+str(max(temp)))
    # res_formula_values.append("Final Val avg: "+str(round(statistics.mean(temp),3)))
    # print(resQoS)
    # print(resDTValues)
    # print(res_formula_values)
    print("Final Results created.")
    return "okay"



def DT_evaluation():
    connectedDTs = dbHelper.getConnectedDTs()
    value_std_low_counter = 0
    value_std_mid_counter = 0
    value_std_high_counter = 0
    qos_std_low_counter = 0
    qos_std_mid_counter = 0
    qos_std_high_counter = 0

    std_low_mark = 2
    std_mid_mark = 5

    evaluation = ""
    for c in connectedDTs:
        #print(c[0])
        std_values = dbHelper.getStdValuesFromDT(c[0])
        qos_values = dbHelper.getStdValuesFromDT(c[0])
        val = []
        evaluation = app.config['evaluation_msg']
        for v in  std_values:
            if v[0] <= std_low_mark:
                value_std_low_counter = value_std_low_counter + 1
            elif v[0] <= std_mid_mark:
                value_std_mid_counter = value_std_mid_counter + 1
            else:
                value_std_high_counter = value_std_high_counter +1
        
        for v in qos_values:
            if v[0] <= std_low_mark:
                qos_std_low_counter = qos_std_low_counter + 1
            elif v[0] <= std_mid_mark:
                qos_std_mid_counter = qos_std_mid_counter + 1
            else:
                qos_std_high_counter = qos_std_high_counter +1
        
        evaluation = evaluation + "DT_ID: "+str(c[0])+" std value evaluation=> low: "+str(value_std_low_counter)+" mid: "+str(value_std_mid_counter)+" high: "+str(value_std_high_counter)
        evaluation = evaluation + "________________"
        evaluation = evaluation + "  DT_ID: "+str(c[0])+" QoS std value evaluation=> low: "+str(qos_std_low_counter)+" mid: "+str(qos_std_mid_counter)+" high: "+str(qos_std_high_counter)
        evaluation = evaluation + "________________"
    app.config.update(
        evaluation_msg = evaluation
    )
    print("evaluation done")
        # stdValue = round(statistics.stdev(val),3)
        # dbHelper.addQoSStdevValue(str(c[0]),stdValue)
        # print("QoS DT ID ", str(c[0])," STDEV ", str(stdValue))
    return "okay"

@app.get("/sendreport")
def callSendReportDTTSA():
    res = sendReportDTTSA()
    return str(res)

def sendReportDTTSA():
    data = dbHelper.getFinalValueTbl()
    report = [{
        "dt_id" : d[0],
        "data_type" : d[1],
        "stdev_value": d[2],
        "min": d[3],
        "max": d[4],
        "avg": d[5]
    } for d in data]
    payload = {"dt_id": app.config['DT_ID'],"dt_type": app.config['dt_type'], "report": report }
    res = requests.post('http://'+ app.config['DTTSA_IP'] +':9000/report',json= payload)
    msg = ""
    if res.status_code == 200:
        msg = "DTTSA submitted"
    else:
        msg = "DTTSA Failed"
    print(msg)
    return msg

# data_type = str(r['data_type'])
#                 stdev_value = str(r['stdev_value'])
#                 min = str(r['min'])
#                 max = str(r['max'])
#                 avg = str(r['avg'])

#send DTTSA, DT subscriptions from other DTs [Internal Subs]
@app.get("/sendsubs")
def sendSubsToDTTSA():
    subList = dbHelper.getSubscriptionInfo("i")
    # sub_dt_id = str(sub['sub_dt_id'])
    #                 sub_api_id = str(sub['sub_api_id'])
    #                 url = str(sub['url'])
    #                 type= str(sub['req_type'])
    subs = [
        {
            "sub_dt_id": sub[3],
            "sub_api_id": sub[4],
            "url": sub[5],
            "req_type": sub[2]
        } for sub in subList]
    payload = {"dt_id": app.config['DT_ID'] , "sublist" : subs}
    res = requests.post('http://'+ app.config['DTTSA_IP'] +':9000/sublist',json= payload)
    return make_response(res.text,200)

def DTSimulation():
    print("DT Simulation Started")
    url = "http://"+str(app.config['local_IP'])+":" + str(app.config['port'])
    res = requests.get(url+"/cal")
    #print(res.text)
    url = "http://"+str(app.config['local_IP'])+":" + str(app.config['port'])
    res = requests.get(url+"/sendothers")
    #print(res.text)
    rows = dbHelper.getFormulaCalTbl()

    if len(rows)%5 == 0:
        calculateStdev()
        calculateQoSStdev()

    if len(rows) >= 15:
        DT_evaluation()
        generateFinalValues()
        sendReportDTTSA()
        #print("DT type: "+ str(app.config['dt_type']))
        scheduler.remove_job("DTSimulation")



def DTStart():
    print("DTStarted")
    print("DT type: "+ str(app.config['dt_type']))
    # app.config['dt_reg_state'] = False
    # app.config['sub_in_state'] = False
    # app.config['send_sub_DTTSA_state'] = False
    url = "http://"+str(app.config['local_IP'])+":" + str(app.config['port'])
    if app.config['dt_reg_state'] == False:
        res = requests.get(url+"/dtreg")
        #print(res.status_code)
        if res.status_code == 200:
            app.config.update(
                dt_reg_state = True
            )

    if app.config['dt_reg_state'] == True and app.config['sub_in_state'] == False:
        res = requests.get(url+"/subin")
        if res.status_code == 200:
            app.config.update(
                sub_in_state = True
            )

    if app.config['dt_reg_state'] == True and app.config['sub_in_state'] == True and app.config['send_sub_DTTSA_state'] == False:
        res = requests.get(url+"/sendsubs")
        if res.status_code == 200:
            app.config.update(
                send_sub_DTTSA_state = True
            )

    if app.config['dt_reg_state'] and app.config['sub_in_state'] and app.config['send_sub_DTTSA_state']:
        scheduler.remove_job("DTStart")
        print("DT start job removed")
        timeInterval = random.randint(5,10)
        print("time interval: "+ str(timeInterval))
        scheduler.add_job(id="DTSimulation", replace_existing=True, func=DTSimulation,trigger="interval",seconds = timeInterval)


def runSchedulerJobs():
    print("SchedularJobs Initiated")
    timeInterval = random.randint(10,20)
    print("time interval: "+ str(timeInterval))
    scheduler.add_job(id="DTStart", replace_existing=True, func=DTStart,trigger="interval",seconds = timeInterval)
    
    scheduler.start()

def start_server(args):
    app.config.update(
        port = args.port
    )
    runSchedulerJobs()
    app.run(host='0.0.0.0',port=args.port)
    

def main(args):
    dbHelper.createDB(args.db)
    start_server(args)

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-port') #python3 dt.py -port <port>
    parser.add_argument('-db')
    args = parser.parse_args()
    main(args)