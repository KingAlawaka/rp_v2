#DTTSA support functionalities
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
from datetime import datetime
import os
import pandas as pd
from glob import glob;from os.path import expanduser

class DTTSASupportServices:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read('environment_config.ini')
        #print(config['database']['DB_IP'])
        self.dbConnection = DBConnection()
        # self.API_vulnerbility_service_IP = config['servers']['API_VULNERBILITY_SERVICE_IP']
        # self.clearDB()

    def clearDB(self):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT truncate_tables('postgres');")
        cur.execute("SELECT truncate_tables('admin');")
        conn.commit()
        cur.close()
        conn.close()
    
    def userRegister(self,username,password,org_code):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('insert into user_tbl (username,password,org_code) values (%s,%s,%s)',(username,password,org_code))
        conn.commit()
        cur.close()
        conn.close()

    def addDTType(self,dt_id,dt_type):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('insert into dt_type_tbl (DT_ID,dt_type) values (%s,%s)',(dt_id,dt_type))
        conn.commit()
        cur.close()
        conn.close()

    def getDTType(self,dt_id):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select * from dt_type_tbl where DT_ID= %s and status=1;',(dt_id,))
        dt_type = cur.fetchall()
        cur.close()
        conn.close()
        return dt_type

    def getUser(self,username,org_code):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select * from user_tbl where username=%s and org_code=%s and status=1;',(username,org_code))
        user = cur.fetchall()
        cur.close()
        conn.close()
        return user
    
    def getOrgList(self):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select * from organization_tbl where status=1;')
        orgList = cur.fetchall()
        cur.close()
        return orgList

    def getDTs(self):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select dt_tbl.org_code,dt_tbl.dt_code,dt_tbl.dt_name,sum(api_security_check_tbl.low_count) as low_sum,sum(api_security_check_tbl.mid_count) as mid_sum,sum(api_security_check_tbl.high_count) as high_sum from dt_tbl join api_security_check_tbl on dt_tbl.id = dt_id where dt_tbl.status=1 and api_security_check_tbl.status=1 group by dt_tbl.org_code,dt_tbl.dt_code,dt_tbl.dt_name; ')
        DTs = cur.fetchall()
        cur.close()
        return DTs

    def addAPIs(self,APIs,DT_ID):
        APIList = []
        try:
            conn = self.dbConnection.get_db_connection()
            cur = conn.cursor()
            for API in APIs:
                    url = str(API['URL'])
                    desc =str(API['Description'])
                    type_req =str(API['Type'])
                    sam_json = str(API['Sample_json']).strip()
                    auth_to = str(API['User_auth_token'])
                
                    cur.execute('insert into API_tbl (DT_ID,URL,description,type,sample_json,user_auth_token ) values (%s,%s,%s,%s,%s,%s) returning id;',(DT_ID,url,desc,type_req,sam_json,auth_to))
                    API_ID = cur.fetchall()
                    conn.commit()
                    tempAPI = [DT_ID,API_ID[0][0],url,sam_json,type_req]
                    APIList.append(tempAPI)
                    
            cur.close()
            conn.close()
            return APIList
        except Exception as e:
            print("error: addAPIs ", str(e))
            return APIList
    
    def addDT(self,org_code,DT_code,DT_name,DT_description,DT_IP):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('insert into DT_tbl (org_code,DT_code,DT_name,DT_description,DT_IP) values (%s,%s,%s,%s,%s) returning id;',(org_code,DT_code,DT_name,DT_description,DT_IP))
        retValue = cur.fetchall()
        
        conn.commit()
        cur.close()
        conn.close()
        try:
            return retValue[0][0]
        except:
            return -1
    
    def getDTAPIs(self, DT_ID):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select * from api_tbl where DT_ID = %s and status=1;',(DT_ID))
        DTs = cur.fetchall()
        cur.close()
        return DTs
    
    def getOtherDTAPIs(self,DT_ID):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        # cur.execute("select * from api_tbl where DT_ID !=%s and (description = '[GET][OUT]' or description = '[POST][OUT]');",(DT_ID))
        cur.execute("select * from api_tbl where DT_ID !=%s and status=1 and (description = '[GET][OUT]' or description = '[POST][OUT]') and DT_ID not in (select sub_dt_id from dt_sub_tbl where status=1 group by sub_dt_id having count(*) > 5) ;",(DT_ID,))
        #cur.execute('select * from api_tbl where DT_ID != %s;',(DT_ID))
        DTs = cur.fetchall()
        cur.close()
        return DTs
    
    def getOtherDTAPIsConsideringTrust(self,DT_ID):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        # cur.execute("select * from api_tbl where DT_ID !=%s and (description = '[GET][OUT]' or description = '[POST][OUT]');",(DT_ID))
        cur.execute("select * from api_tbl where DT_ID !=%s and status=1 and (description = '[GET][OUT]' or description = '[POST][OUT]') and DT_ID in (select distinct dt_id from dt_type_tbl where dt_type_predict is not null and dt_type_predict='n' order by dt_id asc) and DT_ID not in (select sub_dt_id from dt_sub_tbl where dt_id=%s and status=-1);",(DT_ID,DT_ID))
        #cur.execute('select * from api_tbl where DT_ID != %s;',(DT_ID))
        DTs = cur.fetchall()
        cur.close()
        return DTs
    
    def getDTDependencies(self):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select dt_id,sub_dt_id,count(dt_id) from dt_sub_tbl where status=1 group by dt_id,sub_dt_id order by dt_id;')
        records = cur.fetchall()
        cur.close()
        return records

    def getDTIDs(self):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select id from dt_tbl where status=1;')
        records = cur.fetchall()
        cur.close()
        return records
    
    def getDTDetails(self,dt_id):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select * from dt_tbl where id = %s and status=1;',(dt_id,))
        records = cur.fetchall()
        cur.close()
        return records
    
    def getDTDataByType(self,dt_id,data_type):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select * from dt_data_submission_tbl where data_type=%s and sub_dt_id=%s and status=1;',(data_type,dt_id))
        records = cur.fetchall()
        cur.close()
        return records
    
    def getDTTSAQoSValues(self,dt_id):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select * from api_qos_records_tbl where dt_id =%s and time_per_req_mean > 0 and status=1;',(dt_id,))
        records = cur.fetchall()
        cur.close()
        return records
    
    def getDTTSAQoSValuesByTestType(self,dt_id,test_type):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select * from api_qos_records_tbl where dt_id =%s and time_per_req_mean > 0 and test_type=%s and status=1;',(dt_id,test_type))
        records = cur.fetchall()
        cur.close()
        return records
    
    def getDTTSABackupQoSValues(self,dt_id):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select * from backup_qos_records_tbl where dt_id =%s and time_per_req_mean > 0 and status=1;',(dt_id,))
        records = cur.fetchall()
        cur.close()
        return records

    def getTrustCalculationsByIteration(self,itration):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        # cur.execute('select id,dt_id,sum(avg) as trust_score from dttsa_trust_calculations_tbl group by dt_id,id order by id desc limit 4;')
        #TODO change the table and get newly calculated trust score values
        # cur.execute('select dt_id,sum(avg) as trust_score from temp_dttsa_trust_calculations_tbl where status=1 group by dt_id order by dt_id asc;')
        cur.execute('select dt_id,trust_score from dttsa_trust_scores_tbl where iteration_id=%s order by dt_id asc;',(itration,))
        records = cur.fetchall()
        cur.close()
        return records
    
    def getTrustCalculationsRecords(self):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        # cur.execute('select id,dt_id,sum(avg) as trust_score from dttsa_trust_calculations_tbl group by dt_id,id order by id desc limit 4;')
        cur.execute('select dt_id,category,sum(low_count),sum(mid_count),sum(high_count),avg(avg) from temp_dttsa_trust_calculations_tbl where status=1 group by dt_id,category order by dt_id asc;')
        records = cur.fetchall()
        cur.close()
        return records
    
    def getAPIVulnerbilityFinalValues(self):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select dt_id,sum(low_count) as low,sum(mid_count) as mid, sum(high_count) as high  from api_security_check_tbl where status=1 group by dt_id;')
        records = cur.fetchall()
        cur.close()
        return records

    def addDTSubs(self,dt_id,subList):
        try:
            conn = self.dbConnection.get_db_connection()
            cur = conn.cursor()
            for sub in subList:
                    sub_dt_id = str(sub['sub_dt_id'])
                    sub_api_id = str(sub['sub_api_id'])
                    url = str(sub['url'])
                    type= str(sub['req_type'])
                    cur.execute('insert into dt_sub_tbl (dt_id,sub_dt_id,sub_api_id,url,type) values (%s,%s,%s,%s,%s);',(dt_id,sub_dt_id,sub_api_id,url,type))
                    conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print("error: addAPIs ", str(e))
    
    def getQoSdata(self):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select dt_id,round(avg(req_per_sec_mean)::numeric,2) as avg_req_per_sec,round(avg(time_per_req_min)::numeric,4)  as avg_time_per_req_min,round(avg(time_per_req_max)::numeric,4)  as avg_time_per_req_max,round(avg(time_per_req_mean)::numeric,4)  as avg_time_per_req_mean,round(avg(sum_response_time)::numeric,4)  as avg_response_time from api_qos_records_tbl where status=1 group by dt_id order by dt_id;')
        # cur.execute('select dt_id,avg(req_per_sec_mean) as avg_req_per_sec,avg(time_per_req_min) as avg_time_per_req_min,avg(time_per_req_max) as avg_time_per_req_max,avg(time_per_req_mean) as avg_time_per_req_mean,avg(sum_response_time) as avg_response_time from api_qos_records_tbl group by dt_id order by dt_id;')
        orgList = cur.fetchall()
        cur.close()
        return orgList
    
    def addDTReportImpactCategories(self,dt_id,sub_dt_id,category,unit,low_count,mid_count,high_count,dt_impact_prediction):
        try:
            conn = self.dbConnection.get_db_connection()
            cur = conn.cursor()
            cur.execute('insert into dttsa_dt_values_impact_categories_tbl (dt_id,sub_dt_id,category,unit,low_count,mid_count,high_count,dt_impact_prediction,status) values (%s,%s,%s,%s,%s,%s,%s,%s,1);',(dt_id,sub_dt_id,category,unit,low_count,mid_count,high_count,dt_impact_prediction))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print("error: addDTReportImpactCategories ", str(e))
        

    def addDTReports(self,dt_id,report):
        try:
            conn = self.dbConnection.get_db_connection()
            cur = conn.cursor()
            for r in report:
                sub_dt_id = str(r['dt_id'])
                data_type = str(r['data_type'])
                stdev_value = str(r['stdev_value'])
                min = str(r['min'])
                max = str(r['max'])
                avg = str(r['avg'])
                cur.execute('insert into dt_data_submission_tbl (DT_ID,sub_dt_id,data_type,stdev_value,min,max,avg,status) values (%s,%s,%s,%s,%s,%s,%s,1);',(dt_id,sub_dt_id,data_type,stdev_value,min,max,avg))
                conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print("error: addDTReports ", str(e))

    def addDTChangeConReports(self,dt_id,report):
        try:
            conn = self.dbConnection.get_db_connection()
            cur = conn.cursor()
            for r in report:
                response_status = str(r['response'])
                response_time = str(r['elapsed_time'])
                cur.execute('insert into dt_change_con_data_submission_tbl (DT_ID,response_status,response_time,status) values (%s,%s,%s,1);',(dt_id,response_status,response_time))
                conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print("error: addDTChangeConReports ", str(e))

    def addDTChangeTime(self,dt_id,response_status,response_time):
        try:
            conn = self.dbConnection.get_db_connection()
            cur = conn.cursor()
            cur.execute('insert into dt_change_con_data_submission_tbl (DT_ID,response_status,response_time,status) values (%s,%s,%s,1);',(dt_id,response_status,response_time))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print("error: addDTChangeTime ", str(e))


    def saveTblsAsCSV(self):
        try:
            conn = self.dbConnection.get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';")
            allTables = cur.fetchall()
            cur.close()
            conn.close()
            curr_dt=datetime.now()
            ts = int(round(curr_dt.timestamp()))
            save_location = "csv/"
            if not os.path.isdir(save_location):
                os.makedirs(save_location)
            for tbl in allTables:
                filename = "dttsa_"+tbl[0]+"_"+str(ts)+".csv"
                conn = self.dbConnection.get_db_connection()
                cursor = conn.cursor()
                data = pd.read_sql('select * from '+ tbl[0],conn)
                data.to_csv(save_location+filename,index=False)
            return "Ok"
        except Exception as e:
            print("error: addDTReports ", str(e))
            return "error: addDTReports ", str(e)
    
    def recordExecutionStatus(self,function_name,status,msg=""):
        try:
            conn = self.dbConnection.get_db_connection()
            cur = conn.cursor()
            cur.execute('insert into dttsa_execution_status_tbl (function_name,execution_status,msg) values (%s,%s,%s);',(function_name,status,str(msg)))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print("error: recordExecutionStatus ", str(e))

    def addQoSStaging(self,dt_id,low_count,mid_count,high_count,category,test_type):
        try:
            conn = self.dbConnection.get_db_connection()
            cur = conn.cursor()
            cur.execute('insert into dttsa_qos_staging_tbl (dt_id,low_count,mid_count,high_count,category,test_type) values (%s,%s,%s,%s,%s,%s);',(dt_id,low_count,mid_count,high_count,category,test_type))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print("error: recordExecutionStatus ", str(e))
    
    
    def addTrustEffectCalculation(self,dt_id,indirect_con_dt,hop_count,trust_effect,trust_score):
        try:
            conn = self.dbConnection.get_db_connection()
            cur = conn.cursor()
            cur.execute('insert into trust_effect_calculation_tbl (dt_id,indirect_connected_dt,hop_count,trust_effect,trust_score) values (%s,%s,%s,%s,%s);',(dt_id,indirect_con_dt,hop_count,trust_effect,trust_score))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print("error: recordExecutionStatus ", str(e))
    
    def recordTrustScores(self,dt_id,category,lcount,mcount,hcount,avg,dt_type):
        try:
            conn = self.dbConnection.get_db_connection()
            cur = conn.cursor()
            cur.execute('insert into dttsa_trust_calculations_tbl (dt_id,category,low_count,mid_count,high_count,avg,dt_type_prediction) values (%s,%s,%s,%s,%s,%s,%s);',(dt_id,category,lcount,mcount,hcount,avg,dt_type))
            cur.execute('insert into temp_dttsa_trust_calculations_tbl (dt_id,category,low_count,mid_count,high_count,avg) values (%s,%s,%s,%s,%s,%s);',(dt_id,category,lcount,mcount,hcount,avg))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print("error: recordTrustScores ", str(e))

    def getDTtypePredictions(self,dt_id):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select dt_id,dt_type_prediction,category from dttsa_trust_calculations_tbl where dt_id=%s and status=1;',(dt_id,))
        records = cur.fetchall()
        cur.close()
        return records
    
    def updateDTSubs(self,dt_id,sub_dt_id):
        try:
            conn = self.dbConnection.get_db_connection()
            cur = conn.cursor()
            cur.execute('update dt_sub_tbl set status=-1 where dt_id=%s and sub_dt_id=%s and status=1;',(dt_id,sub_dt_id))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print("error: updateDTSubs ", str(e))

    
    def updateDTTypeTblWithPrediction(self,dt_id,prediction):
        try:
            conn = self.dbConnection.get_db_connection()
            cur = conn.cursor()
            cur.execute('update dt_type_tbl set dt_type_predict=%s where dt_id=%s and status=1;',(prediction,dt_id))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print("error: updateDTTypeTblWithPrediction ", str(e))
    
    def truncateTempTrustScores(self):
        try:
            conn = self.dbConnection.get_db_connection()
            cur = conn.cursor()
            cur.execute('TRUNCATE temp_dttsa_trust_calculations_tbl  RESTART IDENTITY;')
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print("error: recordTrustScores ", str(e))

    def qosExecutionStatus(self):
        ret_value = "Started"
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute("select * from dttsa_execution_status_tbl where function_name like 'QoS_%' and execution_status='Finished' and status=1 order by msg desc;")
        # cur.execute('select dt_id,avg(req_per_sec_mean) as avg_req_per_sec,avg(time_per_req_min) as avg_time_per_req_min,avg(time_per_req_max) as avg_time_per_req_max,avg(time_per_req_mean) as avg_time_per_req_mean,avg(sum_response_time) as avg_response_time from api_qos_records_tbl group by dt_id order by dt_id;')
        finished = cur.fetchall()
        cur.close()
        cur = conn.cursor()
        cur.execute("select * from dttsa_execution_status_tbl where function_name like 'QoS_%' and execution_status='Started' and status=1  order by msg desc;")
        started = cur.fetchall()
        cur.close()
        if len(finished) == 0 and len(started) == 0:
            ret_value = "None"
        elif len(finished) == len(started):
            ret_value = "Finished"
        return ret_value
    
    def qosSpecificTestExecutionStatus(self,test_type):
        ret_value = "Started"
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute("select * from dttsa_execution_status_tbl where function_name like %s and execution_status='Finished' and status=1 order by msg desc;",("QoS_"+test_type,))
        # cur.execute('select dt_id,avg(req_per_sec_mean) as avg_req_per_sec,avg(time_per_req_min) as avg_time_per_req_min,avg(time_per_req_max) as avg_time_per_req_max,avg(time_per_req_mean) as avg_time_per_req_mean,avg(sum_response_time) as avg_response_time from api_qos_records_tbl group by dt_id order by dt_id;')
        finished = cur.fetchall()
        cur.close()
        cur = conn.cursor()
        cur.execute("select * from dttsa_execution_status_tbl where function_name like %s and execution_status='Started' and status=1  order by msg desc;",("QoS_"+test_type,))
        started = cur.fetchall()
        cur.close()
        if len(finished) == 0 and len(started) == 0:
            ret_value = "None"
        elif len(finished) == len(started):
            ret_value = "Finished"
        return ret_value

    def backupQoSExecutionStatus(self):
        ret_value = "Started"
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute("select * from dttsa_execution_status_tbl where function_name='BQoS' and execution_status='Finished' and status=1 order by msg desc;")
        # cur.execute('select dt_id,avg(req_per_sec_mean) as avg_req_per_sec,avg(time_per_req_min) as avg_time_per_req_min,avg(time_per_req_max) as avg_time_per_req_max,avg(time_per_req_mean) as avg_time_per_req_mean,avg(sum_response_time) as avg_response_time from api_qos_records_tbl group by dt_id order by dt_id;')
        finished = cur.fetchall()
        cur.close()
        cur = conn.cursor()
        cur.execute("select * from dttsa_execution_status_tbl where function_name='BQoS' and execution_status='Started' and status=1  order by msg desc;")
        started = cur.fetchall()
        cur.close()
        if len(finished) == 0 and len(started) == 0:
            ret_value = "None"
        elif len(finished) == len(started):
            ret_value = "Finished"
        return ret_value

    def apiExecutionStatus(self):
        ret_value = "Started"
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute("select * from dttsa_execution_status_tbl where function_name='API' and execution_status='Running' and msg='APis remaning0' and status=1  order by id desc;")
        records = cur.fetchall()
        cur.close()
        if len(records) == 0:
            ret_value = "None"
        else:
            ret_value = "Finished"
        return ret_value
    
    def getDTTrustCalculations(self,dt_id):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select dt_type_prediction,count(dt_type_prediction) from dttsa_trust_calculations_tbl where dt_id = %s and status=1 group by dt_type_prediction;',(dt_id,))
        # cur.execute('select * from api_qos_records_tbl where dt_id =%s and time_per_req_mean > 0 and status=1;',(dt_id,))
        records = cur.fetchall()
        cur.close()
        return records
    
    def addTrustScoresToTrustScoresTbl(self,iteration_id,dt_id,n_count,c_count,m_count,trust_score):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('insert into dttsa_trust_scores_tbl (iteration_id,dt_id,n_count,c_count,m_count,trust_score) values (%s,%s,%s,%s,%s,%s);',(iteration_id,dt_id,n_count,c_count,m_count,trust_score))
        conn.commit()
        cur.close()
        conn.close()

    def updateStatusforTbls(self,iteration_count):
        try:
            conn = self.dbConnection.get_db_connection()
            cur = conn.cursor()
            # cur.execute('update dt_type_tbl set dt_type_predict=%s where dt_id=%s and status=1;',(iteration_count,))
            cur.execute('update api_security_check_tbl set status=%s where status=1;',(iteration_count,))
            cur.execute('update api_qos_records_tbl set status=%s where status=1;',(iteration_count,))
            cur.execute('update backup_qos_records_tbl set status=%s where status=1;',(iteration_count,))
            cur.execute('update dt_data_submission_tbl set status=%s where status=1;',(iteration_count,))
            cur.execute('update dt_type_tbl set status=%s where status=1;',(iteration_count,))
            cur.execute('update dttsa_execution_status_tbl set status=%s where status=1;',(iteration_count,))
            cur.execute('update dttsa_trust_calculations_tbl set status=%s where status=1;',(iteration_count,))
            cur.execute('update temp_dttsa_trust_calculations_tbl set status=%s where status=1;',(iteration_count,))
            cur.execute('update trust_effect_calculation_tbl set status=%s where status=1;',(iteration_count,))
            cur.execute('update dt_trust_report_tbl set status=%s where status=1;',(iteration_count,))
            cur.execute('update reputation_categorization_tbl set status=%s where status=1;',(iteration_count,))
            cur.execute('update dttsa_qos_staging_tbl set status=%s where status=1;',(iteration_count,))
            cur.execute('update dttsa_dt_values_impact_categories_tbl set status=%s where status=1;',(iteration_count,))
            cur.execute('update reputation_attack_possibilities set status=%s where status=1;',(iteration_count,))
            cur.execute('update debug_msg set status=%s where status=1;',(iteration_count,))
            # cur.execute('update change_requests_tbl set status=%s where status=1;',(iteration_count,))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print("error: updateStatusforTbls ", str(e))

    def getDTIDsSubmitDTReports(self):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select distinct dt_id FROM dt_data_submission_tbl where status=1;')
        # cur.execute('select * from api_qos_records_tbl where dt_id =%s and time_per_req_mean > 0 and status=1;',(dt_id,))
        records = cur.fetchall()
        cur.close()
        return records
    
    def getAllTrustScores(self):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select dt_id,trust_score from dttsa_trust_scores_tbl order by dt_id,iteration_id asc;')
        records = cur.fetchall()
        cur.close()
        return records
    
    def dtTrustReportTbl(self,report_dt_id,for_dt_id,category,low_count,mid_count,high_count):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('insert into dt_trust_report_tbl (report_dt_id,for_dt_id,category,low_count,mid_count,high_count) values (%s,%s,%s,%s,%s,%s);',(report_dt_id,for_dt_id,category,low_count,mid_count,high_count))
        conn.commit()
        cur.close()
        conn.close()
    
    def getDTTrustReports(self,for_dt,category):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select report_dt_id,sum(low_count) as low,sum(mid_count) as mid,sum(high_count) as high from dt_trust_report_tbl where for_dt_id = %s and report_dt_id != %s and category=%s group by report_dt_id;',(for_dt,for_dt,category))
        records = cur.fetchall()
        cur.close()
        return records
    
    def getDTsByPrediction(self,prediction_type):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select distinct dt_id from dt_type_tbl where dt_type_predict=%s order by dt_id asc;',(prediction_type,))
        records = cur.fetchall()
        cur.close()
        return records
    
    def addDTReputationCategorization(self,dt_id,pos_count,neg_count,eq_count,category):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('insert into reputation_categorization_tbl (dt_id,pos_count,neg_count,eq_count,category) values (%s,%s,%s,%s,%s);',(dt_id,pos_count,neg_count,eq_count,category))
        conn.commit()
        cur.close()
        conn.close()

    def getAPIsToAnalyze(self,dt_type1,dt_type2,category,iteration_count):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        # cur.execute('select * from api_tbl where dt_id in (select distinct dt_id from dt_type_tbl where dt_type_predict=%s and status=%s) and status =1;',(dt_type,iteration_count))
        cur.execute('select * from api_tbl where dt_id in (select distinct dt_id from dttsa_trust_calculations_tbl where (dt_type_prediction=%s or dt_type_prediction=%s) and category=%s and status=%s) and status =1;',(dt_type1,dt_type2,category,iteration_count))
        records = cur.fetchall()
        cur.close()
        return records
    
    def getPreviousAPIPrediction(self,dt_id,iteration_count):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select dt_id,dt_type_prediction,category from dttsa_trust_calculations_tbl where dt_id=%s and status=%s;',(dt_id,iteration_count))
        records = cur.fetchall()
        cur.close()
        return records
    
    def getPreviousAPIRecords(self,dt_id,api_id,iteration_count):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select * from api_security_check_tbl where dt_id=%s and api_id=%s and status=%s;',(dt_id,api_id,iteration_count))
        records = cur.fetchall()
        cur.close()
        return records
    
    
    def addDTReputationAttackLog(self,dt_id,attacked_dt_id,attack,strength,attack_type,initiator_dt_id):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('insert into reputation_attack_log_tbl (dt_id,attacked_dt_id,attack,strength,attack_type,initiator_dt_id,status) values (%s,%s,%s,%s,%s,%s,1);',(dt_id,attacked_dt_id,attack,strength,attack_type,initiator_dt_id))
        conn.commit()
        cur.close()
        conn.close()

    def addVulnerableRepAttackPossibleDTs(self,dt_id,attacked_dt,analysis,using_category,logic,attack,attack_type,rep_attack_prediction,confirmation,role):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('insert into reputation_attack_possibilities (dt_id,attacked_dt,analysis,using_category,logic,attack,attack_type,rep_attack_prediction,confirmation,role,status) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1)',(dt_id,attacked_dt,analysis,using_category,logic,attack,attack_type,rep_attack_prediction,confirmation,role))
        conn.commit()
        cur.close()
        conn.close()

    def getDTValuesImpactPredictionsByCategory(self,sub_dt_id,iteration_count,category):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select dt_id,sub_dt_id,dt_impact_prediction,count(dt_impact_prediction) as hit_count from dttsa_dt_values_impact_categories_tbl where status = %s and category=%s and sub_dt_id=%s group by dt_id,sub_dt_id,dt_impact_prediction order by hit_count desc;',(iteration_count,category,sub_dt_id))
        records = cur.fetchall()
        cur.close()
        return records
    
    def getDTTrustCalculationsByCategory(self,dt_id,category,iteration_count):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select * from dttsa_trust_calculations_tbl where status =%s and dt_id=%s and category=%s;',(iteration_count,dt_id,category))
        records = cur.fetchall()
        cur.close()
        return records
    
    def getDTSubByCategory(self,dt_id,category):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select distinct dt_id from dt_sub_tbl where sub_dt_id = %s and type !=%s union select distinct sub_dt_id from dt_sub_tbl where dt_id = %s and type=%s;',(dt_id,category,dt_id,category))
        records = cur.fetchall()
        cur.close()
        return records

    def getDTtypePredictionHistory(self,dt_id):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select distinct dt_id,dt_type,dt_type_predict,count(dt_type_predict) as hit_count from dt_type_tbl where dt_type_predict is not null and dt_id=%s group by dt_id,dt_type,dt_type_predict order by hit_count desc;',(dt_id,))
        records = cur.fetchall()
        cur.close()
        return records

    def addDebugMsg(self,msg):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('insert into debug_msg (msg,status) values (%s,1)',(msg,))
        conn.commit()
        cur.close()
        conn.close()

    def getPossibleAttacks(self,hit_count):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select * from (select distinct dt_id,attacked_dt,count(attacked_dt) as hit_count from reputation_attack_possibilities where rep_attack_prediction=%s group by  dt_id,attacked_dt order by hit_count desc) as hit_pa where hit_pa.hit_count >= %s;',('PA',hit_count))
        records = cur.fetchall()
        cur.close()
        return records
    
    def getPossibleAttackContinuityCount(self,dt_id,attacked_dt_id):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select distinct status from reputation_attack_possibilities where dt_id=%s and attacked_dt=%s order by status asc OFFSET 0 ROWS FETCH FIRST 3 ROWS ONLY;',(dt_id,attacked_dt_id))
        records = cur.fetchall()
        cur.close()
        return records
    
    def getReputationLabelForDT(self,dt_id):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select dt_type_predict,count(dt_type_predict) as type_count from dt_type_tbl where dt_type_predict is not null and dt_id=%s group by dt_type_predict order by type_count desc;',(dt_id,))
        records = cur.fetchall()
        cur.close()
        return records

    def addConnectionChangeRequest(self,dt_id,change_dt,dt_rep_cat,change_dt_rep_cat,result,dt_url):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('insert into change_requests_tbl (dt_id,change_dt,dt_rep_cat,change_dt_rep_cat,result,dt_url) values (%s,%s,%s,%s,%s,%s);',(dt_id,change_dt,dt_rep_cat,change_dt_rep_cat,result,dt_url))
        conn.commit()
        cur.close()
        conn.close()

    def updateConnectionChangeRequest(self,dt_id,change_dt,request_verdict):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute("update change_requests_tbl set result=%s,status=-1,completed_timestamp=current_timestamp at time zone 'UTC' where dt_id = %s and change_dt = %s and status=1;",(request_verdict,dt_id,change_dt))
        conn.commit()
        cur.close()
        conn.close()

    def getConnectionChangeDTUrl(self,dt_id,con_dt):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select * from change_requests_tbl where dt_id=%s and change_dt=%s and status = 1; ',(dt_id,con_dt))
        records = cur.fetchall()
        cur.close()
        return records



    
# 


    # def addAPISecurityCheck(self,DT_ID,API_ID,scan_id):
    #     try:
    #         conn = self.dbConnection.get_db_connection()
    #         cur = conn.cursor()
    #         cur.execute('insert into api_security_check_tbl (DT_ID,API_ID,scan_id) values (%s,%s,%s);',(DT_ID,API_ID,scan_id))
    #         conn.commit()
    #         cur.close()
    #         conn.close()
    #     except:
    #         print("Error: AddAPISecurityCheck")
    
    # def checkAPIVulnerbilities(self,DT_ID,API_ID,url,sample_json,type_req):
    #     dictToSend = {"appname" : str(DT_ID)+"_"+str(API_ID),"url": url ,"headers": "","body": sample_json,"method": type_req}
    #     jsonObject = jsonify(dictToSend)
    #     req_url = self.API_vulnerbility_service_IP + '/scan/'
    #     res = requests.post(req_url, json= dictToSend)
    #     v = res.json()
    #     if v['status']:
    #         scan_id = v['status']
    #         self.addAPISecurityCheck(DT_ID,API_ID,scan_id) #save to api_security_check_tbl
    #         print(scan_id)
    