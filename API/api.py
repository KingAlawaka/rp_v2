from crypt import methods
from email.policy import default
from time import time
from flask import Flask,jsonify,request,render_template,send_from_directory,g
import os
import requests
import hashlib
from pymongo import MongoClient
from flask_sqlalchemy import SQLAlchemy
from models import User,DT
from dbconnection import db_connect
import time
import json

app = Flask(__name__,template_folder="../Dashboard/templates", static_folder="../Dashboard/static")
app.config.from_pyfile('config.py')
db = SQLAlchemy(app)


def generate_hash():
    scanid = hashlib.md5(str(time.time())).hexdigest()
    return scanid

@app.before_request
def before_request():
    g.request_start_time = time.time()
    g.request_time = lambda: "%5fs" % (time.time()-g.request_start_time)

#@app.get("/")
#def index():
#    return "hello world"

############### Dashboard ####################

@app.route('/',defaults={'page': 'scan.html'})
@app.route('/<page>')
def view_dashboard(page):
    return render_template('{}'.format(page))

###################################

@app.get("/hello")
def say_hello():
    userObj = User("Test name",12)
    db.session.add(userObj)
    db.session.commit()
    return jsonify({"message": "hello jason"})

@app.get("/read")
def getvalues():
    userList = User.query.all()
    res = [
        {
            "id":user.id,
            "name":user.name,
            "age":user.age
        } for user in userList]
    #return userList
    #print(userList)
    #for u in userList:
    #   print(u)
    return {"count": len(res), "users" : res}

@app.get("/testtbl")
def readTestTbl():
    userList = DT.query.all()
    res = [
        {
            "id":user.id,
            "name":user.name,
            "age":user.age
        } for user in userList]
    #return userList
    #print(userList)
    #for u in userList:
    #   print(u)
    return {"count": len(res), "users" : res}


@app.route('/scan/',methods=['POST'])
def start_scan():
    #scanid = generate_hash()
    scanid = "test scan id"
    content = request.get_json()
    try:
        name = content['appname']
        url = str(content['url'])
        headers = str(content['headers'])
        body = str(content['body'])
        method = content['method']
        api = "Y"
        #scan_status = scan_single_api(url, method, headers, body, api, scanid)
        if name == "test":
            # Success
            msg = {"status" : scanid}
        else:
            msg = {"status" : "Failed line 38"}
    
    except Exception as e:
        msg = {"Error" : str(e)} 
    
    return jsonify(msg)

@app.post("/send/")
def sendmessage():
    content = request.get_json()
    try:
        message = content['msg']
        sender = content['sender']
        msg = {"status" : "sucess", "data" : f"sample message {message} sender of this message {sender}"}
    except:
        msg = {"status": "Failed"}
    return jsonify(msg)

@app.get("/sendmsg/")
def sendpostmessage():
    dictToSend = {"msg" : "test message" , "sender" : "test sender"}
    res = requests.post("http://10.138.0.2:9000/send/",json=dictToSend)
    dictfromserver = res.json()
    return jsonify(dictfromserver)

@app.get('/call/')
def callOtherServer():
    res = requests.get('http://172.17.0.3:8094/scan/scanids/')
    return jsonify(res.json())

@app.get("/submit/")
def submitScan():
    dictToSend = {"appname" : "test","url": "http://10.138.0.2:9000/send/","headers": "","body": "","method":"GET"}
    jsonObject = jsonify(dictToSend)
    res = requests.post('http://172.17.0.3:8094/scan/', json= dictToSend)
    print(res.text)
    return jsonify(res.json())

def start_server():
    app.run(host='0.0.0.0',port=9000)

def main():
    start_server()

if __name__ == '__main__':
    main()