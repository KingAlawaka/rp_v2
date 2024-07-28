from cProfile import run
from crypt import methods
from lib2to3.pytree import type_repr
from re import L
from sched import scheduler
import socket
from urllib import response
#from click import password_option
import psycopg2
from flask import Flask, jsonify,render_template,request,url_for,redirect,session,make_response,Response,send_file
import hashlib
import requests
from sqlalchemy import null
from flask_apscheduler import APScheduler
import configparser
import time
import threading
from flask_cors import CORS
import networkx as nx
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
import os
import io
import random
import json
from analytics_logic import AnalyticSupportService
import psutil
from datetime import datetime

app = Flask(__name__,template_folder="../Dashboardnew/templates", static_folder="../Dashboardnew/static")
CORS(app)

config = configparser.ConfigParser()
config.read('environment_config.ini')

app.config['firefly_url'] = config['servers']['firefly_service_url']
app.config['policy_id'] = "c8c06dee-c2c6-4e51-a405-ae19591c44b0"

analyticsSupportService = AnalyticSupportService()

@app.route("/getstatus")
def getOperationStatus():
    cpu_usage = psutil.cpu_percent()
    mem_usage = psutil.virtual_memory().percent
    msg = "Ok"
    if cpu_usage > 80 or mem_usage > 80:
        msg = "Warning"
    return jsonify(cpu_usage=cpu_usage, mem_usage=mem_usage, msg=msg)    

@app.route("/getrepattacks")
def getRepAttacks():
    getDTTypes = analyticsSupportService.getDTTypePrediction()

    dt_types = ['','','','','','']

    for t in getDTTypes:
        dt_types[t[0]] = t[1]

    # print(dt_types)

    rep_attacks_count = 0
    rep_all_attacks = analyticsSupportService.getRepAttacks()
    rep_attacks = []

    for i,r in enumerate(rep_all_attacks):
        if dt_types[r[0]] != 'n' and dt_types[r[1]] != 'n' and r[4] == 'Self Promote':
            rep_attacks.append(r)
        elif dt_types[r[0]] == 'n' and (dt_types[r[1]] == 'n') and r[4] == 'Bad Mouthing':
            rep_attacks.append(r)
        elif dt_types[r[0]] != 'n' and (dt_types[r[1]] == 'n') and r[4] == 'Bad Mouthing':
            rep_attacks.append(r)

    # rep_all_attacks
        # print(rep_attacks)

    data = [
        {"DT": "DT "+str(r[0]), "Attacked_DT": "DT "+str(r[1]), "Analysis": str(r[2]), "Category":str(r[3]), "Attack": str(r[4])}
    for r in rep_attacks]
    res = {
        "rep_data": data,
        "status": "Ok"
    }
    return res
    
@app.route("/repattack")
def deployRepAttack():
    attack_type = request.args.get('type')
    dt_subs = analyticsSupportService.getDTSubs()
    getDTTypes = analyticsSupportService.getDTTypePrediction()
    dts = analyticsSupportService.getDTDetails()

    dt_types = ['','','','','','']

    for t in getDTTypes:
        dt_types[t[0]] = t[1]

    sp_attacks = []
    bm_attacks = []

    for s in dt_subs:
        if dt_types[s[0]] != 'n' and dt_types[s[1]] != 'n':
            sp_attacks.append(s)
        elif dt_types[s[0]] != 'n' and dt_types[s[1]] == 'n':
            bm_attacks.append(s)

    # print(sp_attacks)
    # print(bm_attacks)
    # attack_DT = request.args.get('attdt')   #DT id to attack on a selfpromote same DT ID
    # strength = request.args.get('strength') #up one impact level or maximum 1=mid 2=high
    # attack = request.args.get('attack') #bm = bad mouthing sp= self promoting
    # type_of_attack = request.args.get('type')   #i=individual g=group
    # initiator_dt_id = request.args.get('init_dt')

    if attack_type == "sp" and len(sp_attacks) > 0:
        a = random.choice(sp_attacks)
        for d in dts:
            if d[0] == a[0]:
                # print(str(d[5])+"/repattack?attdt="+str(a[1])+"&strength=2&attack=sp&type=i&init_dt"+str(a[0]))
                response = requests.get(url= str(d[5])+"/repattack?attdt="+str(a[1])+"&strength=2&attack=sp&type=i&init_dt="+str(a[0]))
                response_data = response.json()
                msg = "DT "+str(a[0])+ " attacking DT "+str(a[1])+" Self Promote"
    elif attack_type == "bm" and len(bm_attacks) > 0:
        a = random.choice(bm_attacks)
        for d in dts:
            if d[0] == a[0]:
                response = requests.get(url= str(d[5])+"/repattack?attdt="+str(a[1])+"&strength=2&attack=bm&type=i&init_dt="+str(a[0]))
                response_data = response.json()
                msg = "DT "+str(a[0])+ " attacking DT "+str(a[1])+" Bad Mouthing"
    else:
        msg = "No possible attack scenario for "+attack_type
    
    ret = {
        "msg": msg,
        "status": "ok"
    }

    return ret




@app.route("/getInfo")
def testService():
    # count = request.args.get('count')
    # runQoSTest(thread_id=1,test_count=0,concurrent_users=1,loop_times=1)
    # runQoSTest(thread_id=2,test_count=0,concurrent_users=1,loop_times=1)
    # re = dttsaSupportServices.qosSpecificTestExecutionStatus("i")
    # repAttackCheck()
    dts = analyticsSupportService.getDTDetails()
    print(len(dts))
    dt_count = len(dts)
    analysis_count = len(analyticsSupportService.getAnalysisCyclesCount())
    # rep_attacks_count = len(analyticsSupportService.getRepAttackCount())
    avg_trust_score = analyticsSupportService.getAvgTrustScore()

    getDTTypes = analyticsSupportService.getDTTypePrediction()

    dt_types = ['','','','','','']

    for t in getDTTypes:
        dt_types[t[0]] = t[1]

    print(dt_types)

    rep_attacks_count = 0
    rep_attacks = analyticsSupportService.getUniqueRepAttacks()

    for r in rep_attacks:
        if dt_types[r[0]] != 'n' and dt_types[r[1]] != 'n' and r[2] == 'Self Promote':
            rep_attacks_count = rep_attacks_count + 1
        elif dt_types[r[0]] == 'n' and (dt_types[r[1]] == 'n') and r[2] == 'Bad Mouthing':
            rep_attacks_count = rep_attacks_count + 1
        elif dt_types[r[0]] != 'n' and (dt_types[r[1]] == 'n') and r[2] == 'Bad Mouthing':
            rep_attacks_count = rep_attacks_count + 1


    val = {
        "series": [
            {
                "name": 'Trust Score',
                "data": [random.randint(0,100), random.randint(0,100), random.randint(0,100), random.randint(0,100), random.randint(0,100), random.randint(0,100), 65,100]
            }
        ],
        "labels": ['1', '2', '3', '4', '5', '6', '7','8'],
        "cards": [
  {
    "icon": '<img src="https://www.shutterstock.com/image-vector/explore-concept-digital-twins-this-600nw-2366323277.jpg" alt="Trulli" width="500" height="333">',
    "title": 'Number of DTs',
    "total": dt_count,
  },
  {
    "icon": '<img src="https://static.vecteezy.com/system/resources/previews/026/306/689/original/chart-analysis-icon-statistics-business-finance-research-growth-sales-magnify-glass-sign-symbol-black-artwork-graphic-illustration-clipart-eps-vector.jpg" alt="Trulli" width="500" height="333">',
    "title": 'Analysis Cycles',
    "total": analysis_count,
  },
  {
    "icon": '<img src="https://p7.hiclipart.com/preview/428/736/877/security-hacker-cyberattack-computer-icons-computer-security-cybercrime-cyber-crime.jpg" alt="Trulli" width="500" height="333">',
    "title": 'Rep: Attacks',
    "total": rep_attacks_count,
  },
  {
    "icon": '<img src="https://media.istockphoto.com/id/1426831333/vector/handshake-line-icon-deal-partner-business-symbol-editable-stroke-design-template-vector.jpg?s=1024x1024&w=is&k=20&c=Vb66JT7X5Tf-Kwzo_9v_cfFRTT3q_e9Gmf5to4rH9DQ=" alt="Trulli" width="500" height="333">',
    "title": 'Avg: Trust Score',
    "total": avg_trust_score[0][0],
  }
]
    }
    return val


@app.route("/getdtnetwork")
def getDTNetwork():
    icon_list = ["&#xf049","&#xe04b"]
    dt_list = analyticsSupportService.getDTTypes()
    print(len(dt_list))
    if len(dt_list) > 0:
        nodes = [
            {"name": "DT "+str(dt[0]), "size": 40, "color": "green" if dt[1] == "n" else "yellow" if dt[1] == "c" else "red" if dt[1] == "m" else "gray" , "label": "true", "icon": random.choice (icon_list)}
        for dt in dt_list]
    else:
        dt_details = analyticsSupportService.getDTDetails()
        nodes = [
            {"name": "DT "+str(dt[0]), "size": 40, "color": "gray" , "label": "true", "icon": random.choice (icon_list)}
        for dt in dt_details]

    
    # service_nodes = {"name": "Connector", "size": 40, "color": "gray" , "label": "true", "icon": random.choice (icon_list) }

    nodes_dict = {}
    
    for n in nodes:
        key = n["name"].split(" ")[1]
        nodes_dict[key] = n

    node_count = len(nodes_dict)
    # print(len(nodes_dict))
    k = len(nodes_dict)+1
    nodes_dict["Connector"] = {"name": "Connector", "size": 40, "color": "blue" , "label": "true", "icon": "&#xe9f4" }
    k = k+1
    nodes_dict["Trust Analyser"] = {"name": "Trust Analyser", "size": 40, "color": "blue" , "label": "true", "icon": "&#xe4fc" }
    k = k+1
    nodes_dict["Reputation Model"] = {"name": "Reputation Model", "size": 40, "color": "blue" , "label": "true", "icon": "&#xe8dc" }
    k = k+1
    nodes_dict["Blockchain"] = {"name": "Blockchain", "size": 40, "color": "blue" , "label": "true", "icon": "&#xe9b0" }
    print(nodes_dict)
    dt_subs = analyticsSupportService.getDTSubs()
    edges = [
        { "source": e[0], "target": e[1], "width": 2, "color": "black" }
    for e in dt_subs]

    edges_dict = {}
    for i,e in enumerate(edges):
        key = "edge"+str(i)
        edges_dict[key] = e 

    print(len(edges_dict) )
    for i in range(1,node_count+1):
        print(i)
        l = len(edges_dict) + 1
        print(l)
        edges_dict["edge"+str(l)] = { "source":i, "target":  "Connector", "width": 2, "color": "blue" }


    l = len(edges_dict) + 1
    edges_dict["edge"+str(l)] = { "source":"Connector", "target":  "Trust Analyser", "width": 2, "color": "blue" }
    l = l + 1
    edges_dict["edge"+str(l)] = { "source":"Connector", "target":  "Reputation Model", "width": 2, "color": "blue" }
    l = l + 1
    edges_dict["edge"+str(l)] = { "source":"Connector", "target":  "Blockchain", "width": 2, "color": "blue" }

    # print(nodes2)
    # nodes = {
    # 1: { "name": "DT 1", "size": 40, "color": "gray", "label": "true", "icon": "&#xf049" },
    # 2: { "name": "DT 2", "size": 40, "color": "green", "label": "true", "icon": "&#xe04b"},
    # 3: { "name": "DT 3", "size": 40, "color": "orange", "label": "true", "icon": "&#xf049" },
    # 4: { "name": "DT 4", "size": 40, "color": "green", "label": "true", "icon": "&#xe04b" },
    # 5: { "name": "DT 5", "size": 40, "color": "red", "label": "true", "icon": "&#xf049" },
    # }
    # edges = {
    # "edge1": { "source": "1", "target": "2", "width": 2, "color": "black" },
    # "edge2": { "source": "2", "target": "3", "width": 2, "color": "black" },
    # "edge3": { "source": "3", "target": "4", "width": 2, "color": "black" },
    # "edge4": { "source": "4", "target": "1", "width": 2, "color": "black" },
    # "edge5": { "source": "5", "target": "2", "width": 2, "color": "black" },
    # "edge6": { "source": "3", "target": "1", "width": 2, "color": "black" },
    # "edge7": { "source": "4", "target": "5", "width": 2, "color": "black" },
    # }
    # layout = {
    #     "nodes": {
    #         1: { "x": 0, "y": 0 },
    #         2: { "x": 80, "y": 80 },
    #         3: { "x": 160, "y": 0 },
    #         4: { "x": 240, "y": 80 },
    #         5: { "x": 320, "y": 0 },
    #     },
    # }

    # layout = {
    #     "nodes": {
    #         "8": { "x": 0, "y": 0 },
    #         # "2": { "x": 80, "y": 80 },
    #         # "3": { "x": 160, "y": 0 },
    #         # "4": { "x": 240, "y": 80 },
    #         # "5": { "x": 320, "y": 0 },
    #         # "6": { "x": 0, "y": 0 },
    #         # "7": { "x": 80, "y": 80 },
    #         # "8": { "x": 160, "y": 0 },
    #         # "9": { "x": 240, "y": 80 },
    #         # "10": { "x": 320, "y": 0 },
    #         # "11": { "x": 320, "y": 0 }
    #     },
    # }

    res = {
        "nodes" : nodes_dict,
        "edges" : edges_dict,
        # "layout": layout
    }

    return res

@app.route("/gettrustscores")
def getTrustScores():
    dt_id = request.args.get('dtid')
    print(dt_id)
    ret_value = analyticsSupportService.getDTTrustScores(dt_id)
    # print(ret_value)
    trust_scores = []
    iteration_ids = []
    for t in ret_value:
        trust_scores.append(round(t[6], 2))
        iteration_ids.append(t[1])

    print(iteration_ids)
    val = {
        "series": [
            {
                "name": 'Trust Score',
                "data": trust_scores
            }
        ],
        "labels": iteration_ids
    }
    return val

@app.route("/gettrustscoreseffects")
def getTrustScoresTrustEffects():
    dt_id = request.args.get('dtid')
    res_t_effects = analyticsSupportService.getDTTrustEffect(dt_id)
    res_t_scores = analyticsSupportService.getDTTrustScores(dt_id)
    trust_scores = []
    trust_effects = []
    iteration_ids = []
    for t in res_t_scores:
        trust_scores.append(round(t[6], 2))
        iteration_ids.append(t[1])

    for t in res_t_effects:
        trust_effects.append(round(t[2], 2))
    chartData = {
        "series": [
            {
            "name": 'Trust Score (%)',
            "data": trust_scores
            },

            {
            "name": 'Trust Effect',
            "data": trust_effects
            }
        ],
        "labels": iteration_ids
        }
    return chartData

@app.route("/typescount")
def DTTypeCount():
    dt_id = request.args.get('dtid')
    ret_type_counts = analyticsSupportService.getDTTypeCounts(dt_id)
    type_count = [0,0,0,0]
    for i in ret_type_counts:
        if i[0] == "n":
            type_count[0] = i[1]
        elif i[0] == "c":
            type_count[1] = i[1]
        elif i[0] == "m":
            type_count[2] = i[1]
        else:
            type_count[3] = 1

    chartData = {
        "series": type_count,
        "labels": ['Normal', 'Unpredictable', 'Malicious', 'Unknown']
    }
    return chartData

@app.route('/setconfigs')
def setConfigs():
    if 'firefly' in request.args:
        config['servers']['firefly_service_url'] = request.args.get('firefly')
    ### TODO after setting db try to connect to the correct DB
    if 'db' in request.args:
        config['database']['db_ip'] = request.args.get('db')
    with open ('environment_config.ini','w') as configfile:
        config.write(configfile)
    config.read('environment_config.ini')
    app.config.update(
        firefly_url = config['servers']['firefly_service_url']
    )
    # app.config['firefly_url']
    return str(config['servers']['firefly_service_url'])


@app.route('/updatepolicy')
def updateGovPolicy():
    rule = request.args.get('rule')
    json_file_path = 'sample_policy.json'

    with open(json_file_path,'r') as file:
        json_data = json.load(file)

    for policy in json_data['policies']:
        if policy['name'] == 'Change Connections':
            policy['value'] = rule

    payload = {
    "header":{},
    "data": [
        {
            "datatype":{
                "name": "policy",
                "version": "1.1"
            },
            "value": json_data
        }
    ]
    }
    response = requests.post("http://34.29.10.14:5000/api/v1/messages/broadcast", json=payload)

    # Print the response
    # print(response.status_code)
    print(response.json()['data'][0]['id'])
    app.config.update(
        policy_id = response.json()['data'][0]['id']
    )
    return "ok"

@app.route('/getgovpolicy')
def getGovernancePolicy():
    response = requests.get(url= str(app.config['firefly_url'])+"/api/v1/data/"+app.config['policy_id']+"/value")
    print(str(app.config['firefly_url'])+"/api/v1/data/"+app.config['policy_id']+"/value")
    # print(response.text)
    response_data = response.json()
    # print(response_data['value'])
    return response_data

def truncate_to_microseconds(timestamp):
    # Split the timestamp into the main part and the fractional second part
    main_part, frac_part = timestamp.split('.')
    # Truncate the fractional second part to 6 digits (microseconds)
    truncated_frac_part = frac_part[:6]
    # Reconstruct the timestamp
    truncated_timestamp = f"{main_part}.{truncated_frac_part}Z"
    return truncated_timestamp


def calculateTnxTime(t1, t2):
    # Truncate the timestamps
    truncated_timestamp1 = truncate_to_microseconds(t1)
    truncated_timestamp2 = truncate_to_microseconds(t2)

    # Convert timestamps to datetime objects
    time_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    datetime1 = datetime.strptime(truncated_timestamp1, time_format)
    datetime2 = datetime.strptime(truncated_timestamp2, time_format)

    # Calculate the difference
    time_difference = datetime2 - datetime1

    # Get the difference in microseconds and convert to milliseconds
    difference_in_microseconds = time_difference.total_seconds() * 1e6
    difference_in_milliseconds = difference_in_microseconds / 1000

    # Print the difference
    print(f"Difference in milliseconds: {difference_in_milliseconds} ms")
    return round(difference_in_microseconds/1000, 2)

@app.route('/bctnxtimes')
def blockchainTnxTimes():
    response = requests.get(url=str(app.config['firefly_url'])+'/api/v1/transactions?limit=1000')
    response_data = response.json()
    # res_tnx =  requests.get(url=str(app.config['firefly_url'])+"/api/v1/transactions/"+str(response_data[0]['id'])+"/operations")
    # res_tnx_data = res_tnx.json()
    # t1 = res_tnx_data[0]['created']
    # t2 = res_tnx_data[0]['updated']

    avg_tnx = analyticsSupportService.getAvgTnxTime()
    temp = 0.0
    if type(avg_tnx[0][0]) == type(temp):
        # print("b")
        tnx_time_str = str(round(avg_tnx[0][0], 2)) + " ms"
        
    else:
        tnx_time_str = "NA"
        print(type(avg_tnx[0][0]))
        print(type(float))
        print(avg_tnx)

    # for r in response_data:
    #     print(r['id'])
    ret_value = {
        "cards": [
  {
    "icon": '<img src="https://www.shutterstock.com/image-vector/explore-concept-digital-twins-this-600nw-2366323277.jpg" alt="Trulli" width="500" height="333">',
    "title": '# of Blockchain Transactions',
    "total": len(response_data),
  },{
    "icon": '<img src="https://www.shutterstock.com/image-vector/explore-concept-digital-twins-this-600nw-2366323277.jpg" alt="Trulli" width="500" height="333">',
    "title": 'Avg Conformation Time',
    "total": tnx_time_str,
  }]
    }
    return ret_value

@app.route('/changecondata')
def getChangeConData():
    ret_value = analyticsSupportService.getChangeCons()
    data = [
        {"DT_ID": "DT "+str(r[0]), "Change_DT_ID": "DT "+str(r[1]), "Status": str(r[2])}
    for r in ret_value]
    res = {
        "change_con_data": data,
        "status": "Ok"
    }
    return res

@app.route('/changecons')
def getChangeConTbl():
    dts = analyticsSupportService.getDTDetails()
    for dt in dts:
        # print(dt[5])
        response = requests.get(url=str(dt[5])+'/changecon')
        response_data = response.json()

    ret_value = analyticsSupportService.getChangeCons()
    data = [
        {"DT_ID": "DT "+str(r[0]), "Change_DT_ID": "DT "+str(r[1]), "Status": str(r[2])}
    for r in ret_value]
    res = {
        "change_con_data": data,
        "status": "Ok"
    }
    return res

@app.route('/getrepdata')
def getReputationData():
    dts = analyticsSupportService.getDTDetails()
    rep_data = []
    # data = [
    #     {"DT_ID": "DT "+str(r[0]), "Change_DT_ID": "DT "+str(r[1]), "Status": str(r[2])}
    # for r in range(1,len(dts)+1)]
    for i in range(1,len(dts)+1):
        dt_data = analyticsSupportService.getReputationDetails(i)
        total_count = 0
        pos = 0
        neg = 0
        undecide = 0
        for d in dt_data:
            if d[1] == 'positive':
                pos = pos + int(d[2])
            elif d[1] == 'positive':
                neg = neg + int(d[2])
            else:
                undecide = undecide + int(d[2])
        total_count = pos + neg + undecide
        rep_data.append({"id": i, "pos": str(round((pos/total_count)*100,2)),"neg": str(round((neg/total_count)*100,2)),"undecided": str(round((undecide/total_count)*100,2))})
            
        # print(dt_data)
    res = {
        "rep_data": rep_data,
        "status": "Ok"
    }
    return res
    
@app.route('/getDTtrustdata')
def getDTTrustData():
    dt_id = request.args.get('dtid')
    trust_data = analyticsSupportService.getDTTrustCalculation(dt_id)
    data = [
        {"DT_ID": "DT "+str(r[0]), "category": str(r[1]), "type": str(r[2]), "count": str(r[3])}
    for r in trust_data]
    res ={
        "trust_data": data,
        "status": "ok"
    }
    return res

@app.route('/getDTURLs')
def getDTURLs():
    dts = analyticsSupportService.getDTDetails()
    data = [
        {"DT_ID": "DT "+str(d[0]), "url": str(d[5])+"/changecon"}
    for d in dts]
    res = {
        "urls": data,
        "status": "ok"
    }
    return res

def start_server(args):
    app.run(host='0.0.0.0',port=9001,use_reloader=False)

def main(args):
    start_server(args)

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    #parser.add_argument('-a')
    #args = parser.parse_args()
    args = ""
    main(args)
        
