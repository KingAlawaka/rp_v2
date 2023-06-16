import docker
import requests
from time import sleep
from datetime import datetime
import time
import os
import json
import random

from apscheduler.schedulers.background import BackgroundScheduler

st = time.time()
client = docker.from_env()

main_server = "35.224.102.253"

us_server = "35.226.134.9"
eu_server = "35.187.0.95"
asia_server = "35.201.166.187"
north_server = "34.152.51.225"

dttsa_port = 9000
astra_port = 8094
dt_port = 9100
dt_cloud_port_start = 9001
num_of_dts_per_location = 20

dt_server_ips = [us_server,eu_server,asia_server,north_server]
dt_start_fail_urls = []

def makeURL(ip,port):
    return "http://"+ip+":"+ str(port)
'''
Not using in current simulation. because clearing DB will restart the DTTSA
'''
def restartDTTSA():
    print("Restarting DTTSA server")
    url = makeURL(main_server,dttsa_port) + "/restart"
    try:
        res = requests.get(url,verify=False)
        time.sleep(10)
        print("Restarting completed")
    except Exception as e:
        time.sleep(10)
        print("Restarting error completed " + str(e))

def startupDTTSA():
    try:
        url = makeURL(main_server,dttsa_port)+"/setconfigs?astra="+ makeURL(main_server,astra_port) +"&db="+main_server
        response = requests.get(url,verify=False)
        if response.text == makeURL(main_server,astra_port):
            print("DTTSA config correctly")
            u = makeURL(main_server,dttsa_port)+"/dttsa_start"
            r = requests.get(u,verify=False)
            if r.text == "Success":
                print("DTTSA started correctly")
            else:
                print(r.text)
    except Exception as e:
        print("startup DTTSA Error: "+ str(e))


def restartDTs():
    print("DT restarting process started")
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


def startDTs():
    print("DT configuration started")
    try:
        for l in dt_server_ips:
            for i in range(num_of_dts_per_location):
                p = dt_cloud_port_start+i
                temp_url = makeURL(l,p)
                try:
                    url = makeURL(l,p)+"/setup"
                    payload = { "url" : makeURL(l,p) , "dttsa_url" : makeURL(main_server,dttsa_port) }
                    x = requests.post(url,json=payload)
                    print(x.text)
                except Exception as e:
                    print("start DTs loop error: "+ str(e))
                    dt_start_fail_urls.append(temp_url)
    except Exception as e:
        print("start DTs error: "+ str(e))

def main():
    restartDTTSA()
    time.sleep(20)
    startupDTTSA()
    restartDTs()
    time.sleep(60)
    startDTs()
    print(dt_start_fail_urls)

main()

