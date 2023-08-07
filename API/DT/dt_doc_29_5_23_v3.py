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
from dt_simulation_helper import Simulation
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import re
from flask_apscheduler import APScheduler
import statistics
import sys
from dt_logic import DTLogic


app = Flask(__name__)

config = configparser.ConfigParser()
config.read('environment_config.ini')

#DT setup
hostname = socket.gethostname()
IPAddress = socket.gethostbyname(hostname)
localIP = IPAddress
app.config['service_url'] = "notsetyet.com"
app.config['local_IP'] = str(app.config['service_url'])
app.config['DT_ID'] = -1 #initially setting value to -1 to indicate that DT is not yet registered. positive value upon registration
app.config['backup_IP'] = "" #no initial backup server will be deploy
app.config['port'] = 9100
app.config['getinID'] = -1
app.config['getoutID'] = -1
app.config['postinID'] = -1
app.config['postoutID'] = -1
app.config['dt_type'] = "n"
app.config['evaluation_msg'] = "n"


URL_pattern_regex = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,4})')
#traffic_delay = 1 #delay function to mimic network traffic
app.config['init_details_setup_state'] = False
app.config['dt_reg_state'] = False
app.config['sub_in_state'] = False
app.config['send_sub_DTTSA_state'] = False
app.config['execution_finished'] = False

#random DT data generation
organizationList = ['TORG_1','TORG_2','TORG_3','TORG_4','TORG_5','TORG_6'] #env 
DTIDList = ['DT_1','DT_2','DT_3','DT_4','DT_5','DT_6'] #env
DTNameList = ['Robotic Arm','Conveyor Belt'] #env
DTDesList = ['Robotic Arm', 'Conveyor Belt'] #env

#get values from env variables
if os.environ.get('rand_seed') is None:
    print("date rand dt type")
    app.config['rand_seed'] = datetime.now().timestamp()
else:
    print("env rand dt type")
    app.config['rand_seed'] = os.environ['rand_seed']

if os.environ.get('org_code') is None:
    org_code = organizationList[random.randint(0,5)]
    app.config['org_code'] = organizationList[random.randint(0,5)]
else:
    org_code = os.environ['org_code']
    app.config['org_code'] = os.environ['org_code']

if os.environ.get('dt_code') is None:
    DT_code = DTIDList[random.randint(0,5)]
    app.config['dt_code'] = DTIDList[random.randint(0,5)]
else:
    DT_code = os.environ['dt_code']
    app.config['dt_code'] = os.environ['dt_code']

if os.environ.get('dt_name') is None:
    DT_name = DTNameList[random.randint(0,1)]
    app.config['dt_name'] = DTNameList[random.randint(0,1)]
else:
    DT_name = os.environ['dt_name']
    app.config['dt_name'] = os.environ['dt_name']

if os.environ.get('dt_desc') is None:
    DT_Description = DTDesList[random.randint(0,1)]
    app.config['dt_desc'] = DTDesList[random.randint(0,1)]
else:
    DT_Description = os.environ['dt_desc']
    app.config['dt_desc'] = os.environ['dt_desc']

if os.environ.get('dttsa_IP') is None:
    app.config['DTTSA_IP'] =  "https://dttsa-dvi6vsq74a-uc.a.run.app" #"host.docker.internal"
    # app.config['DTTSA_IP'] =  "http://127.0.0.1:9000"
else:
    app.config['DTTSA_IP'] = os.environ['dttsa_IP']

if os.environ.get('num_iterations') is None:
    num_iterations = 15
    app.config['num_iterations'] = 15
else:
    num_iterations = int(os.environ['num_iterations'])
    app.config['num_iterations'] = int(os.environ['num_iterations'])

if os.environ.get('num_dts') is None:
    num_DTs = 12
    app.config['num_dts'] = 12
else:
    num_DTs = int(os.environ['num_dts'])
    app.config['num_dts'] = int(os.environ['num_dts'])

if os.environ.get('CDT_goal') is None:
    CDT_goal = "min"
    app.config['cdt_goal'] = "min"
else:
    CDT_goal = os.environ['CDT_goal']
    app.config['cdt_goal'] = os.environ['CDT_goal']

if os.environ.get('dt_type') is None:
    # n= normal, m= malicious, c=changing
    dt_types = ['n','m','c']
    app.config.update(
        dt_type = random.choice(dt_types)
    )
    print("dt type: "+ app.config['dt_type'])
else:
    app.config.update(
        dt_type = os.environ['dt_type']
    )

#support objects
dbHelper = DBHelper()
simHelper = Simulation(num_iterations,num_DTs,CDT_goal,app.config['dt_type'],app.config['rand_seed'])
numVariables,num_internal_variable,num_external_variable,formula,externalVarLocations = simHelper.generateFormula()
valueRanges = simHelper.generateRandomValueRanges()
scheduler = APScheduler()
scheduler.init_app(app)
dtLogic = DTLogic(dbHelper,num_iterations,num_DTs,CDT_goal,app.config['dt_type'],app.config['rand_seed'])

def dttsaURL():
    return app.config['DTTSA_IP']

'''
Get Subscribers list.
/getsublist?type=i for internal e for external
'''
@app.get('/getsublist')
def getSavedSubList():
    typeofSubs = request.args.get('type') #i for internal. e for external
    if typeofSubs == "i":
        subs = dtLogic.getInternalSubs()
    else:
        subs = dtLogic.getExternalSubs()
    return {"Total records": len(subs),"subList":subs}

'''
Generate values based on the DT value ranges
'''
@app.get('/genVal')
def testGenValue():
    r = dtLogic.generateValue()
    return str(r)

'''
Get DT formula
'''
@app.get('/getformula')
def getFormulaDetails():
    return {
        "Num var":numVariables,
        "Num In var":num_internal_variable,
        "Num Out var":num_external_variable,
        "Formula":formula
    }

'''
Get DT Execution Status
'''
@app.get('/status')
def getDTStatus():
    formula_cal = len(dbHelper.getFormulaCalTbl())

    res = make_response(jsonify({
        "dt_id" : app.config['DT_ID'],
        "status": app.config['execution_finished'],
        "iteration_count": str(formula_cal)
    }),200)
    return res

'''
Get other connect DTs status
'''
@app.get('/otherstat')
def getOtherDTStatus():
    getSubs = dbHelper.getSubscriptionInfo('e')
    all_done = True
    if len(getSubs) > 0:
        for sub in getSubs:
            #url = URL_pattern_regex.search(sub[5])[0]
            res = requests.get(sub[6]+'/status')
            #print(res.text)
            data = json.loads(res.text)
            #print(data['status'])
            if data['status'] == False:
                all_done = False
    return str(all_done)


'''
register DT with DTTSA
'''
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
        "DT_IP": str(app.config['service_url']),
        "APIs": api_array}
    jsonObject = jsonify(dictToSend)
    # res = requests.post('http://'+ app.config['DTTSA_IP'] +':9000/DTReg', json= dictToSend)
    res = requests.post(dttsaURL()+'/DTReg', json= dictToSend)
    return res.text #only get the text part of the response there are more

@app.get('/dtreg')
def DTregService(): 
    GET_in_URL = str(app.config['service_url'])+"/getvalue/"
    GET_out_URL = str(app.config['service_url'])+"/sendvalue"
    POST_out_URL = str(app.config['service_url'])+"/sendpost/"
    POST_in_URL = str(app.config['service_url'])+"/getpost/"
    if app.config['DT_ID'] == -1:
        response = DTreg(GET_in_URL,GET_out_URL,POST_out_URL,POST_in_URL)
        obj1 = json.loads(response)
        
        app.config.update(
            DT_ID = obj1[0]["DT_ID"]
        )
        dtLogic.setDTID(app.config['DT_ID'])
        # APIs = requests.get('http://'+ app.config['DTTSA_IP'] +':9000/getownapis?dt_id='+str(app.config['DT_ID']))
        APIs = requests.get(dttsaURL()+'/getownapis?dt_id='+str(app.config['DT_ID']))
        apiList = APIs.json()['APIs']

        for api in apiList:
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
        dbHelper.addDTDetails(app.config['DT_ID'],app.config['dt_type'],str(app.config['service_url']))
    else:
        response = {"DT_ID": "All ready registed","status": "Failed"},400
    return response

'''
allow other DTs to register their service subscriptions
/sub?dt_id=<ext_DT>&api_id=<api_id>&req=GET&url=127.0.0.1/service
'''
@app.route('/sub')
def recordExternalSub():
    subDT_ID = request.args.get('dt_id')    #DT ID of the External DT
    subAPI_ID = int(request.args.get('api_id'))  #API ID of the subscribing API
    subReq_type = request.args.get('req')   #request type
    subURL = request.args.get('url')        #URL need to response
    ex_dt_url = request.args.get('dt_url') #External_dt URL
    
    if app.config['getinID'] != -1 and app.config['getoutID'] != -1 and app.config['postinID'] != -1 and app.config['postoutID'] != -1:
        if subAPI_ID in (app.config['getinID'],app.config['getoutID'],app.config['postinID'],app.config['postoutID']):
            dbHelper.addExternalSub(subReq_type,subDT_ID,subAPI_ID,subURL,ex_dt_url)
            response = {"msg": "Subscribed successfully","status": "Success"},200
        else:
            response = {"msg": "API ID is not in the range of DTs possible APIs","status": "Failed"},400
    else:
        response = {"msg": "DT, APIs did not have IDs","status": "Failed"},400
    return response

'''
based on the DT formula subscribe to external DT APIs for formula calculations
'''
@app.route('/subin')
def recordInternalSub():
    # APIs = requests.get('http://'+ app.config['DTTSA_IP'] +':9000/getapis?dt_id='+str(app.config['DT_ID']))
    APIs = requests.get(dttsaURL()+'/getapis?dt_id='+str(app.config['DT_ID']))
    
    try:
        apiList = APIs.json()['APIs']
        print(apiList)
        print(externalVarLocations)
        for varLocation in externalVarLocations:
            
            selectedIndex = random.choice(apiList)
            dbHelper.addInternalSub(selectedIndex['type'],selectedIndex['DT_ID'],selectedIndex['API_ID'],selectedIndex['URL'],varLocation)
            #TODO local env use IPs and using a regex IP extracted. cloud env need full
            # temp_DT_IP = URL_pattern_regex.search(selectedIndex['URL'])[0]
            sub_dt_url = URL_pattern_regex.search(selectedIndex['URL'])[0]
            print(sub_dt_url)
            if selectedIndex['type'] == 'POST':
                url = str(app.config['service_url']) +"/getpost/"
            else:
                url = selectedIndex['URL']
            # print('http://'+ temp_DT_IP +'/sub?dt_id='+ str(app.config['DT_ID'])+'&api_id='+ str(selectedIndex['API_ID'])+'&url='+url+'&req='+selectedIndex['type']+'&dt_url='+ str(app.config['service_url']))
            # res = requests.get('http://'+ sub_dt_url +'/sub?dt_id='+ str(app.config['DT_ID'])+'&api_id='+ str(selectedIndex['API_ID'])+'&url='+url+'&req='+selectedIndex['type']+'&dt_url='+ str(app.config['service_url']))
            res = requests.get('http://'+ sub_dt_url +'/sub?dt_id='+ str(app.config['DT_ID'])+'&api_id='+ str(selectedIndex['API_ID'])+'&url='+url+'&req='+selectedIndex['type']+'&dt_url='+ str(app.config['service_url']))

        res = {"msg": "Sucess"}
        return make_response(res,200)
    except Exception as e:
        print(e)
        res = {"msg": "No APIs yet"}
        return make_response(res,400)

'''
Calculate formula value and save in the local DB
'''
@app.route('/cal')
def calculateFormula():
    allSubGETRequests = dbHelper.getInternalGETSubs()
    
    for sub in allSubGETRequests:
        res = requests.get(sub[5]+"?dt_id"+str(app.config['DT_ID']))
        data  = json.loads(res.text)
        dbHelper.insertQoSTbl(sub[3],sub[4],res.elapsed.total_seconds())
        
        dbHelper.insertDataTbl("GET",data['DT_ID'],data['API_ID'],data['value'])
        
    allInternalSubs = dbHelper.getSubscriptionInfo("i")
    
    internalSubValues = []
    internalDTGenValues = []
    internalUsedSubValues = []
    for internalSub in allInternalSubs:
        data = dbHelper.getvaluesToCalculate(internalSub['DT_ID'],internalSub['API_ID'])
        for d in data:
            
            internalSubValues.append({'ID': d['id'],'value': d['value']})
        
    formulaCalculatedValue = -1111111 #this will indicate still not calculated
    if num_external_variable == len(internalSubValues):
        
        internalSubValuesCounter = 0
        for i in range(2, len(formula) - 1):
            v1 = 0
            v2 = 0
            if i == 2:
                if formula[i] == "$":
                    v1 = dtLogic.generateValue()
                    internalDTGenValues.append({'pos': i, 'val': v1 })
                else:
                    v1 = int(internalSubValues[internalSubValuesCounter]["value"])
                    internalUsedSubValues.append({'pos': i, 'val': v1 })
                    internalSubValuesCounter = internalSubValuesCounter + 1
                
                if formula[i+2] == "$":
                    v2 = dtLogic.generateValue()
                    internalDTGenValues.append({'pos': i+2, 'val': v2 })
                else:
                    v2 = int(internalSubValues[internalSubValuesCounter]["value"])
                    internalUsedSubValues.append({'pos': i+2, 'val': v2 })
                    internalSubValuesCounter = internalSubValuesCounter + 1
                #print(str(v1),str(v2),formula[i + 1])
                formulaCalculatedValue = dtLogic.calculatevalues(v1,v2,formula[i + 1])         
            if i >= 5:
                if i % 2 != 0:
                    if formula[i+1] == "$":
                        v1 = dtLogic.generateValue()
                        internalDTGenValues.append({'pos': i+1, 'val': v1 })
                    else:
                        v1 = int(internalSubValues[internalSubValuesCounter]["value"])
                        internalSubValuesCounter = internalSubValuesCounter + 1
                        internalUsedSubValues.append({'pos': i+1, 'val': v1 })
                    
                    formulaCalculatedValue = dtLogic.calculatevalues(formulaCalculatedValue,v1,formula[i])
    for i in internalSubValues:
        dbHelper.updateDataTable(i["ID"])
    for_id = dbHelper.addFormulaCalculation(str(formula),formulaCalculatedValue)
    for i in internalDTGenValues:
        dbHelper.addDTGenData(for_id,i["pos"],i["val"])
        dbHelper.addCalValueData(for_id,i["pos"],i["val"],"i")
    for i in internalUsedSubValues:
        dbHelper.addCalValueData(for_id,i["pos"],i["val"],"e")
    
    res = {"msg": str(formulaCalculatedValue)}
    return make_response(res,200)

'''
Send values to other DTs by checking external subs local table
Only sending POST requests. GET requests are responsibility of the subscribe DT
'''
@app.route('/sendothers')
def sendValuesToOtherDTs():
    res = {"status" : "success", "msg" : "No POST subscribers"}
    allPOSTSubs = dbHelper.getExternalPOSTSubs()
    if len(allPOSTSubs) > 0:
        for sub in allPOSTSubs:
            value = dtLogic.generateValue()
            msgToSend = {
            "value": value,
            "DT_ID": app.config['DT_ID'],
            "API_ID": app.config['postoutID']
            }
            jsonObj = jsonify(msgToSend)
            tempURL = sub[5]
            sub_dt_id = sub[3]
            headers = {'access-token':'test val'}
            res = requests.post(tempURL,json=msgToSend,headers=headers)
            dbHelper.insertQoSTbl(sub_dt_id,99,res.elapsed.total_seconds())
            dbHelper.addTransaction("DT: "+ str(app.config['DT_ID'])+ " API_ID: "+ str(app.config['postoutID']) + "send value to " + res.text)
            dbHelper.insertDataSentTbl('POST',sub_dt_id,str(app.config['postoutID']),value)
            res = res.text
    return make_response(res,200)

'''
Load DT dashboard
'''
@app.route('/')
def index():
    allTransRecords = dbHelper.getAllTransactionTbl()
    allDataRecords = dbHelper.getAllDataTbl()
    allQoSData = dbHelper.getQoSDataForDT()
    d = dbHelper.getFormulaCalTbl()
    data = []
    for i in d:
        data.append(tuple(i))
    labels = [row[0] for row in data]
    values = [row[1] for row in data]

    d2 = dbHelper.getDataSentTbl()
    data2 = []
    for i in d2:
        data2.append(tuple(i))
    labels2 = [row[0] for row in data2]
    values2 = [row[1] for row in data2]

    return render_template('index.html',allQoSData=allQoSData,labels2=labels2,values2=values2,evaluation=app.config['evaluation_msg'],labels=labels,values=values,allDataRecords=allDataRecords, allTransRecords=allTransRecords,org_code=org_code,IP= app.config['service_url'],dt_id=app.config['DT_ID'])

'''
Display DT details
'''
@app.route('/details')
def details():
    dbHelper.addTransaction("/detalis called")
    return json.dumps({
        'Organization' : org_code,
        'IP' : localIP,
        'DT_name' : DT_name,
        'DT_Description' : DT_Description,
        'DT_ID':app.config['DT_ID'],
        'DT_IP': app.config['service_url'],
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

'''
#set DT internal parameter values
#/setvalues?dttsa_ip=127.0.0.1&local_ip=127.0.0.1
'''
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


'''
[POST][IN]
Allowing others to send values using POST
'''
@app.post("/getpost/")
def submitvalue():
    content = request.get_json()
    if dtLogic.delayResponse():
        sleep(dtLogic.delayTime())
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
            res = dtLogic.createResponseHeaders(res)
            return res
        
        dbHelper.insertDataTbl('POST',senderDT,API_ID,value)
        msg = {"status" : "success", "msg" : f"received {value} from sender  {senderDT} using API {API_ID}"}
        payload = msg
        if 'access-token' in request.headers:
            res = make_response(jsonify(payload),200)#200
        else:
            res = make_response(jsonify(payload),406)#200
        res = dtLogic.createResponseHeaders(res)
        return res
    except:
        msg = {"status": "Failed"}
        payload = msg
        res = make_response(jsonify(payload),406)
        res = dtLogic.createResponseHeaders(res)
        return res

'''
[POST][OUT]
Make a post to DT2.
'''
@app.post("/sendpost/")
def postother():
    content = request.get_json()
    if dtLogic.delayResponse():
        sleep(dtLogic.delayTime())
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
            res = dtLogic.createResponseHeaders(res)
            return res
    except:
        msg = {"status": "Failed"}
        payload = msg
        res = make_response(jsonify(payload),406)
        res = dtLogic.createResponseHeaders(res)
        return 
    msgToSend = {
        "value": dtLogic.generateValue(),
        "DT_ID": app.config['DT_ID'],
        "API_ID": app.config['postoutID']
    }
    
    jsonObj = jsonify(msgToSend)
    headers = {'access-token':'test val'}
    url = str(app.config['service_url'])+"/getpost/"
    
    rest = requests.post(url,json=msgToSend,headers=headers)
    payload = {"status" : "success"}
    if 'access_token' in request.headers:
        res = make_response(jsonify(payload),200)#200
    else:
        res = make_response(jsonify(payload),406)#200
    res = dtLogic.createResponseHeaders(res)
    return res


'''
[GET][In]
DT1 will request DT2 to send a value. 
Response will carry the value for calculation
serviceURL will be DT2 IP+Service
'''
@app.get("/getvalue/")
def getvalue():
    if dtLogic.delayResponse():
        sleep(dtLogic.delayTime())
    
    getServiceURL = str(app.config['service_url'])+"/sendvalue"
    res = requests.get(getServiceURL)
    
    payload = res.text
    res = make_response(jsonify(payload),200)
    res = dtLogic.createResponseHeaders(res)
    return res

'''
[GET][OUT]
Opposite of /getvalue/
Accept request from DT2, response with a value for DT2
'''
#allow others to send a get request and get a value [GET][external]
@app.get("/sendvalue")
def sendvalue():
    if dtLogic.delayResponse():
        sleep(dtLogic.delayTime())
    senderDT_ID = request.args.get('dt_id')
    if senderDT_ID == "":
        senderDT_ID = -111111111
    value = dtLogic.generateValue()
    dbHelper.insertDataSentTbl('GET',senderDT_ID,app.config['getoutID'],value)
    res = make_response(jsonify({"value": value, "DT_ID" : app.config['DT_ID'], "API_ID": app.config['getoutID']}),200)
    res = dtLogic.createResponseHeaders(res)
    return res

'''Generate final values for the DT '''
@app.get("/final")
def genFinal():
    dtLogic.generateFinalValues()
    return "okay"

'''Send Final report to DTTSA'''
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
    # res = requests.post('http://'+ app.config['DTTSA_IP'] +':9000/report',json= payload)
    res = requests.post(dttsaURL() +'/report',json= payload)
    msg = ""
    if res.status_code == 200:
        msg = "DTTSA submitted"
    else:
        msg = "DTTSA Failed"
    print(msg)
    return msg

@app.get("/test")
def testService():
    dtLogic.trendAnalysisExDTData()
    return "Ok"

'''
#send DTTSA, DT subscriptions from other DTs [Internal Subs]
'''
@app.get("/sendsubs")
def sendSubsToDTTSA():
    subList = dbHelper.getSubscriptionInfo("i")
    subs = [
        {
            "sub_dt_id": sub[3],
            "sub_api_id": sub[4],
            "url": sub[5],
            "req_type": sub[2]
        } for sub in subList]
    payload = {"dt_id": app.config['DT_ID'] , "sublist" : subs}
    # res = requests.post('http://'+ app.config['DTTSA_IP'] +':9000/sublist',json= payload)
    res = requests.post(dttsaURL() +'/sublist',json= payload)
    return make_response(res.text,200)

def waitUntilOtherDTs():
    print("Waiting until other DT finish")
    status = getOtherDTStatus()
    if status == 'True':
        print('All DT finished')
        if saveCSV():
            scheduler.remove_job("waitUntilOtherDTs")
            print("CSVs saved")
    else:
        url = str(app.config['service_url'])
        res = requests.get(url+"/sendothers")

'''
Main DT simulation logic
'''
def DTSimulation():
    print("DT Simulation Started")
    url = str(app.config['service_url'])
    res = requests.get(url+"/cal")
    
    url = str(app.config['service_url'])
    res = requests.get(url+"/sendothers")
    
    rows = dbHelper.getFormulaCalTbl()

    if len(rows)%5 == 0:
        dtLogic.calculateStdev()
        dtLogic.calculateQoSStdev()
        dtLogic.trendAnalysisExDTData()

    if len(rows) >= num_iterations:
        dtLogic.DT_evaluation()
        dtLogic.generateFinalValues()
        dtLogic.trendAnalysisExDTData()
        #dbHelper.saveDataAsCSV(app.config['DT_ID'])
        sendReportDTTSA()
        scheduler.remove_job("DTSimulation")
        app.config.update(
            execution_finished = True
        )
        timeInterval = random.randint(10,20)
        scheduler.add_job(id="waitUntilOtherDTs", replace_existing=True, func=waitUntilOtherDTs,trigger="interval",seconds = timeInterval)

@app.get("/save")
def saveCSV():
    res = dbHelper.saveDataAsCSV(app.config['DT_ID'])
    return res


@app.route('/restart')
def restartService():
    os._exit(0)

'''
Initial DT setup
["dt_type="+dt_type,"CDT_goal=min","num_dts=12","num_iterations=15","dttsa_IP="+str(dttsa_ip),"rand_seed="+str(random_seed)]
'''
@app.post("/setup")
def initDTSetup():
    content = request.get_json()
    try:
        # dt_type = content['dt_type']
        # cdt_goal = content['cdt_goal']
        # num_dts = content['num_dts']
        # num_iterations = content['num_iterations']
        # rand_seed = content['rand_seed']
        service_url = content['url']
        dttsa_url = content['dttsa_url']
        
        app.config.update(
            service_url = service_url
        )

        app.config.update(
            DTTSA_IP = dttsa_url
        )

        # app.config.update(
        #     rand_seed = rand_seed
        # )

        
        #TODO only main parameters are set. others are not that important in this phase.
        # app.config['rand_seed']
        # app.config['org_code']
        # app.config['dt_code']
        # app.config['dt_name']
        # app.config['dt_desc']
        # app.config['num_iterations']
        # app.config['num_dts']
        # app.config['cdt_goal']
        # app.config['dt_type']

        #random.seed(app.config['rand_seed'])

        msg = {"status": "Done", "service url" : app.config['service_url'], "dttsa_url": app.config['DTTSA_IP'], "dt_type":  app.config['dt_type'] }

        app.config.update(
            init_details_setup_state = True
        )

    except:
        msg = {"status": "Failed"}
        payload = msg
        res = make_response(jsonify(payload),406)
        res = dtLogic.createResponseHeaders(res)
        return msg
    
    return msg


'''
DT startup process
'''
def DTStart():
    print("DTStarted")

    if app.config['init_details_setup_state'] != False:
        print("DT type: "+ str(app.config['dt_type']))
        url = str(app.config['service_url'])
        if app.config['dt_reg_state'] == False:
            res = requests.get(url+"/dtreg")
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
    else:
        print("Waiting for initial DT setup")

def runSchedulerJobs():
    print("SchedularJobs Initiated")
    timeInterval = random.randint(10,20)
    print("time interval: "+ str(timeInterval))
    scheduler.add_job(id="DTStart", replace_existing=True, func=DTStart,trigger="interval",seconds = timeInterval)
    
    scheduler.start()

def start_server(args):
    #TODO manual port set
    app.config.update(
        port = "9100"
    )
    # app.config.update(
    #     port = args.port
    # )
    runSchedulerJobs()
    app.run(host='0.0.0.0',port=9100)
    

def main(args):
    #TODO manual db name set
    dbHelper.createDB("data1.db")
    # dbHelper.createDB(args.db)
    # behaviour_edits = config["behaviour"]
    # behaviour_edits["normal_limit"] = args.nl
    # with open('environment_config.ini','w') as configfile:
    #     config.write(configfile)
    start_server(args)

if __name__ == '__main__':
    print("start")
    #TODO remove cmd arguments and set it through env variables
    from argparse import ArgumentParser
    parser = ArgumentParser()
    #TODO commented out the parameter passing easy cloud deployment
    # parser.add_argument('-port') #python3 dt.py -port <port>
    # parser.add_argument('-db')
    # parser.add_argument('-nl')
    args = parser.parse_args()
    main(args)