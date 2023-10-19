#QoS check
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
import time
from qos_test import QoSTest

class QoSAnalyzer:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read('environment_config.ini')
        #print(config['database']['DB_IP'])
        self.dbConnection = DBConnection()
    
    def addAPIForQoS(self,DT_ID,API_ID):
        try:
            conn = self.dbConnection.get_db_connection()
            cur = conn.cursor()
            cur.execute('insert into api_qos_tbl (DT_ID,API_ID,test_count) values (%s,%s,0);',(DT_ID,API_ID))
            #cur.execute('insert into api_security_check_tbl (DT_ID,API_ID,scan_id) values (%s,%s,%s);',(DT_ID,API_ID,scan_id))
            conn.commit()
            cur.close()
            conn.close()
        except:
            print("Error: Add API for QoS Error in addAPIForQoS()")
    
    def updateQoSTestCount(self,DT_ID,API_ID):
        try:
            conn = self.dbConnection.get_db_connection()
            cur = conn.cursor()
            cur.execute('update api_qos_tbl set test_count = test_count + 1 where dt_id=%s and api_id =%s and status=1;',(DT_ID,API_ID))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print("Error: qos_analysis.py updateQoSTestCount()")
            print(e)
    
    def addQoSRecords(self,results,test_type):
        try:
            conn = self.dbConnection.get_db_connection()
            cur = conn.cursor()
            cur.execute('insert into api_qos_records_tbl (DT_ID,API_ID,start_time,end_time ,test_duration ,req_per_sec_mean ,tot_req ,tot_tested_time ,tot_pass_tests ,time_per_req_min ,time_per_req_mean ,time_per_req_max ,sum_response_time ,tot_failed_reqs ,tot_exception_reqs,test_type) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);',(results[0],results[1],results[2],results[3],results[4],results[5],results[6],results[7],results[8],results[9],results[10],results[11],results[12],results[13],results[14],test_type))
            #cur.execute('insert into api_security_check_tbl (DT_ID,API_ID,scan_id) values (%s,%s,%s);',(DT_ID,API_ID,scan_id))
            conn.commit()
            cur.close()
            conn.close()
            #print(results)
        except Exception as e:
            print("Error: Add API for QoS Error in addQoSRecords()")
            print(e.message)
            

    def getAPIsForQoSAnalysis(self,test_count):
        try:
            conn = self.dbConnection.get_db_connection()
            cur = conn.cursor()
            cur.execute("select api_tbl.dt_id,api_qos_tbl.api_id,api_tbl.url,api_tbl.type,api_tbl.sample_json,api_tbl.user_auth_token from api_tbl join api_qos_tbl on api_tbl.id = API_ID where api_qos_tbl.test_count = %s and api_tbl.status=1 and api_qos_tbl.status=1;",[test_count])
            #cur.execute('insert into api_security_check_tbl (DT_ID,API_ID,scan_id) values (%s,%s,%s);',(DT_ID,API_ID,scan_id))
            APIs = cur.fetchall()
            cur.close()
            conn.close()
            return APIs
        except Exception as e:
            print("Error: Add API for QoS Error in getAPIsForQoSAnalysis()")
            print(e.message)
    
    def addQoSStatus(self,function_name,status,msg=""):
        try:
            conn = self.dbConnection.get_db_connection()
            cur = conn.cursor()
            cur.execute('insert into dttsa_execution_status_tbl (function_name,execution_status,msg) values (%s,%s,%s);',(function_name,status,str(msg)))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print("error: addDTReports ", str(e))

    # def getQoSLowMidHighCount(self,)
    def getDTAPIsbyPotentialCategory(self,potential_category):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select api_tbl.dt_id,api_tbl.id,api_tbl.url,api_tbl.type,api_tbl.sample_json,api_tbl.user_auth_token from api_tbl join dttsa_qos_staging_tbl on api_tbl.dt_id = dttsa_qos_staging_tbl.dt_id where api_tbl.status=1 and dttsa_qos_staging_tbl.status=1 and dttsa_qos_staging_tbl.category = %s;',(potential_category,))
        records = cur.fetchall()
        cur.close()
        return records
    
    def getDTAPIsbyPreviousDTType(self,iteration_count,dt_type,category):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select distinct api_tbl.dt_id,api_tbl.id,api_tbl.url,api_tbl.type,api_tbl.sample_json,api_tbl.user_auth_token from api_tbl join dttsa_trust_calculations_tbl on api_tbl.dt_id = dttsa_trust_calculations_tbl.dt_id where api_tbl.status=1 and dttsa_trust_calculations_tbl.status=%s and dttsa_trust_calculations_tbl.dt_type_prediction = %s and dttsa_trust_calculations_tbl.category=%s;',(iteration_count,dt_type,category))
        records = cur.fetchall()
        cur.close()
        return records

    
    def QoSTest(self,test_type="i",concurrent_users=5,loop_times=2,test_time=3600,stats_interval=5,ramp_up=0,iteration_count=0):
        if test_type == "i":
            #initial logic
            APIs = self.getAPIsForQoSAnalysis(0)
            qosTest = QoSTest(concurrent_users,loop_times,test_time,stats_interval,ramp_up)
            for api in APIs:
                # req_type = api[3]
                # url = api[2]
                # if url == "http://127.0.0.1:9100/sendpost/":
                #     req_type = "GET"
                self.addQoSStatus("QoS_"+test_type,"Running","For API "+str(api))
                #self.addQoSStatus("QoS","Finished")
                results = qosTest.startTest(api[3],api[2],api[4]) #index 9 time per req mean
                results.insert(0,api[1]) #adding DT ID and API ID to the results and pass it
                results.insert(0,api[0])
                self.addQoSRecords(results,test_type)
                self.updateQoSTestCount(api[0],api[1])
                print(results)
        elif test_type == "n":
            APIs = self.getDTAPIsbyPreviousDTType(iteration_count,test_type,"DTTSA QoS")
            print("api count for qos n:"+str(len(APIs))+ " "+str(iteration_count))
            #time.sleep(40)
            qosTest = QoSTest(concurrent_users,loop_times,test_time,stats_interval,ramp_up)
            for api in APIs:
                # req_type = api[3]
                # url = api[2]
                # if url == "http://127.0.0.1:9100/sendpost/":
                #     req_type = "GET"
                self.addQoSStatus("QoS_"+test_type,"Running","For API "+str(api))
                #self.addQoSStatus("QoS","Finished")
                results = qosTest.startTest(api[3],api[2],api[4])
                results.insert(0,api[1])
                results.insert(0,api[0])
                self.addQoSRecords(results,test_type)
                self.updateQoSTestCount(api[0],api[1])
                print(results)
        elif test_type == "c":
            APIs = self.getDTAPIsbyPreviousDTType(iteration_count,test_type,"DTTSA QoS")
            print("api count for qos c:"+str(len(APIs))+ " "+str(iteration_count))
            #time.sleep(40)
            qosTest = QoSTest(concurrent_users,loop_times,test_time,stats_interval,ramp_up)
            for api in APIs:
                # req_type = api[3]
                # url = api[2]
                # if url == "http://127.0.0.1:9100/sendpost/":
                #     req_type = "GET"
                self.addQoSStatus("QoS_"+test_type,"Running","For API "+str(api))
                #self.addQoSStatus("QoS","Finished")
                results = qosTest.startTest(api[3],api[2],api[4])
                results.insert(0,api[1])
                results.insert(0,api[0])
                self.addQoSRecords(results,test_type)
                self.updateQoSTestCount(api[0],api[1])
                print(results)
        elif test_type == "m":
            APIs = self.getDTAPIsbyPreviousDTType(iteration_count,test_type,"DTTSA QoS")
            print("api count for qos m:"+str(len(APIs))+ " "+str(iteration_count))
            #time.sleep(40)
            qosTest = QoSTest(concurrent_users,loop_times,test_time,stats_interval,ramp_up)
            for api in APIs:
                # req_type = api[3]
                # url = api[2]
                # if url == "http://127.0.0.1:9100/sendpost/":
                #     req_type = "GET"
                self.addQoSStatus("QoS_"+test_type,"Running","For API "+str(api))
                #self.addQoSStatus("QoS","Finished")
                results = qosTest.startTest(api[3],api[2],api[4])
                results.insert(0,api[1])
                results.insert(0,api[0])
                self.addQoSRecords(results,test_type)
                self.updateQoSTestCount(api[0],api[1])
                print(results)
        else:
            APIs = self.getDTAPIsbyPotentialCategory(test_type)
            #time.sleep(40)
            qosTest = QoSTest(concurrent_users,loop_times,test_time,stats_interval,ramp_up)
            for api in APIs:
                # req_type = api[3]
                # url = api[2]
                # if url == "http://127.0.0.1:9100/sendpost/":
                #     req_type = "GET"
                self.addQoSStatus("QoS_"+test_type,"Running","For API "+str(api))
                #self.addQoSStatus("QoS","Finished")
                results = qosTest.startTest(api[3],api[2],api[4])
                results.insert(0,api[1])
                results.insert(0,api[0])
                self.addQoSRecords(results,test_type)
                self.updateQoSTestCount(api[0],api[1])
                print(results)
        #ßprint(APIs)
        self.addQoSStatus("QoS_"+test_type,"Finished",test_type)
        print("Thread finished")

    
    def backupQoSTest(self,request_type,url,sample_json):
        qosTest = QoSTest()
        results = qosTest.startTest(request_type,url,sample_json)
        return results
        
            