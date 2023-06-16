#API vulnerbility check
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
from dbconnection import DBConnection
import configparser

class APIAnalyzer:
    def __init__(self):
        
        
        #print(config['database']['DB_IP'])
        self.dbConnection = DBConnection()

    # def get_db_connection(self):
    #     conn = psycopg2.connect(host=self.DB_IP,database=self.DB_name,user=self.DB_user,password=self.DB_password)
    #     return conn
    
    def addAPIExecutionStatus(self,function_name,status,msg=""):
        try:
            conn = self.dbConnection.get_db_connection()
            cur = conn.cursor()
            cur.execute('insert into dttsa_execution_status_tbl (function_name,execution_status,msg) values (%s,%s,%s);',(function_name,status,str(msg)))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print("error: addAPIExecutionStatus ", str(e))

    def checkSubmittedAPI(self):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select * from api_security_check_tbl where (low_count is NULL and mid_count is null and high_count is null) or (low_count = 0 and mid_count = 0 and high_count = 0) ;')
        APIs = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        low_count = 0
        mid_count = 0
        high_count =0
        self.addAPIExecutionStatus("API","Running","APis remaning"+str(len(APIs)))
        config = configparser.ConfigParser()
        config.read('environment_config.ini')
        API_vulnerbility_service_url = config['servers']['API_VULNERBILITY_SERVICE_URL']
        for api in APIs:
            #TODO uncomment this print
            print("API ", api[3])
            req_url = API_vulnerbility_service_url + '/alerts/'+api[3]
            res = requests.get(req_url)
            res.raise_for_status()
            apiObj = res.json()
            try:
                for key in apiObj:
                    for i,a in key.items():
                        if i == 'impact':
                            if a == 'Low':
                                low_count = low_count + 1
                            elif a == 'Mid':
                                mid_count = mid_count + 1
                            else:
                                high_count = high_count + 1
            except Exception as e:
                print("except:", str(e))
                continue
            #print("low ", low_count)
            
            conn = self.dbConnection.get_db_connection()
            cur = conn.cursor()
            cur.execute("update api_security_check_tbl set low_count=%s,mid_count=%s,high_count=%s,report=%s,timestamp=current_timestamp at time zone 'UTC' where scan_id = %s;",(low_count,mid_count,high_count,str(apiObj),api[3]))
            conn.commit()
            cur.close()
            conn.close()
            low_count = 0
            mid_count = 0
            high_count =0
        self.addAPIExecutionStatus("API","Finished","")
        print("API check finished")

    def addAPISecurityCheck(self,DT_ID,API_ID,scan_id):
        try:
            conn = self.dbConnection.get_db_connection()
            cur = conn.cursor()
            cur.execute('insert into api_security_check_tbl (DT_ID,API_ID,scan_id,low_count,mid_count,high_count) values (%s,%s,%s,0,0,0);',(DT_ID,API_ID,scan_id))
            conn.commit()
            cur.close()
            conn.close()
        except:
            print("Error: AddAPISecurityCheck")
    
    def checkAPIVulnerbilities(self,DT_ID,API_ID,url,sample_json,type_req):
        dictToSend = {"appname" : str(DT_ID)+"_"+str(API_ID),"url": url ,"headers": "","body": sample_json,"method": type_req,"auth_header": "","auth_url": ""}
        jsonObject = jsonify(dictToSend)
        config = configparser.ConfigParser()
        config.read('environment_config.ini')
        API_vulnerbility_service_url = config['servers']['API_VULNERBILITY_SERVICE_URL']
        req_url = API_vulnerbility_service_url+ '/scan/'
        res = requests.post(req_url, json= dictToSend)
        v = res.json()
        print(dictToSend)
        if v['status']:
            scan_id = v['status']
            self.addAPISecurityCheck(DT_ID,API_ID,scan_id) #save to api_security_check_tbl
            print(scan_id)

