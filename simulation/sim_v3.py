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


# print("current docker ps")
# print(client.containers.list())

# print("docker images")
# print(client.images.list())
# imageList = client.images.list()

dttsa_img = 'kingalawaka/dttsa:v1'
dt_img = 'kingalawaka/dt-29-5-23-v3'
dt_backup = 'kingalawaka/backup-dt-17-06-23'

dttsa = client.containers.run(dttsa_img,remove=True, detach=True,name='dttsa',volumes=['/var/folders/csv:/app/API/csv'])
dttsa_obj = client.containers.get("dttsa")
dttsa_ip = dttsa_obj.attrs['NetworkSettings']['IPAddress']
# dttsa_ip = dttsa_obj.attrs.get("NetworkSettings", {})#.get("Networks", {}).get("IPAddress")
print(dttsa_obj.name)
print("DTTSA IP"+ str(dttsa_ip) )

num_of_dts = 5
dts_doc_objs = []
backup_dts_doc_objs = []
dt_port = 9100
sim_completed = False
# dt_type = "c"
iteration_count = 0
qos_started = False
dt_type_original = []

# random_seed = datetime.now().timestamp()
random_seed = 123456789
random.seed(random_seed)

for i in range(1,num_of_dts+1):
    dt_types = ['n','m','c']
    dt_type = random.choice(dt_types)
    # dt_type = 'n'
    env_var_list = ["dt_type="+dt_type,"CDT_goal=min","num_dts=12","num_iterations=15","dttsa_IP="+str(dttsa_ip),"rand_seed="+str(random_seed)]
    client.containers.run(dt_img,remove=True,detach=True,name='dt_'+str(i),environment=env_var_list,volumes=['/var/folders/csv:/app/csv'])
    dts_doc_objs.append(client.containers.get("dt_"+str(i)))
    dt_type_original.append(dt_type)

print(dts_doc_objs)
print(dt_type_original)

def runDTBackupDoc(id,dt_type):
    env_var_list = ["dt_type="+dt_type,"CDT_goal=min","num_dts=12","num_iterations=15","dttsa_IP="+str(dttsa_ip)]
    client.containers.run(dt_backup,remove=True,detach=True,name='dt_backup_'+str(id),environment=env_var_list,volumes=['/var/folders/csv:/app/csv'])
    return client.containers.get("dt_backup_"+str(id))
    backup_dts_doc_objs.append(client.containers.get("dt_backup"+str(id)))

def regBackupLocations(backup_ip,dt_id):
    url = "http://"+dttsa_ip+":9000/regbackup?backupip=http://"+backup_ip+":"+str(dt_port)+"&dtid="+str(dt_id)
    response = requests.get(url,verify=False)

def settingBackupDTs():
    normal_limit = 75
    changing = 50
    malicious = 25
    count = 1
    for dt in dt_type_original:
        v = random.randint(1,100)
        
        if dt == 'n':
            if v >= 1 and v<=normal_limit:
                obj = runDTBackupDoc(count,dt)
                regBackupLocations(obj.attrs['NetworkSettings']['IPAddress'],count)
                backup_dts_doc_objs.append(obj)
        elif dt == 'c':
            if v >= 1 and v<=changing:
                obj = runDTBackupDoc(count,dt)
                regBackupLocations(obj.attrs['NetworkSettings']['IPAddress'],count)
                backup_dts_doc_objs.append(obj)
        else:
            if v >= 1 and v<=malicious:
                obj = runDTBackupDoc(count,dt)
                regBackupLocations(obj.attrs['NetworkSettings']['IPAddress'],count)
                backup_dts_doc_objs.append(obj)
        count = count + 1
    print(len(backup_dts_doc_objs))

def simulation():
    print("Checking DTs")
    sim_completed = True
    # iteration_count = iteration_count + 1
    # print(iteration_count)

    dt_iteration_count = 0
    
    for dt_obj in dts_doc_objs:
        ip_address = dt_obj.attrs['NetworkSettings']['IPAddress']
        url = "http://"+ip_address+":"+str(dt_port)+"/status"
        response = requests.get(url,verify=False)
        data = json.loads(response.text)
        #print(data['status'])
        if data['status'] == False:
            sim_completed = False
        dt_iteration_count = int(data['iteration_count'])

    qos_test_url = "http://"+dttsa_ip+":9000/qosstat"
    response = requests.get(qos_test_url,verify=False)
    qos_test_status = json.loads(response.text)['status']

    backup_qos_test_url = "http://"+dttsa_ip+":9000/bqosstat"
    response = requests.get(backup_qos_test_url,verify=False)
    backup_qos_test_status = json.loads(response.text)['status']

    
    if qos_test_status == "None" and dt_iteration_count > 5:
        print("QoS starting")
        url =  "http://"+dttsa_ip+":9000/testqos?testcount=0"
        response = requests.get(url,verify=False)
        print("Reg Backups")
        settingBackupDTs()

    if backup_qos_test_status =="None" and dt_iteration_count > 8:
        print("Backup QoS starting")
        url =  "http://"+dttsa_ip+":9000/testbackupservices?testcount=0"
        response = requests.get(url,verify=False)
    

    if sim_completed and qos_test_status == "Finished" and backup_qos_test_status == "Finished":
        print("Sim completed")
        # ip_address = dttsa_obj.attrs['NetworkSettings']['IPAddress']
        url = "http://"+dttsa_ip+":9000/eval"
        response = requests.get(url,verify=False)
        print(response.text)

        url = "http://"+dttsa_ip+":9000/dependgraph"
        response = requests.get(url,verify=False)
        print(response.text)

        url = "http://"+dttsa_ip+":9000/save"
        response = requests.get(url,verify=False)
        print(response.text)
        scheduler.remove_job("simulation")
        et = time.time()
        elapsed_time = et-st
        print('Execution time:', time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))

scheduler = BackgroundScheduler()
scheduler.add_job(id="simulation",func=simulation, trigger="interval", seconds=30,)
scheduler.start()
print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

try:
        # This is here to simulate application activity (which keeps the main thread alive).
    while True:
        time.sleep(2)
except (KeyboardInterrupt, SystemExit):
        # Not strictly necessary if daemonic mode is enabled but should be done if possible
    print('Stopping simulation...')
    scheduler.shutdown()
    # dttsa_obj.stop()
    # for dt_obj in dts_doc_objs:
    #     dt_obj.stop()
    
    # for dt_obj in backup_dts_doc_objs:
    #     dt_obj.stop()
    
# dt1 = client.containers.run('dt-26-11',remove=True,detach=True,name='dt1',environment=env_var_list,volumes=['/var/folders/csv:/app/csv'],command="-port 9100 -db data.db")
# dt2 = client.containers.run('dt-26-11',remove=True,detach=True,name='dt2',environment=env_var_list,volumes=['/var/folders/csv:/app/csv'],command="-port 9100 -db data.db")
#dt3 = client.containers.run('dt-26',remove=True,detach=True,name='dt3',environment=env_var_list,volumes=['/var/folders/csv:/app/csv'],command="-port 9100 -db data.db")
#dt1 = client.containers.run('dtimage',remove=True, detach=True,name='dt1')
#dt1 = client.containers.run('dtnew',remove=True, detach=True,name='dt1',environment=["test_val=wada_huththo","test_val2=wade hari"])
#dt2 = client.containers.run('digitaltwinimage',remove=True, detach=True,name='dt2')
#dt3 = client.containers.run('digitaltwinimage',remove=True, detach=True,name='dt3')

# dt1_obj=client.containers.get("dt1")
# dt2_obj=client.containers.get("dt2")
#dt3_obj=client.containers.get("dt3")


# print("DT1 IP"+ dt1_obj.attrs['NetworkSettings']['IPAddress'])
#print("DT2 IP"+ dt2_obj.attrs['NetworkSettings']['IPAddress'])
#print("DT3 IP"+ dt3_obj.attrs['NetworkSettings']['IPAddress'])


#dt1IP = dttsa_obj.attrs['NetworkSettings']['IPAddress']
# simulation_over = False
# while(simulation_over == False):
#     val = input("press c to stop")
#     if val == 'c':
#         print('Stopping simulation...')
#         dttsa_obj.stop()
#         for dt_obj in dts_doc_objs:
#             dt_obj.stop()
#         simulation_over = True



# url = "http://"+dt1IP+":9100/details"
# print(url)
# sleep(5)
# response = ''
# while response == '':
#     try:
#         response = requests.get(url,verify=False)
#         print(response.json())
#         #break
#     except Exception as e:
#         print("exception:", str(e))
#         sleep(5)
#         continue
# print("Out")
# dt1obj.stop()
# client.containers.prune()
