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
from flask import Flask, jsonify,render_template,request,url_for,redirect,session,Response,send_file
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
app.config['iteration_count'] = 0
app.config['analysis_started'] = False

'''
Check API vulnerbility finished results for submitted DTs
'''
def runSchedulerJobs():
    print("SchedularJobs Initiated")
    scheduler.add_job(id="checkAPIResults", replace_existing=True, func=checkAPIResults,trigger="interval",seconds = 30)
    scheduler.start()

def generatePasswordHash(password):
    hashedPassword = hashlib.md5(str(password)).hexdigest()
    return hashedPassword

def checkAPIResults():
    print("API checking")
    dttsaSupportServices.recordExecutionStatus("API","Started")
    apiAnalyzer.checkSubmittedAPI()

    # QoSThreadCreated = False
    # for thread in threading.enumerate():
    #     if thread.name == "QoS":
    #         QoSThreadCreated = True
    
    # if not QoSThreadCreated:
    #     qosThread = threading.Thread(target=qosAnalyzer.QoSTest,args=(dRecieved,),name="QoS")
    #     qosThread.daemon = True
    #     qosThread.start()
    #     print("QoS analysis started")

def runQoSTest(test_count=0):
    QoSThreadCreated = False
    for thread in threading.enumerate():
        if thread.name == "QoS":
            QoSThreadCreated = True
    
    if not QoSThreadCreated:
        qosThread = threading.Thread(target=qosAnalyzer.QoSTest,args=(test_count,),name="QoS")
        qosThread.daemon = True
        qosThread.start()
        print("QoS analysis started")
        dttsaSupportServices.recordExecutionStatus("QoS","Started",test_count)

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
    trust_scores = dttsaSupportServices.getTrustCalculations()
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
    records = dttsaSupportServices.getDTDependencies()
    save_loc = "csv/Graph.png"
    
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

    #for csv folder
    if os.path.isfile(save_loc):
        os.remove(save_loc)
    plt.savefig(save_loc, format="PNG")
    plt.clf()

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
            runQoSTest(int(app.config['iteration_count']))
            runBackupQoSTest(int(app.config['iteration_count']))
            msg = "Analysis started"
        else:
            ret_value1 = dttsaSupportServices.qosExecutionStatus()
            ret_value2 = dttsaSupportServices.backupQoSExecutionStatus()
            if ret_value1 == "Finished" and ret_value2 == "Finished":
                evaluation()
                app.config.update(
                    analysis_started = False
                )
                msg = "Evaluation completed, analysis completed"
            elif ret_value1== "Started" or ret_value2== "Started":
                msg = "Analysis Ongoin"
            else:
                msg = "Analysis not started"
    else:
        msg = "No DTs or submitted values"

    return {"status":str(msg)},200


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
                elif val >= qos_mid and val <= qos_high:
                    mid_count = mid_count+1
                else:
                    high_count = high_count +1
            
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
                elif val >= value_mid and val <= value_high:
                    mid_count = mid_count+1
                else:
                    high_count = high_count +1
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
        for r in records:
            res.append(r[1])
        print(res)
        predicted_type = dtTypePredictor(res)
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

        
@app.route('/logout')
def logout():
    session.pop('username',None)
    session.pop('org_code',None)
    return render_template('home/login.html',reg_log="Login")

@app.route('/')
def index():
    # evaluation()
    generateDependecyGraph()
    trust_score = dttsaSupportServices.getTrustCalculations()
    te = ""
    orgList = dttsaSupportServices.getOrgList()
    DTs = dttsaSupportServices.getDTs()
    qos_data = dttsaSupportServices.getQoSdata()
    trust_calculation_records = dttsaSupportServices.getTrustCalculationsRecords()


    return render_template('home/index.html',segment='index',orgList=orgList, DTs = DTs,qos_data=qos_data,trust_score=trust_score,te=te,trust_calculation_records=trust_calculation_records)

@app.post("/report")
def submitDTReports():
    content = request.get_json()
    msg = ""
    try:
        dt_id = str(content['dt_id'])
        report = content['report']
        dt_type = str(content['dt_type'])
        dttsaSupportServices.addDTType(dt_id,dt_type)
        dttsaSupportServices.addDTReports(dt_id,report)
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

@app.get("/getapis/")
def getDTAPIs():
    DT_ID  = request.args.get('dt_id'),
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
    runQoSTest(test_count)
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