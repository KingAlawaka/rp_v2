#DTTSA dashboard and main services management
from cProfile import run
from crypt import methods
from lib2to3.pytree import type_repr
from re import L
from sched import scheduler
import socket
from urllib import response
from click import password_option
import psycopg2
from flask import Flask, jsonify,render_template,request,url_for,redirect,session
import hashlib
import requests
from sqlalchemy import null
from flask_apscheduler import APScheduler
from API_analysis import APIAnalyser


app = Flask(__name__,template_folder="../Dashboardnew/templates", static_folder="../Dashboardnew/static")
#app.secret_key="DTTSA_KEY"
app.config.from_pyfile('config.py')
API_vulnerbility_service_IP = app.config['API_VULNERBILITY_SERVICE_IP'] #change this to cmd arguments and specify in the dockerfile
scheduler = APScheduler()
scheduler.init_app(app)
hostname = socket.gethostname()
localIP = socket.gethostbyname(hostname)
print(localIP)

#apiAnalyser = APIAnalyser(app.config['DB_IP'],app.config['DB_NAME'],app.config['DB_USER'],app.config['DB_PASSWORD'],API_vulnerbility_service_IP)

#runSchedulerJobs()
'''
Check API vulnerbility finished results for submitted DTs
'''
def runSchedulerJobs():
    print("SchedularJobs Initiated")
    scheduler.add_job(id="checkAPIResults",func=checkAPIResults,trigger="interval",seconds = 30)
    scheduler.start()

def get_db_connection():
    #conn = psycopg2.connect(host='172.17.0.1',database='dttsa_db',user='dev_admin',password='123456')
    conn = psycopg2.connect(host=app.config['DB_IP'],database=app.config['DB_NAME'],user=app.config['DB_USER'],password=app.config['DB_PASSWORD'])
    return conn

def generatePasswordHash(password):
    hashedPassword = hashlib.md5(str(password)).hexdigest()
    return hashedPassword

def checkAPIResults():
    print("API checking")
    #apiAnalyser.checkSubmittedAPI()
    # apiAnalyser.hello()
    # conn = get_db_connection()
    # cur = conn.cursor()
    # cur.execute('select * from api_security_check_tbl where (low_count is NULL and mid_count is null and high_count is null) or (low_count = 0 and mid_count = 0 and high_count = 0) ;')
    # APIs = cur.fetchall()
    # conn.commit()
    # cur.close()
    # conn.close()
    # low_count = 0
    # mid_count = 0
    # high_count =0
    # print(len(APIs))
    # for api in APIs:
    #     print("API ", api[3])
    #     req_url = API_vulnerbility_service_IP + '/alerts/'+api[3]
    #     #req_url = "http://172.17.0.5:8094/alerts/ef42ccc28d90cccfd38929ad5292b1d1"
    #     res = requests.get(req_url)
    #     res.raise_for_status()
    #     apiObj = res.json()
    #     #print(len(apiObj))
    #     try:
    #         print("")
            

    #         for key in apiObj:
    #             #if key == 'impact':
    #             #print(len(key))
    #             for i,a in key.items():
    #                 if i == 'impact':
    #                     if a == 'Low':
    #                         low_count = low_count + 1
    #                     elif a == 'Mid':
    #                         mid_count = mid_count + 1
    #                     else:
    #                         high_count = high_count + 1
                
            

    #         #print(apiObj['impact'])
    #     #print(api[0])
    #     #print(api[1])
    #     #print(api[2])
    #     #print(api[3])
    #     except Exception as e:
    #         print("except:", str(e))
    #         continue
    #     print("low ", low_count)
        
    #     conn = get_db_connection()
    #     cur = conn.cursor()
    #     cur.execute("update api_security_check_tbl set low_count=%s,mid_count=%s,high_count=%s,report=%s,timestamp=current_timestamp at time zone 'UTC' where scan_id = %s;",(low_count,mid_count,high_count,str(apiObj),api[3]))
    #     conn.commit()
    #     cur.close()
    #     conn.close()
    #     low_count = 0
    #     mid_count = 0
    #     high_count =0
   


@app.route("/register",methods=('GET','POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        #password = generatePasswordHash(password)
        org_code = request.form['org_code']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('insert into user_tbl (username,password,org_code) values (%s,%s,%s)',(username,password,org_code))
        conn.commit()
        cur.close()
        conn.close()
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

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('select * from user_tbl where username=%s and org_code=%s;',(username,org_code))
        user = cur.fetchall()
        cur.close()
        conn.close()
        #print(user[0][2])
        #print(password.decode("utf-8"))
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

@app.route('/logout')
def logout():
    session.pop('username',None)
    session.pop('org_code',None)
    return render_template('home/login.html',reg_log="Login")

@app.route('/')
def index():
    #print(app.config['test_arg_value'])
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('select * from public."organization_tbl";')
    orgList = cur.fetchall()
    cur.close()

    cur = conn.cursor()
    cur.execute('select dt_tbl.org_code,dt_tbl.dt_code,dt_tbl.dt_name,sum(api_security_check_tbl.low_count) as low_sum,sum(api_security_check_tbl.mid_count) as mid_sum,sum(api_security_check_tbl.high_count) as high_sum from dt_tbl join api_security_check_tbl on dt_tbl.id = dt_id group by dt_tbl.org_code,dt_tbl.dt_code,dt_tbl.dt_name; ')
    DTs = cur.fetchall()
    cur.close()

    conn.close()
    print(orgList)
    
    res = [
        {
            "id": org[0],
            "org_name":org[1],
            "org_code":org[2],
            "timestamp": org[3]
        } for org in orgList]
    return render_template('home/index.html',segment='index',orgList=orgList, DTs = DTs)

@app.route("/DT",methods=('GET','POST'))
def DT():
    return render_template('home/page-user.html',segment='DT')

@app.route("/config",methods=('GET','POST'))
def trustSecurityConfig():
    return render_template('home/dttsa-config.html',segment='dttsa_config')

def addAPIs(APIs,DT_ID):
    APIList = []
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        for API in APIs:
                #print(API['URL'])
                #DT_ID = "DT_1"
                url = str(API['URL'])
                desc =str(API['Description'])
                type_req =str(API['Type'])
                sam_json = str(API['Sample_json']).strip()
                auth_to = str(API['User_auth_token'])
                #conn = get_db_connection()
                #cur = conn.cursor()
                #cur.execute("insert into API_tbl (DT_ID,URL,description,type,sample_json,user_auth_token ) values (%s,'127.0.0.1/send','test DT server','GET','{message : text}','')",DT_ID)
                cur.execute('insert into API_tbl (DT_ID,URL,description,type,sample_json,user_auth_token ) values (%s,%s,%s,%s,%s,%s) returning id;',(DT_ID,url,desc,type_req,sam_json,auth_to))
                API_ID = cur.fetchall()
                conn.commit()
                tempAPI = [DT_ID,API_ID[0][0],url,sam_json,type_req]
                APIList.append(tempAPI)
                #checkAPIVulnerbilities(DT_ID,API_ID[0][0],url,sam_json,type_req)
                #cur.close()
                #conn.close()
        cur.close()
        conn.close()
        return APIList
    except Exception as e:
        print("error: addAPIs ", str(e))
        return APIList

def addDT(org_code,DT_code,DT_name,DT_description):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('insert into DT_tbl (org_code,DT_code,DT_name,DT_description) values (%s,%s,%s,%s) returning id;',(org_code,DT_code,DT_name,DT_description))
    retValue = cur.fetchall()
    #print(retValue[0][0])
    conn.commit()
    cur.close()
    conn.close()
    try:
        return retValue[0][0]
    except:
        return -1

def addAPISecurityCheck(DT_ID,API_ID,scan_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('insert into api_security_check_tbl (DT_ID,API_ID,scan_id) values (%s,%s,%s);',(DT_ID,API_ID,scan_id))
        conn.commit()
        cur.close()
        conn.close()
    except:
        print("Error: AddAPISecurityCheck")

def checkAPIVulnerbilities(DT_ID,API_ID,url,sample_json,type_req):
    dictToSend = {"appname" : str(DT_ID)+"_"+str(API_ID),"url": url ,"headers": "","body": sample_json,"method": type_req}
    jsonObject = jsonify(dictToSend)
    req_url = API_vulnerbility_service_IP + '/scan/'
    res = requests.post(req_url, json= dictToSend)
    v = res.json()
    if v['status']:
        scan_id = v['status']
        addAPISecurityCheck(DT_ID,API_ID,scan_id)
        print(scan_id)
    #print(res.text)

@app.post("/DTReg")
def DTReg():
    content = request.get_json()
    msg = ""
    try:
        org_code = str(content['org_code'])
        DT_code = str(content['DT_code'])
        DT_name = str(content['DT_name'])
        DT_description = str(content['DT_Description'])
        APIs = content['APIs']
        print(APIs)
        DT_ID = addDT(org_code,DT_code,DT_name,DT_description)
        if DT_ID > 0:
            APIList = addAPIs(APIs,DT_ID)
            for api in APIList:
                checkAPIVulnerbilities(api[0],api[1],api[2],api[3],api[4])
            msg = "sucess"
        else:
            msg = "fail"
        
        '''
        conn = get_db_connection()
        cur = conn.cursor()
        for API in APIs:
            print(API['URL'])
            DT_ID = "DT_1"
            url = str(API['URL'])
            desc =str(API['Description'])
            type_req =str(API['Type'])
            sam_json = str(API['Sample_json'])
            auth_to = str(API['User_auth_token'])
            #conn = get_db_connection()
            #cur = conn.cursor()
            #cur.execute("insert into API_tbl (DT_ID,URL,description,type,sample_json,user_auth_token ) values (%s,'127.0.0.1/send','test DT server','GET','{message : text}','')",DT_ID)
            cur.execute('insert into API_tbl (DT_ID,URL,description,type,sample_json,user_auth_token ) values (%s,%s,%s,%s,%s,%s)',(DT_ID,url,desc,type_req,sam_json,auth_to))
            conn.commit()
            #cur.close()
            #conn.close()
        cur.close()
        conn.close()
        '''
        res = {"status" : msg}
    except Exception as e:
        print(e)
        res = {"status" : "hjk"}
    return jsonify(res)

@app.get("/getorg")
def getvalues():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('select * from public."organization_tbl";')
    orgList = cur.fetchall()
    cur.close()
    conn.close()
    print(orgList)
    
    res = [
        {
            "id": org[0],
            "org_name":org[1],
            "org_code":org[2],
            "timestamp": org[3]
        } for org in orgList]
    '''
    '''
    #return render_template('org.html',orgList=orgList)
    #return render_template('home/index.html',segment='index',orgList=orgList)
   # return {"nessage":"hello"}
    return {"count": len(res), "users" : res}

runSchedulerJobs()

def start_server(args):
    #app.config['test_arg_value'] = args.a
    
    app.run(host='0.0.0.0',port=9000,use_reloader=True)

def main(args):
    start_server(args)

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    #parser.add_argument('-a')
    #args = parser.parse_args()
    args = ""
    main(args)