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

main_server = "104.197.47.71"
main_server2 = "104.197.47.71"

us_server = "34.71.131.44"
eu_server = "35.192.111.188"
asia_server = "34.29.65.167"
north_server = "34.122.181.93"

dttsa_port = 9000
astra_port = 8094
dt_port = 9100
dt_cloud_port_start = 9001
backup_dt_port_start = 9030
num_of_dts_per_location = 25  #max 25
backup_dts_per_location = 10 #max 10

dt_server_ips = [us_server]#,eu_server,asia_server,north_server]
dt_start_fail_urls = []
dt_backup_dt_ids = [] # [[per location ids], [per location ids]]

random.seed(123456789)

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
        url = makeURL(server_name,dttsa_port)+"/setconfigs?astra="+ makeURL(main_server,astra_port) +"&db="+main_server
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
                    # dt_types = ['n','m','c']
                    # dt_type = random.choice(dt_types)
                    if l == asia_server:
                        payload = { "url" : makeURL(l,p) , "dttsa_url" : makeURL(main_server2,dttsa_port) }
                    else:
                        payload = { "url" : makeURL(l,p) , "dttsa_url" : makeURL(main_server,dttsa_port)}
                    x = requests.post(url,json=payload)
                    print(x.text)
                except Exception as e:
                    print("start DTs loop error: "+ str(e))
                    dt_start_fail_urls.append(temp_url)
    except Exception as e:
        print("start DTs error: "+ str(e))

def regBackupLocations(backup_url,dt_id):
    if "asia_server" in backup_url:
        url = makeURL(main_server2,dttsa_port) +"/regbackup?backupip="+backup_url+"&dtid="+str(dt_id)
    else:
        url = makeURL(main_server,dttsa_port) +"/regbackup?backupip="+backup_url+"&dtid="+str(dt_id)
    response = requests.get(url,verify=False)
    print(response.text)

def startQoS():
    url = makeURL(main_server,dttsa_port) + "/testqos?testcount=0"
    response = requests.get(url,verify=False)
    print(response.text)

    url = makeURL(main_server2,dttsa_port) + "/testqos?testcount=0"
    response = requests.get(url,verify=False)
    print(response.text)

def startBQoS():
    url = makeURL(main_server,dttsa_port) + "/testbackupservices?testcount=0"
    response = requests.get(url,verify=False)
    print(response.text)

    url = makeURL(main_server2,dttsa_port) + "/testbackupservices?testcount=0"
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

def main():
    restartDTTSA(main_server)
    # restartDTTSA(main_server2)
    time.sleep(20)
    startupDTTSA(main_server)
    # startupDTTSA(main_server2)
    restartDTs()
    time.sleep(60)
    startDTs()
    print(dt_start_fail_urls)
    time.sleep(20)
    setBackupDTs()
    time.sleep(10)
    startBQoS()
    time.sleep(10)
    startQoS()
main()

