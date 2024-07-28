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

class AnalyticSupportService:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read('environment_config.ini')
        #print(config['database']['DB_IP'])
        self.dbConnection = DBConnection()
        # self.API_vulnerbility_service_IP = config['servers']['API_VULNERBILITY_SERVICE_IP']
        # self.clearDB()

    def getDTAPIs(self, DT_ID):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select * from api_tbl where DT_ID = %s and status=1;',(DT_ID))
        DTs = cur.fetchall()
        cur.close()
        return DTs
    
    def getDTDetails(self):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute('select * from dt_tbl where status=1;')
        DTs = cur.fetchall()
        cur.close()
        return DTs
    
    def getAnalysisCyclesCount(self):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute(' select distinct status from dt_type_tbl where status <0;')
        DTs = cur.fetchall()
        cur.close()
        return DTs
    
    def getRepAttacks(self):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        # cur.execute("select distinct dt_id,attacked_dt from reputation_attack_possibilities where rep_attack_prediction='RA';")
        cur.execute("select distinct dt_id,attacked_dt,analysis,using_category, attack from reputation_attack_possibilities where rep_attack_prediction='RA';")
        DTs = cur.fetchall()
        cur.close()
        return DTs
    
    def getUniqueRepAttacks(self):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        # cur.execute("select distinct dt_id,attacked_dt from reputation_attack_possibilities where rep_attack_prediction='RA';")
        cur.execute("select distinct dt_id,attacked_dt, attack from reputation_attack_possibilities where rep_attack_prediction='RA';")
        DTs = cur.fetchall()
        cur.close()
        return DTs
    
    def getAvgTrustScore(self):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute("select ROUND( AVG(trust_score)::numeric, 2 )  from dttsa_trust_scores_tbl;")
        DTs = cur.fetchall()
        cur.close()
        return DTs
    
    def getDTTypes(self):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute("select distinct dt_id,dt_type_predict,status from dt_type_tbl where dt_type_predict is not null and status = (select min(status) from dt_type_tbl) order by status asc;")
        DTs = cur.fetchall()
        cur.close()
        return DTs
    
    def getDTSubs(self):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute("select distinct dt_id,sub_dt_id from dt_sub_tbl where status = 1;")
        DTs = cur.fetchall()
        cur.close()
        return DTs
    
    def getDTTrustScores(self,dt_id):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute("select * from dttsa_trust_scores_tbl where dt_id=%s and status=1 order by iteration_id asc;",(dt_id,))
        DTs = cur.fetchall()
        cur.close()
        return DTs
    
    def getDTTrustEffect(self,dt_id):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute("select dt_id,(status * -1) as iteration_id,sum(trust_effect) as teffect from trust_effect_calculation_tbl where dt_id=%s group by dt_id,status order by status desc;",(dt_id,))
        DTs = cur.fetchall()
        cur.close()
        return DTs
    
    def getDTTypeCounts(self,dt_id):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute("select dt_type_predict,count(dt_type_predict) from dt_type_tbl where dt_type_predict is not null and dt_id=%s group by dt_type_predict;",(dt_id,))
        DTs = cur.fetchall()
        cur.close()
        return DTs

    def getAvgTnxTime(self):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute("select avg(response_time) as avg_tx_time from dt_change_con_data_submission_tbl;")
        DTs = cur.fetchall()
        cur.close()
        return DTs

    def getChangeCons(self):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT distinct dt_id, change_dt,CASE WHEN result = '1' THEN 'success' ELSE 'fail' END AS result FROM change_requests_tbl order by dt_id asc;")
        DTs = cur.fetchall()
        cur.close()
        return DTs
    
    def getReputationDetails(self,dt_id):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute("select dt_id,category,count(category) from reputation_categorization_tbl where dt_id=%s group by dt_id,category;",(dt_id,))
        DTs = cur.fetchall()
        cur.close()
        return DTs
    
    def getDTTrustCalculation(self,dt_id):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        cur.execute("select dt_id,category,dt_type_prediction,count(dt_type_prediction) from dttsa_trust_calculations_tbl where dt_id=%s group by dt_id,category,dt_type_prediction order by category asc;",(dt_id,))
        DTs = cur.fetchall()
        cur.close()
        return DTs
    
    def getDTTypePrediction(self):
        conn = self.dbConnection.get_db_connection()
        cur = conn.cursor()
        # cur.execute("select distinct dt_id,attacked_dt from reputation_attack_possibilities where rep_attack_prediction='RA';")
        cur.execute("select DISTINCT ON (dt_id) dt_id,dt_type_predict,count(dt_type_predict) as hits from dt_type_tbl where dt_type_predict is not null group by dt_id,dt_type_predict order by dt_id,hits desc;")
        DTs = cur.fetchall()
        cur.close()
        return DTs
    
    # def getDTSubs(self):
    #     conn = self.dbConnection.get_db_connection()
    #     cur = conn.cursor()
    #     cur.execute("select * from dt_sub_tbl where status = 1;")
    #     DTs = cur.fetchall()
    #     cur.close()
    #     return DTs

   