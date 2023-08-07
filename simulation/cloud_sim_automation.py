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
import re
from flask_apscheduler import APScheduler
import statistics
import sys
from time import sleep
from apscheduler.schedulers.background import BackgroundScheduler

# Creates a default Background Scheduler
sched = BackgroundScheduler()
# Starts the Scheduled jobs
sched.start()


number_of_simulations = 10

main_server = "34.171.25.121"

us_server = "104.154.17.194"
eu_server = "35.223.233.59"
asia_server = "34.173.139.246"
north_server = "35.239.37.79"
dttsa_port = 9000

sim_prefix = "s"+str(3)

sim_started = False


# app = Flask(__name__)

# scheduler = APScheduler()
# scheduler.init_app(app)

def execute_cloud_sim():
    global sim_started
    sim_started = True
    os.system("python3 cloud_sim.py")

def makeURL(ip,port):
    return "http://"+ip+":"+ str(port)

def saveFiles(sim_id):
    os.system("zip -r ./save/"+sim_id+" ./csv")

def deleteFiles():
    os.system("sudo find ./csv/ -mindepth 1  -delete")

def evaluteSimulation():
    u = makeURL(main_server,dttsa_port)+"/eval"
    r = requests.get(u,verify=False)
    if r.text == "okay":
        print("Sim evaluation completed")
    else:
        print(r.text)

def saveSimulationFiles():
    u = makeURL(main_server,dttsa_port)+"/save"
    r = requests.get(u,verify=False)
    if r.text == "Ok":
        print("Sim csv file save completed")
    else:
        print(r.text)

def cloudSimStart():
    global number_of_simulations
    global sim_started
    if number_of_simulations != 0:
        u = makeURL(main_server,dttsa_port)+"/qosstat"
        r = requests.get(u,verify=False)
        if r.json()['status'] == "Finished":
            print("DTTSA QoS Finished")
            evaluteSimulation()
            saveSimulationFiles()
            saveFiles(sim_prefix+"_"+str(number_of_simulations))
            deleteFiles()
            number_of_simulations = number_of_simulations - 1
            sim_started = False
            stopScheduleJob()
            # number_of_simulations = sim_num
        else:
            print(r.text)
    

def startScheduleJob():
    print("Starts the Scheduled jobs")
    sched.add_job(cloudSimStart,'interval', seconds=300, id='my_job_id')
    

def stopScheduleJob():
    print("Stopping Scheduled jobs ")
    sched.remove_job('my_job_id')
    # sched.shutdown()

# Runs an infinite loop
while number_of_simulations != 0:
    print("Sim Number "+str(number_of_simulations))
    if sim_started == False:
        execute_cloud_sim()
        startScheduleJob()
        sim_started = True
    sleep(300)
