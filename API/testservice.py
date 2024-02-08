import json
from flask import Flask,jsonify,request,Response
import socket
import random
import requests
from datetime import datetime
import psycopg2
from flask_sock import Sock

app = Flask(__name__)
sock = Sock(app)
app.config.from_pyfile('config.py')

app.config['dttsa_url'] = "http://127.0.0.1:9000"

def get_db_connection():
    #conn = psycopg2.connect(host='172.17.0.1',database='dttsa_db',user='dev_admin',password='123456')
    conn = psycopg2.connect(host=app.config['DB_IP'],database=app.config['DB_NAME'],user=app.config['DB_USER'],password=app.config['DB_PASSWORD'])
    return conn

@app.route("/seturl")
def setUrls():
    dttsa_url = request.args.get('dttsa')
    app.config.update(
        dttsa_url = random.choice(dttsa_url)
    )
    return "ok"


def readJson():
    f = open("../sample_jsons/dttsa_config.json")
    data = json.load(f)
    for i in data['trust categories']:
        print(i["category"])

@sock.route('/ws?namespace=default&ephemeral&autoack&filter.events=blockchain_event_received')
def socketRead(sock):
    print("connected")
    while True:
        data = sock.receive()
        print(data)


@app.route("/return")
def requestChangeReturnFromChain():
    dt_id = request.args.get('dt')
    con_dt_id = request.args.get('con_dt')
    reply = request.args.get('reply')

    url = app.config['dttsa_url'] +"/reqchangereturn?dt="+str(dt_id)+"&con_dt="+str(con_dt_id)+"&reply="+str(reply)
    res = requests.get(url)
    return "ok"

@app.get('/firefly')
def testFireFly():
    dt = request.args.get('dt')
    connectDT = request.args.get('condt')
    rep_type = request.args.get('rep')
    # urls = ['http://127.0.0.1:5109/api/messages/broadcast?ns=default',
    #         'http://127.0.0.1:5209/api/messages/broadcast?ns=default',
    #         'http://127.0.0.1:5309/api/messages/broadcast?ns=default',
    #         'http://127.0.0.1:5409/api/messages/broadcast?ns=default']
    # myobj = {
    # "value": "",
    # "jsonValue": {"DT_ID": dt,"connect": connectDT},
    # "datatypename": "", 
    # "datatypeversion" : "" }

    # x = requests.post(random.choice(urls), json = myobj)
    # print(x.elapsed.total_seconds())
    # print(x.text)
    headers = {
        'accept': 'application/json',
        'Request-Timeout': '2m0s',
        'Content-Type': 'application/json',
    }

    json_data = {
        'idempotencyKey': '',
        'input': {
            '_condt': connectDT,
            '_dt': dt,
            '_reptype': rep_type,
        },
        'key': '',
        'options': {},
    }

    response = requests.post(
        'http://127.0.0.1:5000/api/v1/namespaces/default/apis/DTConnectionChangeV2/invoke/changeConnection',
        headers=headers,
        json=json_data,
    )
    # json_data(response.text)
    retValue = {"response": response.text, "response time": str(response.elapsed.total_seconds())}
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