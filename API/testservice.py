import json
from flask import Flask,jsonify,request,Response
import socket
import random
import requests
from datetime import datetime
import psycopg2

app = Flask(__name__)
app.config.from_pyfile('config.py')

def get_db_connection():
    #conn = psycopg2.connect(host='172.17.0.1',database='dttsa_db',user='dev_admin',password='123456')
    conn = psycopg2.connect(host=app.config['DB_IP'],database=app.config['DB_NAME'],user=app.config['DB_USER'],password=app.config['DB_PASSWORD'])
    return conn



def readJson():
    f = open("../sample_jsons/dttsa_config.json")
    data = json.load(f)
    for i in data['trust categories']:
        print(i["category"])

@app.get('/firefly')
def testFireFly():
    dt = request.args.get('dt')
    connectDT = request.args.get('condt')
    url = 'http://127.0.0.1:5109/api/messages/broadcast?ns=default'
    myobj = {
    "value": "",
    "jsonValue": {"DT_ID": dt,"connect": connectDT},
    "datatypename": "", 
    "datatypeversion" : "" }

    x = requests.post(url, json = myobj)
    print(x.elapsed.total_seconds())
    print(x.text)
    retValue = {"response": str(x.text), "response time": str(x.elapsed.total_seconds())}
    return retValue

@app.get('/test')
def DTregService():
    readJson()
    return {"status":"working"}

@app.get('/getconfig')
def getDTTSAConfig():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('select * from dttsa_evaluation_config_tbl order by id desc limit 1;')
    resultsList = cur.fetchall()
    data = json.loads(str(resultsList[0][1]))
    cur.close()
    conn.close()
    #print(resultsList[0][0])
    for i in data['trust categories']:
        print(i["category"])
    return "resultsList"

@app.get('/setconfig')
def setDTTSAConfig():
    f = open("../sample_jsons/dttsa_config.json")
    data = f.read()
    #print(
    #data = json.load(f)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"insert into  dttsa_evaluation_config_tbl (configuration_json) values ('{data}');")
    conn.commit()
    cur.close()
    conn.close()
    return {"status":"working"}

def start_server():
    app.run(host='0.0.0.0',port=9100)

def main():
    start_server()

if __name__ == '__main__':
    main()