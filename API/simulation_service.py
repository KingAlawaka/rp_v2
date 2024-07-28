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
import psutil
from datetime import datetime

app = Flask(__name__,template_folder="../Dashboardnew/templates", static_folder="../Dashboardnew/static")
CORS(app)

config = configparser.ConfigParser()
config.read('environment_config.ini')

main_server = "34.29.10.14"
us_server = "34.132.190.108"
db_server = "35.193.34.135"
firefly_server = "34.29.10.14"

dttsa_port = 9000
astra_port = 8094
firefly_port = 5000

num_of_dts_per_location = 5  #max 25
backup_dts_per_location = 2 #max 10
dt_cloud_port_start = 9001
backup_dt_port_start = 9030

dt_start_fail_urls = []
dt_backup_dt_ids = []
dt_server_ips = [us_server]
dt_types = ['n','c','m']

same_type_count = int(int(num_of_dts_per_location) / 3)

@app.route("/startdttsa")
def simStartDTTSA():
    restartDTTSA(main_server)
    time.sleep(20)
    startupDTTSA(main_server)
    
    res = {
        "status": "ok"
    }
    return res

@app.route("/startdts")
def startDTs():
    restartDTs()
    time.sleep(20)
    startDTs()

    res = {
        "status": "ok"
    }
    return res

@app.route("/startbdts")
def startBDTs():
    setBackupDTs()
    
    res = {
        "status": "ok"
    }
    return res

@app.route("/analyze")
def simAnalysis():
    u = makeURL(main_server,dttsa_port)+"/analyze"
    r = requests.get(u,verify=False)
    # if r.json()['status'] == "Evaluation completed, analysis completed":
    #     print("Anlysis Done")
    res = {
        "status": str(r.json()['status'])
    }
    return res

def makeURL(ip,port):
    return "http://"+ip+":"+ str(port)
'''
Not using in current simulation. because clearing DB will restart the DTTSA
'''
def restartDTTSA(server_name):
    print("Restarting DTTSA server")
    url = makeURL(server_name,dttsa_port) + "/restart"
    try:
        res = requests.get(url,verify=False)
        time.sleep(10)
        print("Restarting completed")
    except Exception as e:
        time.sleep(10)
        print("Restarting error completed " + str(e))

def startupDTTSA(server_name):
    try:
        url = makeURL(server_name,dttsa_port)+"/setconfigs?astra="+ makeURL(main_server,astra_port) +"&db="+db_server+"&firefly="+makeURL(firefly_server,firefly_port)
        response = requests.get(url,verify=False)
        if response.text == makeURL(main_server,astra_port):
            print("DTTSA config correctly")
            u = makeURL(server_name,dttsa_port)+"/dttsa_start"
            r = requests.get(u,verify=False)
            if r.text == "Success":
                print("DTTSA started correctly")
            else:
                print(r.text)
    except Exception as e:
        print("startup DTTSA Error: "+ str(e))


def restartDTs():
    print("DT restarting process started")
    # print(arg_value)
    try:
        for l in dt_server_ips:
            for i in range(num_of_dts_per_location):
                try:
                    url = makeURL(l,dt_cloud_port_start+i)+"/restart"
                    res = requests.get(url, verify= False)
                except Exception as e:
                    print("Restart DT loop error: "+ str(e))
    except Exception as e:
        print("Restart DT error: "+ str(e))


def startDTs(set_dt_type=False):
    print("DT configuration started")
    try:
        for l in dt_server_ips:
            dt_type_counter = 0
            location_type_counter = 0
            for i in range(num_of_dts_per_location):
                p = dt_cloud_port_start+i
                temp_url = makeURL(l,p)
                try:
                    url = makeURL(l,p)+"/setup"
                    # dt_types = ['n','m','c']
                    # dt_type = random.choice(dt_types)
                    
                    if set_dt_type:
                        print("dt_id",i+1, " dt_type", dt_types[dt_type_counter])
                        payload = { "url" : makeURL(l,p) , "dttsa_url" : makeURL(main_server,dttsa_port), "dt_type": dt_types[dt_type_counter]}
                    else:
                        # dt_types = ['n','m','c']
                        print("Setting random DT types")
                        dt_type = random.choice(dt_types)
                        payload = { "url" : makeURL(l,p) , "dttsa_url" : makeURL(main_server,dttsa_port),"dt_type": dt_type}
                    x = requests.post(url,json=payload)
                    print(x.text)
                    location_type_counter += 1
                    if location_type_counter == same_type_count:
                        dt_type_counter += 1
                        location_type_counter = 0
                except Exception as e:
                    print("start DTs loop error: "+ str(e))
                    dt_start_fail_urls.append(temp_url)
    except Exception as e:
        print("start DTs error: "+ str(e))


def regBackupLocations(backup_url,dt_id):
    url = makeURL(main_server,dttsa_port) +"/regbackup?backupip="+backup_url+"&dtid="+str(dt_id)
    response = requests.get(url,verify=False)
    print(response.text)

def startQoS():
    url = makeURL(main_server,dttsa_port) + "/testqos?testcount=0"
    response = requests.get(url,verify=False)
    print(response.text)

def startBQoS():
    url = makeURL(main_server,dttsa_port) + "/testbackupservices?testcount=0"
    response = requests.get(url,verify=False)
    print(response.text)

def setBackupDTs():
    try:
        for l in dt_server_ips:
            normal_dt_ids = []
            changing_dt_ids = []
            malicious_dt_ids = []
            not_reg_dts = []
            backups = []
            backup_count = 0
            for i in range(num_of_dts_per_location):
                p = dt_cloud_port_start+i
                temp_url = makeURL(l,p)
                try:
                    url = makeURL(l,p)+"/details"
                    response = requests.get(url,verify=False)
                    dt_type = response.json()['dt_type']
                    dt_id = int(response.json()['DT_ID'])
                    if dt_id != -1:
                        if dt_type == "n":
                            normal_dt_ids.append([url,dt_id])
                        elif dt_type == "c":
                            changing_dt_ids.append([url,dt_id])
                        elif dt_type == "m":
                            malicious_dt_ids.append([url,dt_id])
                    else:
                        not_reg_dts.append(url)
                except Exception as e:
                    print("set backup dts loop error: "+ str(e))
                    dt_start_fail_urls.append(temp_url)
            # print("end of loop")
            for d in normal_dt_ids:
                v = random.randint(1,4)
                if v in (1,2,3):
                    if backup_count != backup_dts_per_location:
                        backups.append([d[0],d[1]])
                        backup_count = backup_count + 1
            for e in changing_dt_ids:
                v = random.randint(1,4)
                if v in (1,3):
                    if backup_count != backup_dts_per_location:
                        backups.append([e[0],e[1]])
                        backup_count = backup_count + 1
            for f in malicious_dt_ids:
                v = random.randint(1,4)
                if v == 3:
                    if backup_count != backup_dts_per_location:
                        backups.append([f[0],f[1]])
                        backup_count = backup_count + 1
            # dt_backup_dt_ids.append([normal_dt_ids,changing_dt_ids,malicious_dt_ids,not_reg_dts])
            # for a in malicious_dt_ids:
            #     print(a[0])
            #     print(a[1])
            print("setting up backup dts for "+ l)
            dt_backup_dt_ids.append(backups)
            print(backup_count)
            for i in range(len(backups)):
                p = backup_dt_port_start+i
                temp_url = makeURL(l,p)
                regBackupLocations(temp_url,backups[i][1])

        print(dt_backup_dt_ids)
    except Exception as e:
        print("set backup DTs error: "+ str(e))

def start_server(args):
    app.run(host='0.0.0.0',port=9002,use_reloader=False)

def main(args):
    start_server(args)

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    #parser.add_argument('-a')
    #args = parser.parse_args()
    args = ""
    main(args)