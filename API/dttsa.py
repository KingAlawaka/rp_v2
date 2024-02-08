#DTTSA dashboard and main services management
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
from API_analysis import APIAnalyzer
from dbconnection import DBConnection
from dttsa_support import DTTSASupportServices
import configparser
from qos_analysis import QoSAnalyzer
from resilient_analysis import ResilienceAnalyzer
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


app = Flask(__name__,template_folder="../Dashboardnew/templates", static_folder="../Dashboardnew/static")
CORS(app)

scheduler = APScheduler()
scheduler.init_app(app)


config = configparser.ConfigParser()
config.read('environment_config.ini')
API_vulnerbility_service_URL = config['servers']['API_VULNERBILITY_SERVICE_URL']


dbCon = DBConnection()
apiAnalyzer = APIAnalyzer()
dttsaSupportServices = DTTSASupportServices()
qosAnalyzer = QoSAnalyzer()
resilienceAnalyzer = ResilienceAnalyzer()

app.config['api_job'] = "False"
app.config['qos_job'] = "False"
app.config['dependency_creation'] = "False"
app.config['trend_analysis_job'] = "False"
app.config['iteration_count'] = 0 #update inside the trustScoreCalculation()
app.config['analysis_started'] = False
app.config['API_analysis_counter'] = 0

app.config['qos_analysis_started'] = False
app.config['qos_init_test_started'] = False
app.config['qos_pn_test_started'] = False
app.config['qos_pc_test_started'] = False
app.config['qos_pm_test_started'] = False
app.config['qos_analysis_ongoing'] = False
app.config['qos_number_of_tests'] = 5
app.config['qos_loop_times'] = 1
app.config['rep_attack_analysis_started'] = False

app.config['dependecy_graph_image_counter'] = 0

'''
Check API vulnerbility finished results for submitted DTs
'''
def runSchedulerJobs():
    print("SchedularJobs Initiated")
    scheduler.add_job(id="checkAPIResults", replace_existing=True, func=checkAPIResults,trigger="interval",seconds = 30)
    scheduler.add_job(id="qosAnalysisLogic", replace_existing=True, func=qosAnalysisLogic,trigger="interval",seconds = 30)
    scheduler.add_job(id="repAttackAnalysis", replace_existing=True, func=repAttackAnalysis,trigger="interval",seconds = 30)
    scheduler.start()

def repAttackAnalysis():
    if (int(app.config['iteration_count']) != 0 and app.config['rep_attack_analysis_started'] ):
        print("Rep attack analysis started")
    else:
        print("Waiting for finish analysis")

def impactMajorityDetector(impacts,type_index,add_val_index):
    impact_counter = [0,0,0] #n c m
    for i in impacts:
        if i[type_index] == 'n':
            if add_val_index != 1:
                impact_counter[0] = impact_counter[0] + i[add_val_index]
            else:
                impact_counter[0] = impact_counter[0] + 1

        if i[type_index] == 'c':
            if add_val_index != 1:
                impact_counter[1] = impact_counter[1] + i[add_val_index]
            else:
                impact_counter[1] = impact_counter[1] + 1

        if i[type_index] == 'm':
            if add_val_index != 1:
                impact_counter[2] = impact_counter[2] + i[add_val_index]
            else:
                impact_counter[2] = impact_counter[2] + 1
    
    max_value = max(impact_counter)
    multiple_majorities_counter = 0
    for i in impact_counter:
        if i == max_value:
            multiple_majorities_counter += 1

    multiple_majority = False
    majority_impact = ""
    if multiple_majorities_counter != 1:
        multiple_majority = True
        if impact_counter[0] == max_value and impact_counter[1] == max_value:
            majority_impact = "c"
        else:
            majority_impact = "m"
    else:
        if impact_counter[0] == max_value:
            majority_impact = "n"
        elif impact_counter[1] == max_value:
            majority_impact = "c"
        else:
            majority_impact = "m"



    return multiple_majority,majority_impact

def repAttackCheck():
    # app.config.update(
    #     iteration_count = 1
    # )
    dts = dttsaSupportServices.getDTIDs()
    # print(dts)
    for dt in dts:
        subs = dttsaSupportServices.getDTSubByCategory(dt[0],'POST')
        category_impacts = []
        print(dt[0])
        dttsaSupportServices.addDebugMsg(dt[0])
        qos_impact_predictions = dttsaSupportServices.getDTValuesImpactPredictionsByCategory(dt[0],(int(app.config['iteration_count'])*-1),'QoS')
        print(qos_impact_predictions)
        values_impact_predictions = dttsaSupportServices.getDTValuesImpactPredictionsByCategory(dt[0],(int(app.config['iteration_count'])*-1),'Values')
        dttsaSupportServices.addDebugMsg("QoS impact predictions: "+str(qos_impact_predictions))
        dttsaSupportServices.addDebugMsg("Values impact predictions: "+str(values_impact_predictions))

        qos_multiple_majority,qos_majority_type = impactMajorityDetector(qos_impact_predictions,2,3)
        if len(qos_impact_predictions) > 0:
            category_impacts.append([qos_majority_type])
        values_multiple_majority,values_majority_type = impactMajorityDetector(values_impact_predictions,2,3)
        if len(values_impact_predictions) > 0:
            category_impacts.append([values_majority_type])
        
        dttsaSupportServices.addDebugMsg("QoS multi majority "+str(qos_multiple_majority)+" majority type "+str(qos_majority_type))
        dttsaSupportServices.addDebugMsg("values multi majority "+str(values_multiple_majority)+" majority type "+str(values_majority_type))

        dttsa_qos_classification = dttsaSupportServices.getDTTrustCalculationsByCategory(dt[0],'DTTSA QoS',(int(app.config['iteration_count'])*-1))
        print(dttsa_qos_classification)
        dttsaSupportServices.addDebugMsg("DTTSA QoS " + str(dttsa_qos_classification))
        dttsa_qos_multiple_majority,dttsa_qos_majority_type = impactMajorityDetector(dttsa_qos_classification,7,1)
        if len(dttsa_qos_classification) > 0:
            category_impacts.append([dttsa_qos_majority_type])
        dttsaSupportServices.addDebugMsg("DTTSA QoS multi majority "+str(dttsa_qos_multiple_majority)+" majority type "+str(dttsa_qos_majority_type))

        dt_type_prediction_history = dttsaSupportServices.getDTtypePredictionHistory(dt[0])
        dttsaSupportServices.addDebugMsg("DT history " + str(dt_type_prediction_history))
        dt_type_history_prediction_multiple_majority, dt_type_history_prediction_type = impactMajorityDetector(dt_type_prediction_history,2,3)
        if len(dt_type_prediction_history) > 0:
            category_impacts.append([dt_type_history_prediction_type])
        dttsaSupportServices.addDebugMsg("DT type prediction history multi majority "+str(dt_type_history_prediction_multiple_majority)+" majority type "+str(dt_type_history_prediction_type))


        dttsaSupportServices.addDebugMsg("Overall " + str(category_impacts))
        overall_category_multiple_majority,overall_category_type = impactMajorityDetector(category_impacts,0,1)
        # if qos_majority_type == values_majority_type == dttsa_qos_majority_type == dt_type_history_prediction_type:
        # if overall_category_multiple_majority == False:
        dttsaSupportServices.addDebugMsg("Overall multi majority"+ str(overall_category_multiple_majority) +" overall majority " +str(overall_category_type))

        majority_impact_prediction = ""
        considerd_DTs = []
        dt_qos_attack = False
        dt_value_attack = False
        dttsa_qos_attack = False

        dt_report_dt_id = 0
        dt_attacked_dt_id = 0
        dttsa_report_dt_id = 0
        dttsa_attacked_dt_id = 0

        dt_attack_name = ""
        dttsa_attack_name = ""
        #Logic 1 all participating categories have same type
        if overall_category_multiple_majority == False and category_impacts.count([overall_category_type]) == len(category_impacts):
            dttsaSupportServices.addDebugMsg("Overall agree")
            majority_impact_prediction = overall_category_type
            
            #QoS
            for ip in qos_impact_predictions:
                dttsaSupportServices.addDebugMsg(" logic 1 qos ip[2] values "+ str(ip[2]))
                dttsaSupportServices.addDebugMsg(" considered DTs  "+ str(considerd_DTs))
                if ip[2] != majority_impact_prediction and ip[0] not in considerd_DTs:
                    attack_name = ""
                    if majority_impact_prediction == "n":
                        if ip[2] == "c" or ip[2] == "m":
                            attack_name = "Bad Mouthing"
                            dt_qos_attack = True
                            dt_report_dt_id = ip[0]
                            dt_attacked_dt_id = ip[1]
                    elif majority_impact_prediction == "c" or  majority_impact_prediction == "m":
                        if ip[2] == "c" or ip[2] == "n":
                            attack_name = "Self Promote"
                            dt_qos_attack = True
                            dt_report_dt_id = ip[0]
                            dt_attacked_dt_id = ip[1]
                    else:
                        attack_name = "majority "+ majority_impact_prediction + " reported "+ip[2]
                    dt_attack_name = attack_name
                    print("DT ", ip[0]," reporting DT ", ip[1], " incorrectly in QoS (DT) "+attack_name)
                    detection_msg = "DT " + str(ip[0]) + " reporting DT " + str(ip[1])+" incorrectly (DT)"+attack_name +" all agree "
                    submitted_dt_type_history_multi_values,submitted_dt_type_history = impactMajorityDetector(dttsaSupportServices.getDTtypePredictionHistory(dt[0]),2,3)
                    if submitted_dt_type_history_multi_values== False and (submitted_dt_type_history != "c" or submitted_dt_type_history !="m") and (dt_type_history_prediction_type != "c" or dt_type_history_prediction_type != "m") :
                        dttsaSupportServices.addDebugMsg(detection_msg)
                        dttsaSupportServices.addVulnerableRepAttackPossibleDTs(ip[0],ip[1], detection_msg,"QoS","logic 1",attack_name,"group","RA",100,"member")
                    considerd_DTs.append(ip[0])
                else:
                    considerd_DTs.append(ip[0])

            #Values
            for ip in values_impact_predictions:
                dttsaSupportServices.addDebugMsg(" logic 1 values ip[2] values "+ str(ip[2]))
                dttsaSupportServices.addDebugMsg(" considered DTs  "+ str(considerd_DTs))
                if ip[2] != majority_impact_prediction and ip[0] not in considerd_DTs:
                    attack_name = ""
                    if majority_impact_prediction == "n":
                        if ip[2] == "c" or ip[2] == "m":
                            attack_name = "Bad Mouthing"
                            dt_value_attack = True
                            dt_report_dt_id = ip[0]
                            dt_attacked_dt_id = ip[1]
                    elif majority_impact_prediction == "c" or  majority_impact_prediction == "m":
                        if ip[2] == "c" or ip[2] == "n":
                            attack_name = "Self Promote"
                            dt_value_attack = True
                            dt_report_dt_id = ip[0]
                            dt_attacked_dt_id = ip[1]
                    else:
                        attack_name = "majority "+ majority_impact_prediction + " reported "+ip[2]
                    dt_attack_name = attack_name
                    print("DT ", ip[0]," reporting DT ", ip[1], " incorrectly (DT) "+attack_name)
                    detection_msg = "DT " + str(ip[0]) + " reporting DT " + str(ip[1])+" incorrectly in Values (DT)"+attack_name +" all agree "
                    submitted_dt_type_history_multi_values,submitted_dt_type_history = impactMajorityDetector(dttsaSupportServices.getDTtypePredictionHistory(dt[0]),2,3)
                    if submitted_dt_type_history_multi_values== False and (submitted_dt_type_history != "c" or submitted_dt_type_history !="m") and (dt_type_history_prediction_type != "c" or dt_type_history_prediction_type != "m") :
                        dttsaSupportServices.addDebugMsg(detection_msg)
                        dttsaSupportServices.addVulnerableRepAttackPossibleDTs(ip[0],ip[1], detection_msg,"Values","logic 1",attack_name,"group","RA",100,"member")
                    considerd_DTs.append(ip[0])
                else:
                    considerd_DTs.append(ip[0])
            
        else:
            dttsaSupportServices.addDebugMsg("Overall disagree")
            # if overall_category_multiple_majority == False: dttsa_qos_multiple_majority,dttsa_qos_majority_type
            if dttsa_qos_multiple_majority == False and dt_type_history_prediction_multiple_majority == False:
                if dttsa_qos_majority_type == dt_type_history_prediction_type:
                    majority_impact_prediction = dttsa_qos_majority_type
            
                    #QoS
                    for ip in qos_impact_predictions:
                        dttsaSupportServices.addDebugMsg(" logic 2 qos ip[2] values "+ str(ip[2]))
                        dttsaSupportServices.addDebugMsg(" considered DTs  "+ str(considerd_DTs))
                        if ip[2] != majority_impact_prediction and ip[0] not in considerd_DTs:
                            attack_name = ""
                            if majority_impact_prediction == "n":
                                if ip[2] == "c" or ip[2] == "m":
                                    attack_name = "Bad Mouthing"
                                    dt_qos_attack = True
                                    dt_report_dt_id = ip[0]
                                    dt_attacked_dt_id = ip[1]
                            elif majority_impact_prediction == "c" or  majority_impact_prediction == "m":
                                if ip[2] == "c" or ip[2] == "n":
                                    attack_name = "Self Promote"
                                    dt_qos_attack = True
                                    dt_report_dt_id = ip[0]
                                    dt_attacked_dt_id = ip[1]
                            else:
                                attack_name = "majority "+ majority_impact_prediction + " reported "+ip[2]
                            dt_attack_name = attack_name
                            print("DT ", ip[0]," reporting DT ", ip[1], " incorrectly in QoS (DT) "+attack_name)
                            detection_msg = "DT " + str(ip[0]) + " reporting DT " + str(ip[1])+" incorrectly (DT)"+attack_name +" Overall disagree DTTSA and History"
                            submitted_dt_type_history_multi_values,submitted_dt_type_history = impactMajorityDetector(dttsaSupportServices.getDTtypePredictionHistory(dt[0]),2,3)
                            if dt_type_history_prediction_type == "n":
                                dttsaSupportServices.addDebugMsg(detection_msg)
                                dttsaSupportServices.addVulnerableRepAttackPossibleDTs(ip[0],ip[1], detection_msg,"QoS","logic 2",attack_name,"group","RA",100,"member")
                            elif submitted_dt_type_history_multi_values== False and (submitted_dt_type_history != "c" or submitted_dt_type_history !="m") and (dt_type_history_prediction_type != "c" or dt_type_history_prediction_type != "m") :
                                dttsaSupportServices.addDebugMsg(detection_msg)
                                dttsaSupportServices.addVulnerableRepAttackPossibleDTs(ip[0],ip[1], detection_msg,"QoS","logic 2",attack_name,"group","RA",100,"member")
                            considerd_DTs.append(ip[0])
                        else:
                            considerd_DTs.append(ip[0])

                    #Values
                    for ip in values_impact_predictions:
                        dttsaSupportServices.addDebugMsg(" logic 2 ip[2] values "+ str(ip[2]))
                        dttsaSupportServices.addDebugMsg(" considered DTs  "+ str(considerd_DTs))
                        if ip[2] != majority_impact_prediction and ip[0] not in considerd_DTs:
                            attack_name = ""
                            if majority_impact_prediction == "n":
                                if ip[2] == "c" or ip[2] == "m":
                                    attack_name = "Bad Mouthing"
                                    dt_qos_attack = True
                                    dt_report_dt_id = ip[0]
                                    dt_attacked_dt_id = ip[1]
                            elif majority_impact_prediction == "c" or  majority_impact_prediction == "m":
                                if ip[2] == "c" or ip[2] == "n":
                                    attack_name = "Self Promote"
                                    dt_qos_attack = True
                                    dt_report_dt_id = ip[0]
                                    dt_attacked_dt_id = ip[1]
                            else:
                                attack_name = "majority "+ majority_impact_prediction + " reported "+ip[2]
                            dt_attack_name = attack_name
                            print("DT ", ip[0]," reporting DT ", ip[1], " incorrectly (DT) "+attack_name)
                            detection_msg = "DT " + str(ip[0]) + " reporting DT " + str(ip[1])+" incorrectly in Values (DT)"+attack_name +" Overall disagree DTTSA and History"
                            submitted_dt_type_history_multi_values,submitted_dt_type_history = impactMajorityDetector(dttsaSupportServices.getDTtypePredictionHistory(dt[0]),2,3)
                            if dt_type_history_prediction_type == "n":
                                dttsaSupportServices.addDebugMsg(detection_msg)
                                dttsaSupportServices.addVulnerableRepAttackPossibleDTs(ip[0],ip[1], detection_msg,"Values","logic 2",attack_name,"group","RA",100,"member")
                            elif submitted_dt_type_history_multi_values== False and (submitted_dt_type_history != "c" or submitted_dt_type_history !="m") and (dt_type_history_prediction_type != "c" or dt_type_history_prediction_type != "m") :
                                dttsaSupportServices.addDebugMsg(detection_msg)
                                dttsaSupportServices.addVulnerableRepAttackPossibleDTs(ip[0],ip[1], detection_msg,"Values","logic 2",attack_name,"group","RA",100,"member")
                            considerd_DTs.append(ip[0])
                        else:
                            considerd_DTs.append(ip[0])
                else:
                    #if statement logic
                    #dttsa_qos_multiple_majority == False and len(dt_type_prediction_history) > 3 and dt_type_history_prediction_multiple_majority == False
                    if dttsa_qos_multiple_majority == False:
                        majority_impact_prediction = dttsa_qos_majority_type
                
                        #QoS
                        for ip in qos_impact_predictions:
                            dttsaSupportServices.addDebugMsg(" logic 3 qos ip[2] values "+ str(ip[2]))
                            dttsaSupportServices.addDebugMsg(" considered DTs  "+ str(considerd_DTs))
                            if ip[2] != majority_impact_prediction and ip[0] not in considerd_DTs:
                                attack_name = ""
                                if majority_impact_prediction == "n":
                                    if ip[2] == "c" or ip[2] == "m":
                                        attack_name = "Bad Mouthing"
                                        dt_qos_attack = True
                                        dt_report_dt_id = ip[0]
                                        dt_attacked_dt_id = ip[1]
                                elif majority_impact_prediction == "c" or  majority_impact_prediction == "m":
                                    if ip[2] == "c" or ip[2] == "n":
                                        attack_name = "Self Promote"
                                        dt_qos_attack = True
                                        dt_report_dt_id = ip[0]
                                        dt_attacked_dt_id = ip[1]
                                else:
                                    attack_name = "majority "+ majority_impact_prediction + " reported "+ip[2]
                                dt_attack_name = attack_name
                                print("DT ", ip[0]," reporting DT ", ip[1], " incorrectly in QoS (DT) "+attack_name)
                                detection_msg = "DT " + str(ip[0]) + " reporting DT " + str(ip[1])+" incorrectly (DT)"+attack_name +" Overall disagree using only DTTSA to determine"
                                submitted_dt_type_history_multi_values,submitted_dt_type_history = impactMajorityDetector(dttsaSupportServices.getDTtypePredictionHistory(dt[0]),2,3)
                                if dt_type_history_prediction_type == "n":
                                    dttsaSupportServices.addDebugMsg(detection_msg)
                                    dttsaSupportServices.addVulnerableRepAttackPossibleDTs(ip[0],ip[1], detection_msg,"QoS","logic 3",attack_name,"group","PA",100,"member")
                                elif submitted_dt_type_history_multi_values== False and (submitted_dt_type_history != "c" or submitted_dt_type_history !="m") and (dt_type_history_prediction_type != "c" or dt_type_history_prediction_type != "m") :
                                    dttsaSupportServices.addDebugMsg(detection_msg)
                                    dttsaSupportServices.addVulnerableRepAttackPossibleDTs(ip[0],ip[1], detection_msg,"QoS","logic 3",attack_name,"group","PA",100,"member") 
                                considerd_DTs.append(ip[0])
                            else:
                                considerd_DTs.append(ip[0])

                        #Values
                        for ip in values_impact_predictions:
                            dttsaSupportServices.addDebugMsg(" logic 3 values ip[2] values "+ str(ip[2]))
                            dttsaSupportServices.addDebugMsg(" considered DTs  "+ str(considerd_DTs))
                            if ip[2] != majority_impact_prediction and ip[0] not in considerd_DTs:
                                attack_name = ""
                                if majority_impact_prediction == "n":
                                    if ip[2] == "c" or ip[2] == "m":
                                        attack_name = "Bad Mouthing"
                                        dt_qos_attack = True
                                        dt_report_dt_id = ip[0]
                                        dt_attacked_dt_id = ip[1]
                                elif majority_impact_prediction == "c" or  majority_impact_prediction == "m":
                                    if ip[2] == "c" or ip[2] == "n":
                                        attack_name = "Self Promote"
                                        dt_qos_attack = True
                                        dt_report_dt_id = ip[0]
                                        dt_attacked_dt_id = ip[1]
                                else:
                                    attack_name = "majority "+ majority_impact_prediction + " reported "+ip[2]
                                dt_attack_name = attack_name
                                print("DT ", ip[0]," reporting DT ", ip[1], " incorrectly (DT) "+attack_name)
                                detection_msg = "DT " + str(ip[0]) + " reporting DT " + str(ip[1])+" incorrectly in Values (DT)"+attack_name +" Overall disagree using only DTTSA to determine"
                                submitted_dt_type_history_multi_values,submitted_dt_type_history = impactMajorityDetector(dttsaSupportServices.getDTtypePredictionHistory(dt[0]),2,3)

                                if dt_type_history_prediction_type == "n":
                                    dttsaSupportServices.addDebugMsg(detection_msg)
                                    dttsaSupportServices.addVulnerableRepAttackPossibleDTs(ip[0],ip[1], detection_msg,"Values","logic 3",attack_name,"group","PA",100,"member")
                                elif submitted_dt_type_history_multi_values== False and (submitted_dt_type_history != "c" or submitted_dt_type_history !="m") and (dt_type_history_prediction_type != "c" or dt_type_history_prediction_type != "m") :
                                    dttsaSupportServices.addDebugMsg(detection_msg)
                                    dttsaSupportServices.addVulnerableRepAttackPossibleDTs(ip[0],ip[1], detection_msg,"Values","logic 3",attack_name,"group","PA",100,"member")
                                considerd_DTs.append(ip[0])
                            else:
                                considerd_DTs.append(ip[0])
                    elif dt_type_history_prediction_multiple_majority == False:
                        #considering DT type prediction history
                        majority_impact_prediction = dt_type_history_prediction_type
                
                        #QoS
                        for ip in qos_impact_predictions:
                            dttsaSupportServices.addDebugMsg(" logic 4 qos ip[2] values "+ str(ip[2]))
                            dttsaSupportServices.addDebugMsg(" considered DTs  "+ str(considerd_DTs))
                            if ip[2] != majority_impact_prediction and ip[0] not in considerd_DTs:
                                attack_name = ""
                                if majority_impact_prediction == "n":
                                    if ip[2] == "c" or ip[2] == "m":
                                        attack_name = "Bad Mouthing"
                                        dt_qos_attack = True
                                        dt_report_dt_id = ip[0]
                                        dt_attacked_dt_id = ip[1]
                                elif majority_impact_prediction == "c" or  majority_impact_prediction == "m":
                                    if ip[2] == "c" or ip[2] == "n":
                                        attack_name = "Self Promote"
                                        dt_qos_attack = True
                                        dt_report_dt_id = ip[0]
                                        dt_attacked_dt_id = ip[1]
                                else:
                                    attack_name = "majority "+ majority_impact_prediction + " reported "+ip[2]
                                dt_attack_name = attack_name
                                print("DT ", ip[0]," reporting DT ", ip[1], " incorrectly in QoS (DT) "+attack_name)
                                detection_msg = "DT " + str(ip[0]) + " reporting DT " + str(ip[1])+" incorrectly (DT)"+attack_name +" Overall disagree Histroy"
                                submitted_dt_type_history_multi_values,submitted_dt_type_history = impactMajorityDetector(dttsaSupportServices.getDTtypePredictionHistory(dt[0]),2,3)
                                if submitted_dt_type_history_multi_values== False and (submitted_dt_type_history != "c" or submitted_dt_type_history !="m") and (dt_type_history_prediction_type != "c" or dt_type_history_prediction_type != "m") :
                                    dttsaSupportServices.addDebugMsg(detection_msg)
                                    dttsaSupportServices.addVulnerableRepAttackPossibleDTs(ip[0],ip[1], detection_msg,"QoS","logic 4",attack_name,"group","PA",100,"member")
                                considerd_DTs.append(ip[0])
                            else:
                                considerd_DTs.append(ip[0])

                        #Values
                        for ip in values_impact_predictions:
                            dttsaSupportServices.addDebugMsg(" logic 4 values ip[2] values "+ str(ip[2]))
                            dttsaSupportServices.addDebugMsg(" considered DTs  "+ str(considerd_DTs))
                            if ip[2] != majority_impact_prediction and ip[0] not in considerd_DTs:
                                attack_name = ""
                                if majority_impact_prediction == "n":
                                    if ip[2] == "c" or ip[2] == "m":
                                        attack_name = "Bad Mouthing"
                                        dt_qos_attack = True
                                        dt_report_dt_id = ip[0]
                                        dt_attacked_dt_id = ip[1]
                                elif majority_impact_prediction == "c" or  majority_impact_prediction == "m":
                                    if ip[2] == "c" or ip[2] == "n":
                                        attack_name = "Self Promote"
                                        dt_qos_attack = True
                                        dt_report_dt_id = ip[0]
                                        dt_attacked_dt_id = ip[1]
                                else:
                                    attack_name = "majority "+ majority_impact_prediction + " reported "+ip[2]
                                dt_attack_name = attack_name
                                print("DT ", ip[0]," reporting DT ", ip[1], " incorrectly (DT) "+attack_name)
                                detection_msg = "DT " + str(ip[0]) + " reporting DT " + str(ip[1])+" incorrectly in Values (DT)"+attack_name +" Overall disagree History "
                                submitted_dt_type_history_multi_values,submitted_dt_type_history = impactMajorityDetector(dttsaSupportServices.getDTtypePredictionHistory(dt[0]),2,3)
                                if submitted_dt_type_history_multi_values== False and (submitted_dt_type_history != "c" or submitted_dt_type_history !="m") and (dt_type_history_prediction_type != "c" or dt_type_history_prediction_type != "m") :
                                    dttsaSupportServices.addDebugMsg(detection_msg)
                                    dttsaSupportServices.addVulnerableRepAttackPossibleDTs(ip[0],ip[1], detection_msg,"Values","logic 4",attack_name,"group","PA",100,"member")
                                considerd_DTs.append(ip[0])
                            else:
                                considerd_DTs.append(ip[0])

    possible_attacks = dttsaSupportServices.getPossibleAttacks(3)
    for pa in possible_attacks:
        attack_counter = dttsaSupportServices.getPossibleAttackContinuityCount(pa[0],pa[1])
        if len(attack_counter)>=3:
            dttsaSupportServices.addDebugMsg("PA to RA true for DT "+str(pa[0]) +" and attacked DT "+str(pa[1]))
            values = []
            all_neg = True
            for ac in attack_counter:
                if ac[0] > 0:
                    all_neg = False
                values.append(ac[0])
            if all_neg == True:
                res = [-1 * values[i] for i in range(len(values))]
                v1 = res[0] - res [1]
                v2 = res[1] - res [2]
                if (v1-v2) == 0:
                    dttsaSupportServices.addDebugMsg("Continous attack ")
                    submitted_dt_type_history_multi_values,submitted_dt_type_history = impactMajorityDetector(dttsaSupportServices.getDTtypePredictionHistory(pa[0]),2,3)
                    attacked_dt_type_history_multi_values,attacked_dt_type_history = impactMajorityDetector(dttsaSupportServices.getDTtypePredictionHistory(pa[1]),2,3)
                    if submitted_dt_type_history_multi_values== False and (submitted_dt_type_history != "c" or submitted_dt_type_history !="m") and (attacked_dt_type_history != "c" or attacked_dt_type_history != "m") :
                        detection_msg = "DT " + str(pa[0]) + " reporting DT " + str(pa[1])+" incorrectly. changing PA to RA"
                        dttsaSupportServices.addDebugMsg("Attack recorded")
                        dttsaSupportServices.addDebugMsg(detection_msg)
                        dttsaSupportServices.addVulnerableRepAttackPossibleDTs(pa[0],pa[1], detection_msg,"PA to RA","logic 5","Continuous","group","RA",100,"member")



        # if len(qos_impact_predictions)>=2:
        #     dttsaSupportServices.addDebugMsg("inside len impact >= 2 ")
        #     majority_impact_prediction = qos_impact_predictions[0][2]
        #     dttsa_prediction = dttsa_qos_classification[0][7]
        #     majority_agree_with_dttsa = True
        #     if majority_impact_prediction != dttsa_prediction:
        #         majority_agree_with_dttsa = False

        #     dttsaSupportServices.addDebugMsg("majority prediction: "+str(majority_impact_prediction))
        #     for ip in qos_impact_predictions:
        #         dttsaSupportServices.addDebugMsg(" ip[2] values "+ str(ip[2]))
        #         if ip[2] != majority_impact_prediction and ip[0] not in considerd_DTs:
        #             attack_name = ""
        #             if majority_impact_prediction == "n":
        #                 if ip[2] == "c" or ip[2] == "m":
        #                     attack_name = "Bad Mouthing"
        #                     dt_qos_attack = True
        #                     dt_report_dt_id = ip[0]
        #                     dt_attacked_dt_id = ip[1]
        #             elif majority_impact_prediction == "c" or  majority_impact_prediction == "m":
        #                 if ip[2] == "c" or ip[2] == "n":
        #                     attack_name = "Self Promote"
        #                     dt_qos_attack = True
        #                     dt_report_dt_id = ip[0]
        #                     dt_attacked_dt_id = ip[1]
        #             else:
        #                 attack_name = "majority "+ majority_impact_prediction + " reported "+ip[2]
        #             dt_attack_name = attack_name
        #             print("DT ", ip[0]," reporting DT ", ip[1], " incorrectly (DT) "+attack_name)
        #             detection_msg = "DT " + str(ip[0]) + " reporting DT " + str(ip[1])+" incorrectly (DT)"+attack_name +" majority agree with DTTSA "+str(majority_agree_with_dttsa)
        #             dttsaSupportServices.addVulnerableRepAttackPossibleDTs(ip[0],ip[1], detection_msg)
        #         else:
        #             considerd_DTs.append(ip[0])

        #         if dttsa_qos_classification[0][7] != ip[2] and ip[0] not in considerd_DTs:
        #             attack_name = ""
        #             if dttsa_qos_classification[0][7] == "n":
        #                 if ip[2] == "c" or ip[2] == "m":
        #                     attack_name = "Bad Mouthing"
        #                     dttsa_qos_attack = True
        #                     dttsa_report_dt_id = ip[0]
        #                     dttsa_attacked_dt_id = ip[1]
        #             elif dttsa_qos_classification[0][7] == "c" or  dttsa_qos_classification[0][7] == "m":
        #                 if ip[2] == "c" or ip[2] == "n":
        #                     attack_name = "Self Promote"
        #                     dttsa_qos_attack = True
        #                     dttsa_report_dt_id = ip[0]
        #                     dttsa_attacked_dt_id = ip[1]
        #             else:
        #                 attack_name = "DTTSA report "+ dttsa_qos_classification[0][7] + " reported "+ip[2]
        #             dttsa_attack_name = attack_name
        #             print("DT ", ip[0]," reporting DT ", ip[1], " incorrectly (DTTSA vs DT)")
        #             detection_msg = "DT " + str(ip[0])+ " reporting DT " + str(ip[1]) + " incorrectly (DTTSA vs DT) "+attack_name+" majority agree with DTTSA "+str(majority_agree_with_dttsa)
        #             dttsaSupportServices.addVulnerableRepAttackPossibleDTs(ip[0],ip[1],detection_msg)
        #         else:
        #             considerd_DTs.append(ip[0])
            
        #     if dttsa_attacked_dt_id == dt_attacked_dt_id and dttsa_report_dt_id == dt_report_dt_id and dttsa_qos_attack and dt_qos_attack and dttsa_attack_name==dt_attack_name:
        #         detection_msg = "DT " + str(ip[0])+ " reporting DT " + str(ip[1]) + " incorrectly (DTTSA and DT) Valid "+dt_attack_name+" majority agree with DTTSA "+str(majority_agree_with_dttsa)
        #         dttsaSupportServices.addVulnerableRepAttackPossibleDTs(ip[0],ip[1],detection_msg)

        #     # prediction_list = []
        #     # submitted_dt_ids = []
        #     # hit_counts = []
        #     # for i,ip in enumerate(impact_predictions):
        #     #     prediction_list.append(ip[2])
        #     #     submitted_dt_ids.append(ip[0])
        #     #     hit_counts.append(ip[3])
        #     # prediction_mismatch = DTSubmittedValueMismatchDetector(prediction_list)
        #     # dt_id_mismatch = DTSubmittedValueMismatchDetector(submitted_dt_ids)
        #     # hit_count_mismatch = DTSubmittedValueMismatchDetector(hit_counts)
        #     # print(submitted_dt_ids)
        #     # print(dt_id_mismatch)
        #     # if prediction_mismatch and dt_id_mismatch:
        #     #     print("different prediction from different DTs")
        #     #     max_hit_count = max(hit_counts)
        #     #     for i in range(len(prediction_list)):
        #     #         if hit_counts[i] == max_hit_count:
        #     # elif prediction_mismatch and dt_id_mismatch == False:
        #     #     print("different predictions same DT")
        #     # elif prediction_mismatch == False and dt_id_mismatch:
        #     #     print("same prediction different DTs")
        #     # v1 = impact_predictions[0][3]
        #     # v2 = impact_predictions[1][3]
        #     # if v1 == v2:
        #     #     print("first two impact scores are equal")
        #     #     if impact_predictions[0][0] == impact_predictions[1][0]:
        #     #         print("first two equal impact socres from same DT")
        #     #         majority_impact_prediction = impact_predictions[0][2]
        #     #     else:
        #     #         print("first two equal impact scores are not from same DT")
        #     #         print("checking both predictions are same or not")
        #     #         if impact_predictions[0][2] == impact_predictions[1][2]:
        #     #             print("not equal DTs but same prediction")

        #     # print(v1)
        # elif len(qos_impact_predictions) == 1:
        #     dttsaSupportServices.addDebugMsg(" inside len impact == 1 ")
        #     if dttsa_qos_classification[0][7] != qos_impact_predictions[0][2]:
                
        #         attack_name = ""
        #         if dttsa_qos_classification[0][7] == "n":
        #             if qos_impact_predictions[0][2] == "c" or qos_impact_predictions[0][2] == "m":
        #                 attack_name = "Bad Mouthing"
        #         elif dttsa_qos_classification[0][7] == "c" or  dttsa_qos_classification[0][7] == "m":
        #             if qos_impact_predictions[0][2] == "c" or qos_impact_predictions[0][2] == "n":
        #                 attack_name = "Self Promote"
        #         else:
        #             attack_name = "DTTSA report "+ dttsa_qos_classification[0][7] + " reported "+ qos_impact_predictions[0][2]
        #         print("DT ", qos_impact_predictions[0][0]," reporting DT ", qos_impact_predictions[0][1], " incorrectly (DTTSA vs DT)")
        #         detection_msg = "DT " + str(qos_impact_predictions[0][0])+ " reporting DT " + str(qos_impact_predictions[0][1]) + " incorrectly (DTTSA vs DT) "+attack_name+" majority agree with DTTSA "+str(majority_agree_with_dttsa)
        #         dttsaSupportServices.addVulnerableRepAttackPossibleDTs(qos_impact_predictions[0][0],qos_impact_predictions[0][1],detection_msg)

        print("______")

def generatePasswordHash(password):
    hashedPassword = hashlib.md5(str(password)).hexdigest()
    return hashedPassword

def checkAPIResults():
    print("API checking")
    dttsaSupportServices.recordExecutionStatus("API","Started")
    apiAnalyzer.checkSubmittedAPI()

def runQoSTest(test_type="i",concurrent_users=1,loop_times=1,iteration_count=0):
    QoSThreadCreated = False
    for thread in threading.enumerate():
        if thread.name == "QoS_"+test_type:
            QoSThreadCreated = True
    
    if not QoSThreadCreated:
        qosThread = threading.Thread(target=qosAnalyzer.QoSTest,args=(test_type,concurrent_users,loop_times,3600,5,0,iteration_count),name="QoS_"+test_type)
        qosThread.daemon = True
        qosThread.start()
        print("QoS_"+test_type+ " Test started")
        dttsaSupportServices.recordExecutionStatus("QoS_"+test_type,"Started",test_type)

def runBackupQoSTest(test_count=0):
    QoSThreadCreated = False
    for thread in threading.enumerate():
        if thread.name == "BQoS":
            QoSThreadCreated = True
    
    if not QoSThreadCreated:
        qosThread = threading.Thread(target=resilienceAnalyzer.backupServiceQoSTest,args=(test_count,),name="BQoS")
        qosThread.daemon = True
        qosThread.start()
        print("BQoS analysis started")
        dttsaSupportServices.recordExecutionStatus("BQoS","Started",test_count)

def runAPIAnalysis():
    # iteration count * -1 because using status coloumn
    apis_to_check = dttsaSupportServices.getAPIsToAnalyze('n','c','API Security',int(app.config['iteration_count'])*-1)
    for api in apis_to_check:
        apiAnalyzer.checkAPIVulnerbilities(api[1],api[0],api[2],api[5],api[4])
    malicious_apis = dttsaSupportServices.getAPIsToAnalyze('m','m','API Security',int(app.config['iteration_count'])*-1)
    for mapi in malicious_apis:
        previous_api_record = dttsaSupportServices.getPreviousAPIRecords(mapi[1],mapi[0],int(app.config['iteration_count'])*-1)
        for papi in previous_api_record:
            apiAnalyzer.addMaliciousAPIs(mapi[1],mapi[0],papi[3],papi[4],papi[5],papi[6])


def trustEffectCalculations():
    records = dttsaSupportServices.getDTDependencies()
    G=nx.DiGraph()
    for record in records:
        G.add_edge(str(record[1]), str(record[0]),weight=record[2]) #edge drawing from source to destination in order to correctly show that change order
        print(str(record[0]), str(record[1]),record[2])
    node_sizes =1500# [3 + 10 * i for i in range(len(G))]
    pos = nx.spring_layout(G)
    cmap = plt.cm.plasma
    nx.draw_networkx(G,pos,node_size=1500, node_color='yellow', font_size=8, font_weight='bold',with_labels=True,arrows=True)
    # nx.draw_networkx_nodes(G,pos,node_size=node_sizes,node_color='yellow')
    # nx.draw_networkx_edges(G,pos,node_size=node_sizes,arrowstyle="->",arrowsize=10,edge_cmap=cmap,width=2)
    #print(nx.is_directed(G))
    #for record in records:
        #p = nx.dijkstra_predecessor_and_distance(G,str(record[0]))
    p = nx.shortest_path(G)
    trust_score = []
    te = []
    #p = {'1': {'1': ['1'], '4': ['1', '4'], '2': ['1', '4', '2']}, '4': {'4': ['4'], '2': ['4', '2'], '1': ['4', '2', '1']}, '2': {'2': ['2'], '1': ['2', '1'], '4': ['2', '1', '4']}, '3': {'3': ['3'], '1': ['3', '1'], '4': ['3', '1', '4'], '2': ['3', '1', '4', '2']}, '5': {'5': ['5'], '2': ['5', '2'], '4': ['5', '4'], '1': ['5', '2', '1']}}
    #hop_count = 0
    influence = 0.5
    DTs = p.keys()
    print(DTs)
    trust_scores = dttsaSupportServices.getTrustCalculationsByIteration(app.config['iteration_count'])
    if len(trust_scores) > 0:
        for s in trust_scores:
            trust_score.insert(int(s[0])-1,s[1])
            te.append(0)
        print(trust_score)
        for dt in DTs:
            #print(p[dt])
            indirect_connets = p[dt].keys()
            #print(indirect_connets)
            for con in indirect_connets:
                #print(con)
                #print(len(p[dt][con]))
                if con != dt:
                    te[int(con)-1] = te[int(con)-1] + trust_score[int(dt)-1] * influence / (len(p[dt][con])-1)
                    dttsaSupportServices.addTrustEffectCalculation(dt,con,len(p[dt][con])-1,te[int(con)-1],trust_score[int(dt)-1])
        print(trust_score)
        print(te)
        return trust_score,te
    else:
        print("No trust scores to calculate")
        return -1,-1

def generateDependecyGraph():
    # evaluation()
    #df = pd.read_csv('data.csv')
    strfile="../Dashboardnew/static/assets/img/Graph.png"
    dependencyGraphImgs = "../Dashboardnew/static/assets/img/col/"
    records = dttsaSupportServices.getDTDependencies()
    save_loc = "csv/Graph.png"
    
    G=nx.DiGraph()
    for record in records:
        G.add_edge(str(record[1]), str(record[0]),weight=record[2]) #edge drawing from source to destination in order to correctly show that change order
        # print(str(record[0]), str(record[1]),record[2])
    color_map = []
    for node in G:
        # print("Node ",str(node))
        dt_type = dttsaSupportServices.getReputationLabelForDT(node)
        if (len(dt_type)>0):
            if  dt_type[0][0] == 'n':
                color_map.append('green')
            elif dt_type[0][0] == 'c':
                color_map.append('yellow')
            elif dt_type[0][0] == 'm':
                color_map.append('red')
            else:
                color_map.append('gray')
        else:
            color_map.append('gray')


    # node_sizes =1500# [3 + 10 * i for i in range(len(G))]
    pos = nx.spring_layout(G)
    # pos = nx.nx_pydot.graphviz_layout(G)
    cmap = plt.cm.plasma
    nx.draw_networkx(G,pos,node_size=1000, node_color=color_map, font_size=8, font_weight='bold',with_labels=True,arrows=True)
    # nx.draw_networkx_nodes(G,pos,node_size=node_sizes,node_color='yellow')
    # nx.draw_networkx_edges(G,pos,node_size=node_sizes,arrowstyle="->",arrowsize=10,edge_cmap=cmap,width=2)
    #print(nx.is_directed(G))
    #for record in records:
        #p = nx.dijkstra_predecessor_and_distance(G,str(record[0]))
    # p = nx.shortest_path(G)
    # trust_score = []
    # te = []
    # #p = {'1': {'1': ['1'], '4': ['1', '4'], '2': ['1', '4', '2']}, '4': {'4': ['4'], '2': ['4', '2'], '1': ['4', '2', '1']}, '2': {'2': ['2'], '1': ['2', '1'], '4': ['2', '1', '4']}, '3': {'3': ['3'], '1': ['3', '1'], '4': ['3', '1', '4'], '2': ['3', '1', '4', '2']}, '5': {'5': ['5'], '2': ['5', '2'], '4': ['5', '4'], '1': ['5', '2', '1']}}
    # #hop_count = 0
    # influence = 0.5
    # DTs = p.keys()
    # print(DTs)
    # trust_scores = dttsaSupportServices.getTrustCalculations()
    # if len(trust_score) > 0:
    #     for s in trust_scores:
    #         trust_score.insert(int(s[0])-1,s[1])
    #         te.append(0)
    #     print(trust_score)
    #     for dt in DTs:
    #         #print(p[dt])
    #         indirect_connets = p[dt].keys()
    #         #print(indirect_connets)
    #         for con in indirect_connets:
    #             #print(con)
    #             #print(len(p[dt][con]))
    #             if con != dt:
    #                 te[int(con)-1] = te[int(con)-1] + trust_score[int(dt)-1] * influence / (len(p[dt][con])-1)
    #                 dttsaSupportServices.addTrustEffectCalculation(dt,con,len(p[dt][con])-1,te[int(con)-1],trust_score[int(dt)-1])
    #     print(trust_score)
    #     print(te)
    # else:
    #     print("No trust scores to calculate")

    #nx.draw(G,pos,node_size=1500, node_color='yellow', font_size=8, font_weight='bold',with_labels=True,arrows=True)
    # labels = nx.get_edge_attributes(G,'weight')
    # nx.draw_networkx_edge_labels(G,pos,edge_labels=labels)

    #for dashboard
    if os.path.isfile(strfile):
        os.remove(strfile)
    plt.savefig(strfile, format="PNG")

    if app.config['dependecy_graph_image_counter'] == 0:
        image_names = os.listdir('../Dashboardnew/static/assets/img/col/')
        for i in image_names:
            os.remove(dependencyGraphImgs+str(i))

    #for Dependecy graph collection
    app.config.update(
        dependecy_graph_image_counter = app.config['dependecy_graph_image_counter']+ 1
    )
    plt.savefig(dependencyGraphImgs+str(app.config['dependecy_graph_image_counter'])+"_.png", format="PNG")

    #for csv folder
    if os.path.isfile(save_loc):
        os.remove(save_loc)
    plt.savefig(save_loc, format="PNG")
    plt.clf()

@app.route("/configqos")
def configureQoSParameters():
    test_count= request.args.get('numbertest')
    loop_count= request.args.get('loopcount')
    app.config.update(
        qos_number_of_tests = test_count
    )

    app.config.update(
        qos_loop_times = loop_count
    )
    msg = {"status" : "QoS Config Done"}, 200
    return msg

@app.route("/analyze")
def startAnalayze():
    '''
    check if DTs submitted values using
    SELECT * FROM dt_data_submission_tbl where status=1;
    then if not started start QOS and BQOS
    if finish QoS and BQOS 
    have a blocking conditional variable app.config['analysis_started']
    '''
    num_DTs = len(dttsaSupportServices.getDTIDs())
    num_DTs_submitted_final_values = len(dttsaSupportServices.getDTIDsSubmitDTReports())
    
    msg = ""
    if num_DTs > 0 and num_DTs_submitted_final_values > 0:
        submit_percentage = num_DTs_submitted_final_values / num_DTs * 100
        if submit_percentage >= 80.0 and app.config['analysis_started'] == False:
            print("Starting analysis")
            app.config.update(
                analysis_started = True
            )
            # runQoSTest(int(app.config['iteration_count']),5,2)
            # qosAnalysisManagement()
            runBackupQoSTest(test_count=int(app.config['iteration_count']))
            #TODO API analysis get all normal and submit again for analyze
            if int(app.config['iteration_count']) > 0:
                runAPIAnalysis()
            else:
                print("API analysis is already running")
            msg = "Analysis started"
        else:
            ret_value1 = dttsaSupportServices.qosExecutionStatus()
            ret_value2 = dttsaSupportServices.backupQoSExecutionStatus()
            ret_value3 = apiAnalyzer.APISecurityAnalysisStatus()
            if ret_value1 == "Finished" and ret_value2 == "Finished" and ret_value3 == "Finished" and app.config['qos_analysis_ongoing'] == False:
                evaluation()
                app.config.update(
                    analysis_started = False
                )

                app.config.update(
                    qos_analysis_started = False
                )
                
                reputationAnalysis()
                reputationAttackAnalysis()
                repAttackCheck()
                msg = "Evaluation completed, analysis completed"
            elif ret_value1== "Started" or ret_value2== "Started" or ret_value3 == "Started":
                msg = "Analysis Ongoing"
            elif ret_value1 == "Finished" and ret_value2 == "Finished" and app.config['qos_analysis_ongoing'] == False:
                counter = int(app.config['API_analysis_counter']) + 1
                app.config.update(
                    API_analysis_counter = counter
                )
                if int(app.config['API_analysis_counter']) == 3:
                    evaluation()
                    app.config.update(
                        analysis_started = False
                    )

                    app.config.update(
                        qos_analysis_started = False
                    )

                    app.config.update(
                    API_analysis_counter = 0
                    )
                
                    reputationAnalysis()
                    reputationAttackAnalysis()
                    repAttackCheck()
                    msg = "Evaluation completed, analysis completed"
                else:
                    msg = "Waiting for API analysis "+str(app.config['API_analysis_counter'])
            else:
                msg = "Analysis not started "+ str(submit_percentage) + "QoS:"+ret_value1+" BQoS:"+ret_value2+" API:"+ret_value3
    else:
        msg = "No DTs or No submitted values "+str(num_DTs_submitted_final_values)+":"+str(num_DTs)

    return {"status":str(msg)},200

def reputationAnalysis():
    dts = dttsaSupportServices.getDTIDs()
    trust_scores = dttsaSupportServices.getAllTrustScores()
    print(dts)
    print(trust_scores)
    for d in dts:
        data = []
        for t in trust_scores:
            if d[0] == t[0]:
                data.append(t[1])
        print(data)
        print(d[0])
        reputationClassification(d[0],data)

def reputationClassification(dt_id,data):
    pos_count = 0
    min_count = 0
    eq_count = 0
    status = ""
    for i,t in enumerate(data):
        print(i+1)
        if i+2 <= len(data):
            print("run")
            if data[i] < data[i+1]:
                pos_count += 1
            elif data[i] > data[i+1]:
                min_count += 1
            else:
                eq_count += 1

    print(pos_count)
    print(min_count)
    print(eq_count)

    #TODO refine the categorization logic
    if pos_count == min_count == eq_count:
        print("undecided")
        status = "undecided"
    elif min_count > pos_count and min_count > eq_count:
        print("negative")
        status = "negative"
    elif pos_count > min_count  and pos_count > eq_count:
        print("positive")
        status = "positive"
    elif eq_count > min_count and eq_count > pos_count:
        print("positive")
        status = "positive"
    elif eq_count == min_count:
        print("negative")
        status = "negative"
    elif pos_count == min_count:
        print("negative")
        status = "negative"
    elif pos_count == eq_count:
        print("positive")
        status = "positive"
    else:
        print("undecided")
        status = "undecided"
    
    dttsaSupportServices.addDTReputationCategorization(dt_id,pos_count,min_count,eq_count,status)

def reputationAttackAnalysis():
    normal_dts = dttsaSupportServices.getDTsByPrediction('n')
    if len(normal_dts) == 0:
        normal_dts = dttsaSupportServices.getDTsByPrediction('c')
    for ndt in normal_dts:
        trust_reports_values = dttsaSupportServices.getDTTrustReports(ndt[0],"Values")
        trust_reports_qos = dttsaSupportServices.getDTTrustReports(ndt[0],"QoS")
        print(trust_reports_values)
        print(trust_reports_qos)
        print("[][][][]")

@app.route("/reqchangereturn")
def requestChangeReturnFromChain():
    dt_id = request.args.get('dt')
    con_dt_id = request.args.get('con_dt')
    reply = request.args.get('reply')
    
    dt_url = dttsaSupportServices.getConnectionChangeDTUrl(dt_id,con_dt_id)
    dttsaSupportServices.updateConnectionChangeRequest(dt_id,con_dt_id,reply)
    for u in dt_url:
        res = requests.get(u[6]+"/reqchangereply?con_dt="+str(con_dt_id)+"&reply="+str(reply))
    msg = "done"
    return make_response(msg,200)



#/reqchange?dt=1
@app.route("/reqchange")
def requestConnectionChange():
    #TODO change oracle URL
    oracle_req_url = "http://34.16.92.58:9100"
    # oracle_req_url = "http://127.0.0.1:9100"
    dt_id = request.args.get('dt')
    con_dt_id = request.args.get('con_dt')
    dt_url=request.args.get('url')
    # v = random.randint(0,1)
    # if v == 1:
    #     dttsaSupportServices.addConnectionChangeRequest(dt_id,con_dt_id,"dt_rep_type","con_dt_rep_type",1)
    #     msg = {"change_req_status": "sucess"}
    # else:
    #     dttsaSupportServices.addConnectionChangeRequest(dt_id,con_dt_id,"dt_rep_type","con_dt_rep_type",0)
    #     msg = {"change_req_status": "fail"}
    
    dt_rep_counts = dttsaSupportServices.getReputationLabelForDT(dt_id)
    con_dt_rep_counts = dttsaSupportServices.getReputationLabelForDT(con_dt_id)
    dt_rep_type = ''
    con_dt_rep_type = ''
    permission = 0
    
    
    if (len(dt_rep_counts)>0):
        dt_rep_type =  dt_rep_counts[0][0]

    if (len(con_dt_rep_counts)>0):
        con_dt_rep_type =  con_dt_rep_counts[0][0]
    
    if dt_rep_type == 'n' and (con_dt_rep_type == 'c' or con_dt_rep_type == 'm'):
        dttsaSupportServices.addConnectionChangeRequest(dt_id,con_dt_id,dt_rep_type,con_dt_rep_type,"1",dt_url)
        oracle_url = oracle_req_url+"/firefly?dt="+str(dt_id)+"&condt="+str(con_dt_id)+"&rep=n"
        res = requests.get(oracle_url)
        msg = {"change_req_status": "sucess"}
    else:
        dttsaSupportServices.addConnectionChangeRequest(dt_id,con_dt_id,dt_rep_type,con_dt_rep_type,"0",dt_url)
        oracle_url = oracle_req_url+"/firefly?dt="+str(dt_id)+"&condt="+str(con_dt_id)+"&rep=m"
        res = requests.get(oracle_url)
        msg = {"change_req_status": "fail"}
    
    return make_response(msg,200)

@app.route("/getrepinfo")
def getTrustandReputationInfo():
    dt_id = request.args.get('dt')
    rep_counts = dttsaSupportServices.getReputationLabelForDT(dt_id)
    if (len(rep_counts)>0):
        res = {"rep_category": rep_counts[0][0]}
    else:
        res = {"rep_category": "False"}
    
    return make_response(res,200)

@app.route("/test")
def testService():
    count = request.args.get('count')
    # runQoSTest(thread_id=1,test_count=0,concurrent_users=1,loop_times=1)
    # runQoSTest(thread_id=2,test_count=0,concurrent_users=1,loop_times=1)
    # re = dttsaSupportServices.qosSpecificTestExecutionStatus("i")
    repAttackCheck()
    return "ok"

@app.route("/save")
def saveTblToCSV():
    res = dttsaSupportServices.saveTblsAsCSV()
    return res

@app.route("/register",methods=('GET','POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        org_code = request.form['org_code']

        dttsaSupportServices.userRegister(username,password,org_code)

        return redirect(url_for('index'))
    return render_template('home/login.html',reg_log="Register")

@app.route("/login", methods=('GET','POST'))
def login():
    if 'username' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        org_code = request.form['org_code']

        user = dttsaSupportServices.getUser(username,org_code)

        if len(user) == 1:
            if password.decode("utf-8")  == user[0][2]:
                session['username'] = username
                session['org_code'] = org_code
                return redirect(url_for('index'))
            else:
                return redirect(url_for('register',reg_log="Register"))
        else:
            return redirect(url_for('register',reg_log="Register"))
    return render_template('home/login.html',reg_log="Login")

def weightedAvg(low,mid,high):
    l=[low,mid,high]
    w = [3,2,1] #initial weights low=1 mid=2 high=3
    v = 0
    for i in range(len(l)):
        v = l[i]*w[i] + v
    v = v/sum(w)
    return round(v,2)

def weightedAvgHighMidLow(low,mid,high):
    print()
    l=[low,mid,high]
    w = [1,2,3] #initial weights low=1 mid=2 high=3
    v = 0
    print(l)
    for i in range(len(l)):
        v = l[i]*w[i] + v
        print(v)
    v = v/sum(w)
    print(v)
    return round(v,2)

@app.route('/dependgraph')
def createDependencyGraph():
    generateDependecyGraph()
    return "Dependency graph created"

def APIDTTypeDetector(v):
    m_api_value = 23.5
    c_api_value = 24.9
    n_api_value = 25
    if v >= n_api_value:
        return "n"
    elif v >= m_api_value and v <= c_api_value:
        return "c"
    else:
        return "m"

def DTTypeDetector(l):
    if len(l) > 0 :
        if l.count(0) == 2:
            m = max(l)
            i = l.index(m)
            if i == 0:
                return "n"
            elif i == 1:
                return "c"
            else:
                return "m"
        elif len(l) == len(set(l)): #no duplicates
            m = max(l)
            i = l.index(m)
            if i == 0:
                return "n"
            elif i == 1:
                return "c"
            else:
                return "m"
        else:
            # TODO all counts are equal can be label as c instead of m
            if l[0] == l[1] == l[2] == 1:
                return "c"
            elif l[0] == l[1] == l[2] == 0:
                return "-"
            elif l[0] == l[1]:
                return "c"
            elif l[1] == l[2]:
                return "c"
            else:
                return "m"
    else:
        return "-"
    
def DTSubmittedValueMismatchDetector(l):
    init_value = l[0]
    for i in l:
        if i != init_value:
            return True
    return False

def dtTypePredictor(l):
    res = []

    n_count = l.count('n')
    res.append(n_count)
    c_count = l.count('c')
    res.append(c_count)
    m_count = l.count('m')
    res.append(m_count)
    non_count = l.count('-')
    res.append(non_count)

    max_val = max(res)
    c = res.count(max_val)
    if c == 1:
        i = res.index(max_val)
        if i == 0:
            return "n"
        elif i==1:
            return "c"
        else:
            return "m"
    # TODO create seperate cases, c=2 as c c=3 as m
    elif c == 2 or c == 3:
        return "c"
    else:
        return "m"

def trustScoreCalculation():
    n_weight = 3
    c_weight = 2
    m_weight = 1
    dts = dttsaSupportServices.getDTIDs()
    i_count = int(app.config['iteration_count']) + 1
    app.config.update(
            iteration_count = i_count
    )
    for dt in dts:
        dt_cat_trust_values = dttsaSupportServices.getDTTrustCalculations(dt[0])
        n_count = 0
        c_count = 0
        m_count = 0
        # print("raw counts")
        # print(dt_cat_trust_values)
        for v in dt_cat_trust_values:
            # print("v "+v[0])
            if v[0] == 'n':
                n_count = v[1]
            elif v[0] == 'c':
                c_count = v[1]
            elif v[0] == 'm':
                m_count = v[1]
        tot_cat_count = n_count + c_count + m_count
        trust_score = (n_weight*n_count+c_weight*c_count+m_weight*m_count)/(tot_cat_count*3)*100
        print("@@ DT @@")
        print(dt)
        print("n "+str(n_count)+" c "+str(c_count)+" m "+str(m_count))
        print(trust_score)
        dttsaSupportServices.addTrustScoresToTrustScoresTbl(app.config['iteration_count'],dt,n_count,c_count,m_count,trust_score)

def qosAnalysisEvaluation(test_type):
    qos_low = 0.5
    qos_mid = 0.6
    qos_high= 1.0

    dts = dttsaSupportServices.getDTIDs()
    for dt in dts:
        low_count = 0
        mid_count = 0
        high_count = 0
        qos_counts = []
        dttsa_qos_counts = []
        values_qos = dttsaSupportServices.getDTDataByType(dt[0],"QoS")
        values_qos_dttsa = dttsaSupportServices.getDTTSAQoSValuesByTestType(dt[0],test_type)
        if len(values_qos) != 0:
            for v in values_qos:
                val = round(float(v[7]),1)
                if val <= qos_low:
                    low_count = low_count+1
                    dttsaSupportServices.dtTrustReportTbl(v[1],v[2],v[3],1,0,0)
                elif val >= qos_mid and val <= qos_high:
                    mid_count = mid_count+1
                    dttsaSupportServices.dtTrustReportTbl(v[1],v[2],v[3],0,1,0)
                else:
                    high_count = high_count +1
                    dttsaSupportServices.dtTrustReportTbl(v[1],v[2],v[3],0,0,1)
            
            qos_counts = [low_count,mid_count,high_count]
        low_count = 0
        mid_count = 0
        high_count = 0

        for v in values_qos_dttsa:
            val = round(float(v[11]),1)
            if val <= qos_low:
                low_count = low_count+1
            elif val >= qos_mid and val <= qos_high:
                mid_count = mid_count+1
            else:
                high_count = high_count +1
        dttsa_qos_counts = [low_count,mid_count,high_count]
        print(qos_counts)
        print(dttsa_qos_counts)

        if (dttsa_qos_counts[0] > 0 and dttsa_qos_counts[1]== 0 and dttsa_qos_counts[2] == 0):
            if len(qos_counts) > 0:
                if (qos_counts[0]>0 and qos_counts[1]==0 and qos_counts[2]==0):
                    print("Def Normal DT")
                    weighted_avg = weightedAvg(qos_counts[0],qos_counts[1],qos_counts[2])
                    dttsaSupportServices.recordTrustScores(dt[0],"DT QoS",low_count,mid_count,high_count,weighted_avg,DTTypeDetector(qos_counts))
                    weighted_avg = weightedAvg(dttsa_qos_counts[0],dttsa_qos_counts[1],dttsa_qos_counts[2])
                    dttsaSupportServices.recordTrustScores(dt[0],"DTTSA QoS",low_count,mid_count,high_count,weighted_avg,DTTypeDetector(dttsa_qos_counts))
            else:
                print("Def Normal DT only DTTSA")
                weighted_avg = weightedAvg(dttsa_qos_counts[0],dttsa_qos_counts[1],dttsa_qos_counts[2])
                dttsaSupportServices.recordTrustScores(dt[0],"DTTSA QoS",low_count,mid_count,high_count,weighted_avg,DTTypeDetector(dttsa_qos_counts))
        else:
            temp_type = DTTypeDetector(dttsa_qos_counts)
            dttsaSupportServices.addQoSStaging(dt[0],dttsa_qos_counts[0],dttsa_qos_counts[1],dttsa_qos_counts[2],"p"+temp_type,test_type)

def qosAnalysisLogic():
    print("£££ qosAnalysisLogic Called £££")
    qos_low = 0.5
    qos_mid = 0.6
    qos_high= 1.0

    low_count = 0
    mid_count = 0
    high_count = 0

    #Two different number of tests for APIs will be carriedout and these values config here
    x_test_count = 5
    # y_test_count = 10

    # qos_analysis_status = dttsaSupportServices.qosExecutionStatus()
    qos_analysis_status = ""
    print(app.config['qos_analysis_started'])
    # print(qos_analysis_status)
    print(app.config['analysis_started'])
    

    if (int(app.config['iteration_count']) == 0):
        print("__qos test statuses__")
        init_test_status = dttsaSupportServices.qosSpecificTestExecutionStatus("i")
        pn_test_status = dttsaSupportServices.qosSpecificTestExecutionStatus("pn")
        pc_test_status = dttsaSupportServices.qosSpecificTestExecutionStatus("pc")
        pm_test_status = dttsaSupportServices.qosSpecificTestExecutionStatus("pm")
        print(init_test_status)
        print(pn_test_status)
        print(pc_test_status)
        print(pm_test_status)

        if(pm_test_status=="Finished"):
            app.config.update(
                qos_pm_test_started = False
            )

        if(pn_test_status=="Finished"):
            app.config.update(
                qos_pn_test_started = False
            )

        if(pc_test_status=="Finished"):
            app.config.update(
                qos_pm_test_started = False
            )

        if (init_test_status == pn_test_status == pc_test_status == pm_test_status) and (init_test_status == "None" or init_test_status == "Finished"):
            qos_analysis_status = init_test_status
        else:
            qos_analysis_status = "Started"
        
        print(qos_analysis_status)
        print(int(int(app.config['qos_number_of_tests'])/int(app.config['qos_loop_times'])))
        if  app.config['qos_analysis_started'] == False and (qos_analysis_status == "None" or qos_analysis_status == "Finished") and app.config['analysis_started'] == True:
            print("Analysis Started and No QoS active tests")
            app.config.update(
                    qos_analysis_started = True
            )

            app.config.update(
                qos_analysis_ongoing = True
            )

        
        if init_test_status != 'Finished' and app.config['qos_analysis_started'] == True and app.config['qos_init_test_started'] == False and app.config['qos_pn_test_started'] == False and app.config['qos_pc_test_started'] == False and app.config['qos_pm_test_started'] == False:
            print("Init test")
            app.config.update(
                qos_init_test_started = True
            )
            app.config.update(
                qos_analysis_ongoing = True
            )
            runQoSTest(test_type="i",concurrent_users=int(app.config['qos_number_of_tests']),loop_times=int(app.config['qos_loop_times']))

            
        if init_test_status == 'Finished' and app.config['qos_analysis_started'] == True and app.config['qos_init_test_started'] == True:
            print("initial categorization")
            qosAnalysisEvaluation("i")
            app.config.update(
                qos_init_test_started = False
            )

        if init_test_status == 'Finished' and app.config['qos_analysis_started'] == True and app.config['qos_init_test_started'] == False and app.config['qos_pn_test_started'] == False and app.config['qos_pc_test_started'] == False and app.config['qos_pm_test_started'] == False:
            print("get dts from staging and run concurrent tests for pn,pc,and pm")
            if  (pm_test_status !="Finished" and pc_test_status!="Finished" and pm_test_status!="Finished") or (pm_test_status !="Started" and pc_test_status!="Started" and pm_test_status!="Started"):
                app.config.update(
                    qos_pn_test_started = True
                )
                runQoSTest(test_type="pn",concurrent_users=int(int(app.config['qos_number_of_tests'])/int(app.config['qos_loop_times'])),loop_times=int(app.config['qos_loop_times'])*2)

                app.config.update(
                    qos_pc_test_started = True
                )
                runQoSTest(test_type="pc",concurrent_users=int(int(app.config['qos_number_of_tests'])/int(app.config['qos_loop_times'])),loop_times=int(app.config['qos_loop_times'])*2)

                app.config.update(
                    qos_pm_test_started = True
                )

                app.config.update(
                    qos_analysis_ongoing = True
                )
                runQoSTest(test_type="pm",concurrent_users=int(app.config['qos_number_of_tests']),loop_times=int(app.config['qos_loop_times']))
            
            #get dts from staging and run concurrent tests for pn,pc,and pm
        
        if (app.config['qos_analysis_started'] == True and pm_test_status =="Finished" and pc_test_status =="Finished" and pm_test_status =="Finished" and qos_analysis_status=="Finished"):
            print("P tests finished")
            app.config.update(
                qos_analysis_ongoing = False
            )
            # print("initial categorization")
            # qosAnalysisEvaluation("i")
            # app.config.update(
            #     qos_analysis_started = False
            # )
    else:
        print("__"+ str(app.config['iteration_count'])+" test__")
        n_test_status = dttsaSupportServices.qosSpecificTestExecutionStatus("n")
        c_test_status = dttsaSupportServices.qosSpecificTestExecutionStatus("c")
        m_test_status = dttsaSupportServices.qosSpecificTestExecutionStatus("m")

        print(n_test_status)
        print(c_test_status)
        print(m_test_status)

        if (n_test_status == c_test_status == m_test_status):
            qos_analysis_status = n_test_status
        else:
            qos_analysis_status = "Started"

        if  app.config['qos_analysis_started'] == False and (qos_analysis_status != "Started" or qos_analysis_status == "None" ) and app.config['analysis_started'] == True:
            print("Analysis Started and No QoS active tests")
            app.config.update(
                    qos_analysis_started = True
            )
            i_count = int(app.config['iteration_count']) * -1
            print(int(app.config['qos_number_of_tests'])/int(app.config['qos_loop_times']))
            runQoSTest(test_type="m",concurrent_users=int(app.config['qos_number_of_tests']),loop_times=int(app.config['qos_loop_times']),iteration_count=i_count)
            runQoSTest(test_type="c",concurrent_users=int(int(app.config['qos_number_of_tests'])/int(app.config['qos_loop_times'])),loop_times=int(app.config['qos_loop_times'])*2,iteration_count=i_count)
            runQoSTest(test_type="n",concurrent_users=int(int(app.config['qos_number_of_tests'])/int(app.config['qos_loop_times'])),loop_times=int(app.config['qos_loop_times'])*2,iteration_count=i_count)
        # else:
        #     if n_test_status == "Finished" and c_test_status == "Finished" and m_test_status=="Finished" and qos_analysis_status == "Finished":
        #         app.config.update(
        #             qos_analysis_started = False
        #         )

@app.route('/eval')
def evaluation():
    '''
    get all DT ids;
    DT wise, QoS and value analysis,final verdict, to list
    	value	   QoS
    low	    <1	 <0.5
    mid	 1.0-2.0 0.5-0.7
    high	2<	 0.7<
    [12,low_count,mid_count,high_count]
    weigted average 
    round up 1 <2= normal 2-3= changing over 3 = malicious
    round up 2 <1 normal 1-2= changing  over 2 = malicious
    '''
    qos_low = 0.5
    qos_mid = 0.6
    qos_high= 1.0

    value_low = 1.4
    value_mid = 1.5
    value_high = 2.0

    low_count = 0
    mid_count = 0
    high_count = 0

    normal_mark = 1
    chainging_mark = 2
    final_results = []
    dts = dttsaSupportServices.getDTIDs()
    qos_results = []
    val_results = []
    dttsa_qos_results = []
    dttsa_backup_qos_results = []
    dttsaSupportServices.truncateTempTrustScores()
    for dt in dts:
        qos_counts = []
        value_counts = []
        detection = ""
        values_qos = dttsaSupportServices.getDTDataByType(dt[0],"QoS")
        values_data = dttsaSupportServices.getDTDataByType(dt[0],"Values")
        values_qos_dttsa = dttsaSupportServices.getDTTSAQoSValues(dt[0])
        values_backup_qos = dttsaSupportServices.getDTTSABackupQoSValues(dt[0])

        #TODO check for QoS on DT level
        if len(values_qos) != 0:
            for v in values_qos:
                val = round(float(v[7]),1)
                if val <= qos_low:
                    low_count = low_count+1
                    dttsaSupportServices.dtTrustReportTbl(v[1],v[2],v[3],1,0,0)
                elif val >= qos_mid and val <= qos_high:
                    mid_count = mid_count+1
                    dttsaSupportServices.dtTrustReportTbl(v[1],v[2],v[3],0,1,0)
                else:
                    high_count = high_count +1
                    dttsaSupportServices.dtTrustReportTbl(v[1],v[2],v[3],0,0,1)
            
            qos_counts = [low_count,mid_count,high_count]
            weighted_avg = weightedAvg(low_count,mid_count,high_count)
            temp_results = [dt[0],qos_counts,weighted_avg,DTTypeDetector(qos_counts)]
            dttsaSupportServices.recordTrustScores(dt[0],"DT QoS",low_count,mid_count,high_count,weighted_avg,DTTypeDetector(qos_counts))
            qos_results.append(temp_results)
        low_count = 0
        mid_count = 0
        high_count = 0
        
        for v in values_qos_dttsa:
            val = round(float(v[11]),1)
            if val <= qos_low:
                low_count = low_count+1
            elif val >= qos_mid and val <= qos_high:
                mid_count = mid_count+1
            else:
                high_count = high_count +1
        dttsa_qos_counts = [low_count,mid_count,high_count]
        weighted_avg = weightedAvg(low_count,mid_count,high_count)
        temp_results = [dt[0],dttsa_qos_counts,weighted_avg,DTTypeDetector(dttsa_qos_counts)]
        dttsaSupportServices.recordTrustScores(dt[0],"DTTSA QoS",low_count,mid_count,high_count,weighted_avg,DTTypeDetector(dttsa_qos_counts))
        dttsa_qos_results.append(temp_results)
        low_count = 0
        mid_count = 0
        high_count = 0

        if len(values_backup_qos) == 0:
            dttsa_backup_qos_results.append([dt[0],0])
        else:
            for v in values_backup_qos:
                val = round(float(v[11]),1)
                if val <= qos_low:
                    low_count = low_count+1
                elif val >= qos_mid and val <= qos_high:
                    mid_count = mid_count+1
                else:
                    high_count = high_count +1
            dttsa_qos_counts = [low_count,mid_count,high_count]
            weighted_avg = weightedAvg(low_count,mid_count,high_count)
            #TODO if there is a backup QoS prediction, give a lower prediction because not all DTs have a backup.
            backup_qos_type_predict = DTTypeDetector(dttsa_qos_counts)
            if backup_qos_type_predict == "m":
                backup_qos_type_predict = "c"
            elif backup_qos_type_predict == "c":
                backup_qos_type_predict = "n"
            temp_results = [dt[0],dttsa_qos_counts,weighted_avg,backup_qos_type_predict]
            dttsaSupportServices.recordTrustScores(dt[0],"Backup QoS",low_count,mid_count,high_count,weighted_avg,backup_qos_type_predict)
            dttsa_backup_qos_results.append(temp_results)
            low_count = 0
            mid_count = 0
            high_count = 0
        #TODO check for data availability on DT level value analysis
        if len(values_data) != 0:
            for v in values_data:
                val = round(float(v[4]),1)
                if val <= value_low:
                    low_count = low_count+1
                    dttsaSupportServices.dtTrustReportTbl(v[1],v[2],v[3],1,0,0)
                elif val >= value_mid and val <= value_high:
                    mid_count = mid_count+1
                    dttsaSupportServices.dtTrustReportTbl(v[1],v[2],v[3],0,1,0)
                else:
                    high_count = high_count +1
                    dttsaSupportServices.dtTrustReportTbl(v[1],v[2],v[3],0,0,1)
            value_counts = [low_count,mid_count,high_count]
            weighted_avg = weightedAvg(low_count,mid_count,high_count)
            temp_results = [dt[0],value_counts,weighted_avg,DTTypeDetector(value_counts)]
            dttsaSupportServices.recordTrustScores(dt[0],"DT Values",low_count,mid_count,high_count,weighted_avg,DTTypeDetector(value_counts))
            #TODO goal analysis use the same value analysis
            # dttsaSupportServices.recordTrustScores(dt[0],"Goal Analysis",low_count,mid_count,high_count,weighted_avg,DTTypeDetector(value_counts))
            val_results.append(temp_results)
        low_count = 0
        mid_count = 0
        high_count = 0

        # if weighted_avg < normal_mark :
        #     detection = "Normal"
        # elif weighted_avg >= normal_mark and weighted_avg <= chainging_mark:
        #     detection = "Changing"
        # else:
        #     detection = "Malicious"
        # t = [dt[0],low_count,mid_count,high_count,weighted_avg,detection]
        # final_results.append(t)
    getAPIVulnerbilityresults = dttsaSupportServices.getAPIVulnerbilityFinalValues()
    api_results = []
    total_api_vulnerbility_tests = 20
    low_api_vulnerbility_tests = 9
    mid_api_vulnerbility_tests = 2
    high_api_vulnerbility_tests = 9
    number_of_services = 4
    for res in getAPIVulnerbilityresults:
        weighted_avg = weightedAvgHighMidLow(( low_api_vulnerbility_tests*number_of_services - int(res[1])),(mid_api_vulnerbility_tests*number_of_services - int(res[2])),(high_api_vulnerbility_tests*number_of_services - int(res[3])))
        api_results.append([res[0],res[1],res[2],res[3],weighted_avg,APIDTTypeDetector(weighted_avg)])
        dttsaSupportServices.recordTrustScores(res[0],"API Security",res[1],res[2],res[3],weighted_avg,APIDTTypeDetector(weighted_avg))
    
    # records = dttsaSupportServices.getDTtypePredictions()
    print("called")
    # print(dts)
    for dt in dts:
        # print(dt)
        records = dttsaSupportServices.getDTtypePredictions(dt[0])
        res = []
        # api_analysis_tested = False
        for r in records:
            # if r[2] == 'API Security':
            #     api_analysis_tested = True
            res.append(r[1])
        # if api_analysis_tested == False:
        #     previous_api_result = dttsaSupportServices.getPreviousAPIPrediction(dt[0],int(app.config['iteration_count']) * -1)
        #     for p in previous_api_result:
        #         res.append(p[1])
        print(res)
        predicted_type = dtTypePredictor(res)
        value_mismatch = DTSubmittedValueMismatchDetector(res)
        # if value_mismatch:
        #     #add to table
        #     dttsaSupportServices.addVulnerableRepAttackPossibleDTs(dt[0])
        # print("Dt ID" , str(dt[0]))
        #TODO uncommented adding DTs calculations available back to DT type table
        type_record = dttsaSupportServices.getDTType(dt[0])
        print("type record", str(len(type_record)))
        if (len(type_record) != 1 ):
            assigned_dt_type = getDTType(dt[0])
            dttsaSupportServices.addDTType(dt[0],assigned_dt_type)
            dttsaSupportServices.updateDTTypeTblWithPrediction(dt[0],predicted_type)
        else:
            dttsaSupportServices.updateDTTypeTblWithPrediction(dt[0],predicted_type)

    trustScoreCalculation()
    trustEffectCalculations()
    dttsaSupportServices.updateStatusforTbls(int(app.config['iteration_count']) * -1)

    print("___")
    print(qos_results)
    print("___")
    print(dttsa_qos_results)
    print("___")
    print(dttsa_backup_qos_results)
    print("___")
    print(val_results)
    print("___")
    print(api_results)
    print("___")
    # print(final_results)
    return "okay"

def getDTType(dt_id):
    dt_details = dttsaSupportServices.getDTDetails(dt_id)
    print("DT_url len ", str(len(dt_details)))
    if len(dt_details) > 0:
        print("DT_url ", dt_details[0][5])
        dt_url = dt_details[0][5]+"/details"
        r = requests.get(dt_url,verify=False)
        data = json.loads(r.text)
        print(data['dt_type'])
        return data['dt_type']

@app.route('/network')
def DisplayDTNetwork():
    image_names = os.listdir('../Dashboardnew/static/assets/img/col/')
    urls = []
    for i in image_names:
        urls.append("/static/assets/img/col/"+str(i))

    return render_template('home/network.html',image_names = urls)
        
@app.route('/logout')
def logout():
    session.pop('username',None)
    session.pop('org_code',None)
    return render_template('home/login.html',reg_log="Login")

@app.route('/')
def index():
    # evaluation()
    generateDependecyGraph()
    # trust_score = dttsaSupportServices.getTrustCalculations()
    trust_score = ""
    te = ""
    orgList = dttsaSupportServices.getOrgList()
    DTs = dttsaSupportServices.getDTs()
    qos_data = dttsaSupportServices.getQoSdata()
    trust_calculation_records = dttsaSupportServices.getTrustCalculationsRecords()


    return render_template('home/index.html',segment='index',orgList=orgList, DTs = DTs,qos_data=qos_data,trust_score=trust_score,te=te,trust_calculation_records=trust_calculation_records)

@app.route('/repattacklog')
def reputationAttackLog():
    dt_id = request.args.get('dt')
    attack_DT = request.args.get('attdt')   #DT id to attack on a selfpromote same DT ID
    strength = request.args.get('strength') #up one impact level or maximum 1=mid 2=high
    attack = request.args.get('attack') #bm = bad mouthing sp= self promoting
    type_of_attack = request.args.get('type')   #i=individual g=group
    initiator_dt_id = request.args.get('init_dt')
    dttsaSupportServices.addDTReputationAttackLog(dt_id,attack_DT,attack,strength,type_of_attack,initiator_dt_id)
    res = {"msg": "Rep attack logged"}
    return make_response(res,200)

def imapactCategorization(val,test_type):
    low_count = 0
    mid_count = 0
    high_count = 0
    if test_type == 'QoS': 
        if val <= float(config['trust_calculation']['qos_low']):
            low_count = low_count+1
        elif val >= float(config['trust_calculation']['qos_mid']) and val <= float(config['trust_calculation']['qos_high']):
            mid_count = mid_count+1
        else:
            high_count = high_count +1
    elif test_type == 'Values':
        if val <= float(config['trust_calculation']['value_low']):
            low_count = low_count+1
        elif val >= float(config['trust_calculation']['value_mid']) and val <= float(config['trust_calculation']['value_high']):
            mid_count = mid_count+1
        else:
            high_count = high_count +1
    impact_counts = [low_count,mid_count,high_count]
    return impact_counts,DTTypeDetector(impact_counts)

def dtValueImpactCategorization(dt_id,report):
    for r in report:
        sub_dt_id = str(r['dt_id'])
        data_type = str(r['data_type'])
        stdev_value = str(r['stdev_value'])
        min = str(r['min'])
        max = str(r['max'])
        avg = str(r['avg'])
        if data_type == 'QoS' and sub_dt_id != '-111111111' and sub_dt_id != dt_id:
            category = data_type
            val,classification = imapactCategorization(float(avg),'QoS')
            dttsaSupportServices.addDTReportImpactCategories(dt_id,sub_dt_id,category,"avg",val[0],val[1],val[2],classification)
        elif data_type == 'Values' and sub_dt_id != '-111111111' and sub_dt_id != dt_id:
            category = data_type
            val,classification = imapactCategorization(float(stdev_value),'Values')
            dttsaSupportServices.addDTReportImpactCategories(dt_id,sub_dt_id,category,"std",val[0],val[1],val[2],classification)
        
@app.post("/report")
def submitDTReports():
    content = request.get_json()
    msg = ""
    try:
        dt_id = str(content['dt_id'])
        report = content['report']
        change_con_report = content['change_con_report']
        dt_type = str(content['dt_type'])
        dttsaSupportServices.addDTType(dt_id,dt_type)
        dttsaSupportServices.addDTReports(dt_id,report)
        dttsaSupportServices.addDTChangeConReports(dt_id,change_con_report)
        dtValueImpactCategorization(dt_id,report)
        msg = "sucesss"
        res = {"status": msg},200
    except Exception as e:
        msg = str(e)
        res = {"status":"error","msg":msg},400
    return res

@app.route("/DT",methods=('GET','POST'))
def DT():
    return render_template('home/page-user.html',segment='DT')

@app.route("/config",methods=('GET','POST'))
def trustSecurityConfig():
    return render_template('home/dttsa-config.html',segment='dttsa_config')

@app.post("/sublist")
def submitSubs():
    content = request.get_json()
    msg = ""
    try:
        dt_id = str(content['dt_id'])
        subList = content['sublist']
        dttsaSupportServices.addDTSubs(dt_id,subList)
        msg = "sucesss"
        res = {"status": msg},200
    except Exception as e:
        msg = str(e)
        res = {"status":"error","msg":msg},400
    return res

@app.post("/DTReg")
def DTReg():
    content = request.get_json()
    msg = ""
    try:
        org_code = str(content['org_code'])
        DT_code = str(content['DT_code'])
        DT_name = str(content['DT_name'])
        DT_description = str(content['DT_Description'])
        DT_IP = content['DT_IP']
        APIs = content['APIs']
        print(APIs)
        DT_ID = dttsaSupportServices.addDT(org_code,DT_code,DT_name,DT_description,DT_IP) #add DT details to DT_tbl
        if DT_ID > 0:
            #TODO send post req headers
            APIList = dttsaSupportServices.addAPIs(APIs,DT_ID) #add individual APIs to API_tbl
            for api in APIList:
                apiAnalyzer.checkAPIVulnerbilities(api[0],api[1],api[2],api[3],api[4]) #sending APIs to vulnerability check service #DT_ID,API_ID,url,sample_json,type_req
                qosAnalyzer.addAPIForQoS(api[0],api[1]) #DT_ID,API_ID
            msg = "success"
        else:
            msg = "fail"
        
        res = {"status" : msg, "DT_ID": DT_ID}, 200
    except Exception as e:
        print(e)
        res = {"status" : "Failed"}
    return jsonify(res)

@app.get("/qosstat")
def qosStatus():
    ret_value = dttsaSupportServices.qosExecutionStatus()
    return {"status":str(ret_value)},200

@app.get("/bqosstat")
def bqosStatus():
    ret_value = dttsaSupportServices.backupQoSExecutionStatus()
    return {"status":str(ret_value)},200

@app.get("/getorg")
def getvalues():
    orgList = dttsaSupportServices.getOrgList()
    
    res = [
        {
            "id": org[0],
            "org_name":org[1],
            "org_code":org[2],
            "timestamp": org[3]
        } for org in orgList]
    return {"count": len(res), "users" : res}

@app.get("/getownapis/")
def getOwnAPIs():
    DT_ID  = request.args.get('dt_id'),
    API_list = dttsaSupportServices.getDTAPIs(DT_ID)
    
    res = [
        {
            "API_ID": api[0],
            "URL": api[2]
        } for api in API_list]
    return {"count": len(res), "APIs" : res}

@app.get("/updatesubs")
def updateDTSubs():
    DT_ID  = request.args.get('dt_id')
    sub_dt_id = request.args.get('sub_dt_id')
    dttsaSupportServices.updateDTSubs(DT_ID,sub_dt_id)
    res = {"status" : "sucess"}
    return make_response(res,200)

@app.get("/getapis/")
def getDTAPIs():
    DT_ID  = request.args.get('dt_id')
    res = []
    rep_counts = dttsaSupportServices.getReputationLabelForDT(DT_ID)
    print(rep_counts)
    if (len(rep_counts)>0):
        # res = {"rep_category": }
        print(rep_counts[0][0])
        if rep_counts[0][0] != 'm' or rep_counts[0][0] != 'c' :
            API_list = dttsaSupportServices.getOtherDTAPIsConsideringTrust(DT_ID)
            res = [
            {
                "API_ID": api[0],
                "DT_ID": api[1],
                "URL": api[2],
                "desc": api[3],
                "type": api[4],
                "sample": api[5]
            } for api in API_list]
    else:
        API_list = dttsaSupportServices.getOtherDTAPIs(DT_ID)
        res = [
        {
            "API_ID": api[0],
            "DT_ID": api[1],
            "URL": api[2],
            "desc": api[3],
            "type": api[4],
            "sample": api[5]
        } for api in API_list]

    
    return {"count": len(res), "APIs" : res}

@app.route('/regbackup')
def setvalue():
    backuplocation = request.args.get('backupip')
    DT_ID = request.args.get('dtid')

    retVal = resilienceAnalyzer.addBackupServiceLocations(DT_ID,backuplocation)
    print(retVal)
    if retVal == "True":
        msg = {"status" : "Success", "DT_ID": DT_ID}, 200
    else:
        msg = {"status" : "Failed", "DT_ID": DT_ID}, 400
    print(msg)
    return msg

@app.route('/testbackupservices')
def testBackupServices():
    test_count = request.args.get('testcount')
    runBackupQoSTest(test_count)
    # resilienceAnalyzer.backupServiceQoSTest()
    # if retVal == True:
    #     msg = {"status" : "Success"}, 200
    # else:
    #     msg = {"status" : "Failed"}, 400
    # print(msg)
    msg = {"status" : "QoS Test Started"}, 200
    return msg

@app.route('/testqos')
def testqos():
    test_count= request.args.get('testcount')
    c_users = int(request.args.get('c'))
    loop = int(request.args.get('l'))
    runQoSTest(iteration_count=test_count,concurrent_users=c_users,loop_times=loop)
    msg = {"status" : "QoS Test Started"}, 200
    return msg

@app.route('/setconfigs')
def setConfigs():
    if 'astra' in request.args:
        config['servers']['API_VULNERBILITY_SERVICE_URL'] = request.args.get('astra')
    ### TODO after setting db try to connect to the correct DB
    if 'db' in request.args:
        config['database']['db_ip'] = request.args.get('db')
    with open ('environment_config.ini','w') as configfile:
        config.write(configfile)
    dttsaSupportServices.clearDB()
    config.read('environment_config.ini')
    return str(config['servers']['API_VULNERBILITY_SERVICE_URL'])

@app.route('/restart')
def restartService():
    os._exit(0)

@app.route('/dttsa_details')
def DTTSAStatus():
    config.read('environment_config.ini')
    return json.dumps({
        'version' : "v7",
        'astra' : str(config['servers']['API_VULNERBILITY_SERVICE_URL']),
        'db' : str(config['database']['db_ip'])
    })

#runSchedulerJobs()

@app.route('/dttsa_start')
def startDTTSA():
    runSchedulerJobs()
    return "Success"

def start_server(args):
    #app.config['test_arg_value'] = args.a
    # runSchedulerJobs()
    app.run(host='0.0.0.0',port=9000,use_reloader=False) #use_reloader = True support hot reloading but scheduler will run twice

def main(args):
    start_server(args)

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    #parser.add_argument('-a')
    #args = parser.parse_args()
    args = ""
    main(args)