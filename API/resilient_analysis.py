#DT resilience analysis
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
import re
from qos_analysis import QoSAnalyzer

class ResilienceAnalyzer:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read('environment_config.ini')
        #print(config['database']['DB_IP'])
        self.dbConnection = DBConnection()
    
    def addBackupServiceLocations(self,DT_ID,IP):
        try:
            conn = self.dbConnection.get_db_connection()
            cur = conn.cursor()
            cur.execute('insert into backup_service_locations_tbl (DT_ID,IP) values (%s,%s);',(DT_ID,IP))
            conn.commit()
            cur.close()
            conn.close()
            return "True"
        except Exception as e:
            print("Error: addBackupServiceLocations ", str(e))

    def getBackupServiceLocations(self,DT_ID):
        try:
            conn = self.dbConnection.get_db_connection()
            cur = conn.cursor()
            cur.execute('select ip from backup_service_locations_tbl where dt_id=%s and status = 1;',(DT_ID))
            BackupServiceLocations = cur.fetchall()
            conn.commit()
            cur.close()
            conn.close()
            return BackupServiceLocations
        except Exception as e:
            print("Error: getBackupServiceLocations ", str(e))
    
    def createBackupURL(self,url,backup_IP):
        substr1 = re.split("//",url)
        substr2 = re.split("/",substr1[1])
        backup_url = backup_IP + "/" + substr2[1]
        return backup_url
    
    def getBackupServicesToCheck(self,test_count):
        try:
            conn = self.dbConnection.get_db_connection()
            cur = conn.cursor()
            cur.execute('select distinct api_tbl.id as api_id, api_tbl.dt_id, backup_service_locations_tbl.ip as backup_ip,api_tbl.url,api_tbl.type,api_tbl.sample_json,api_tbl.user_auth_token from backup_service_locations_tbl inner join api_qos_tbl on api_qos_tbl.dt_id = backup_service_locations_tbl.dt_id inner join api_tbl on api_tbl.dt_id = api_qos_tbl.dt_id where api_qos_tbl.test_count=%s and backup_service_locations_tbl.status = 1 and api_qos_tbl.status = 1 and api_tbl.status = 1 order by api_tbl.id;',(str(test_count)))
            BackupServiceAPIs = cur.fetchall()
            conn.commit()
            cur.close()
            conn.close()
            return BackupServiceAPIs
        except Exception as e:
            print("Error: getBackupServicesToCheck ", str(e))
    
    def addBackupQoSRecords(self,results):
        try:
            conn = self.dbConnection.get_db_connection()
            cur = conn.cursor()
            cur.execute('insert into backup_qos_records_tbl (DT_ID,API_ID,start_time,end_time ,test_duration ,req_per_sec_mean ,tot_req ,tot_tested_time ,tot_pass_tests ,time_per_req_min ,time_per_req_mean ,time_per_req_max ,sum_response_time ,tot_failed_reqs ,tot_exception_reqs) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);',(results[0],results[1],results[2],results[3],results[4],results[5],results[6],results[7],results[8],results[9],results[10],results[11],results[12],results[13],results[14]))
            #cur.execute('insert into api_security_check_tbl (DT_ID,API_ID,scan_id) values (%s,%s,%s);',(DT_ID,API_ID,scan_id))
            conn.commit()
            cur.close()
            conn.close()
            #print(results)
        except Exception as e:
            print("Error: Add API for QoS Error in addBackupQoSRecords()")
            print(e.message)
    
    def addBackupAPIForQoS(self,DT_ID,API_ID):
        try:
            conn = self.dbConnection.get_db_connection()
            cur = conn.cursor()
            cur.execute('insert into backup_qos_tbl (DT_ID,API_ID,test_count) values (%s,%s,0);',(DT_ID,API_ID))
            #cur.execute('insert into api_security_check_tbl (DT_ID,API_ID,scan_id) values (%s,%s,%s);',(DT_ID,API_ID,scan_id))
            conn.commit()
            cur.close()
            conn.close()
        except:
            print("Error: Add API for QoS Error in addAPIForQoS()")
    
    def updateBackupQoSTestCount(self,DT_ID,API_ID):
        try:
            conn = self.dbConnection.get_db_connection()
            cur = conn.cursor()
            cur.execute('update backup_qos_tbl set test_count = test_count + 1 where dt_id=%s and api_id =%s and status=1;',(DT_ID,API_ID))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print("Error: qos_analysis.py updateBackupQoSTestCount()")
            print(e)

    def addBackupQoSStatus(self,function_name,status,msg=""):
        try:
            conn = self.dbConnection.get_db_connection()
            cur = conn.cursor()
            cur.execute('insert into dttsa_execution_status_tbl (function_name,execution_status,msg) values (%s,%s,%s);',(function_name,status,str(msg)))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print("error: addDTReports ", str(e))
    
    def backupServiceQoSTest(self,test_count):
        try:
            BackupServiceAPIs = self.getBackupServicesToCheck(test_count)
            qosAnalyzer = QoSAnalyzer()
            for api in BackupServiceAPIs:
                self.addBackupAPIForQoS(api[1],api[0])
                testURL = self.createBackupURL(api[3],api[2])
                print(testURL)
                self.addBackupQoSStatus("BQoS","Running","For API "+str(api))
                results = qosAnalyzer.backupQoSTest(api[4],testURL,api[5])
                print(results)
                results.insert(0,api[0])#apiID
                results.insert(0,api[1])#DT_ID
                self.addBackupQoSRecords(results)
                self.updateBackupQoSTestCount(api[1],api[0])
            self.addBackupQoSStatus("BQoS","Finished")
            return True
        except Exception as e:
            print("Error: backupServiceQoSTest ", str(e))
        
