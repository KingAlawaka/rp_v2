from cgi import print_form
import sqlite3
import os
import pandas as pd
from glob import glob;from os.path import expanduser
from datetime import datetime

class DBHelper:
    def __init__(self):
        self.DB_name = "database.db"
        self.DB_file = "schema.sql"
    
    def createDB(self,db_name):
        self.DB_name = db_name
        connection = sqlite3.connect(os.fspath('databases/'+self.DB_name))

        with open(self.DB_file) as f:
            connection.executescript(f.read())
        
        cur = connection.cursor()

        cur.execute("insert into trans_tbl (trans,status) values ('Database created',1)")

        #remove for temp 
        #cur.execute("INSERT INTO subs_tbl (direction, req_type, DT_ID, API_ID, url, status) VALUES ('from','GET',2,2,'http://127.0.0.1:9100/sendvalue/',1);")
        # cur.execute("INSERT INTO subs_external_tbl (direction, req_type, DT_ID, API_ID, url, status) VALUES ('to','GET',2,2,'http://127.0.0.1:9100/sendvalue/',1);")
        # cur.execute("INSERT INTO subs_external_tbl (direction, req_type, DT_ID, API_ID, url, status) VALUES ('to','POST',2,2,'http://127.0.0.1:9100/postother/',1);")
        # cur.execute("INSERT INTO subs_internal_tbl (direction, req_type, DT_ID, API_ID, url,formula_position, status) VALUES ('from','GET',2,2,'http://127.0.0.1:9100/getvalue/',2,1);")
        # cur.execute("INSERT INTO subs_internal_tbl (direction, req_type, DT_ID, API_ID, url,formula_position, status) VALUES ('from','POST',2,2,'http://127.0.0.1:9100/submitvalue/',2,1);")

        connection.commit()
        connection.close()
    
    def get_db_connection(self):
        conn = sqlite3.connect(os.fspath('databases/'+self.DB_name))
        conn.row_factory = sqlite3.Row
        return conn

    def readDB(self,query):
        conn = self.get_db_connection()
        allRows = conn.execute(query).fetchall()
        conn.close()
        #print(posts)
        # for p in posts:
        #     print(p['created'])
        return allRows
    
    def getAllTransactionTbl(self):
        allRows = self.readDB('select * from trans_tbl where status=1')
        return allRows
    
    def getAllDataTbl(self):
        allRows = self.readDB("select * from data_tbl where status=1;")
        return allRows

    def addTransaction(self,content):
        try:
            connection = self.get_db_connection()
            cur = connection.cursor()
            cur.execute("insert into trans_tbl (trans,status) values ('"+ content +"',1)")
            connection.commit()
            connection.close()
        except Exception as e:
            print("except: addTransaction ", str(e))

    def addDebugMsg(self,msg):
        try:
            connection = self.get_db_connection()
            cur = connection.cursor()
            cur.execute("insert into debug_tbl (msg,status) values ('"+ msg +"',1)")
            connection.commit()
            connection.close()
        except Exception as e:
            print("except: addTransaction ", str(e))
    
    def insertDataTbl(self,req_type,DT_ID,API_ID,value):
        try:
            connection = self.get_db_connection()
            cur = connection.cursor()
            cur.execute('insert into data_tbl (req_type,DT_ID,API_ID,value,used,status) values ("'+ req_type +'",'+ str(DT_ID)+','+str(API_ID)+','+str(value)+',0,1);')
            connection.commit()
            connection.close()
        except Exception as e:
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values (%s,%s,%s,%s,1);',(req_type,DT_ID,API_ID,value)
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values ('+ req_type +','+ str(DT_ID)+','+str(API_ID)+','+str(value)+',0);'
            print("except: insertDataTbl ", str(e))
    
    def getSubscriptionInfo(self,sub_type):
        connection = self.get_db_connection()
        connection.row_factory = sqlite3.Row
        cur = connection.cursor()
        if sub_type == "i": #i = internal subs, e = external
            cur.execute('select * from subs_internal_tbl where status=1;')
        else:
            cur.execute('select * from subs_external_tbl where status=1;')
        results = cur.fetchall()
        #result = cur.fetchone()
        connection.close()
        #url = self.readDB()
        #print(len(result))
        #for r in result:
            #url = r
        #print(result)
        return results

    def addDTDetails(self,dt_id,dt_type,dt_url):
        try:
            connection = self.get_db_connection()
            cur = connection.cursor()
            cur.execute('insert into dt_details_tbl (DT_ID,type,url,status) values ('+ str(dt_id)+',"'+str(dt_type)+'","'+dt_url+'",1);')
            connection.commit()
            connection.close()
        except Exception as e:
            print("except: addExternalSub ", str(e))

    def addExternalSub(self,req_type,DT_ID,API_ID,url,ex_dt_url):
        try:
            connection = self.get_db_connection()
            cur = connection.cursor()
            cur.execute('insert into subs_external_tbl (direction,req_type,DT_ID,API_ID,url,ex_dt_url,status) values ("to","'+req_type+'",'+ str(DT_ID)+','+str(API_ID)+',"'+url+'","'+ex_dt_url+'",1);')
            connection.commit()
            connection.close()
        except Exception as e:
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values (%s,%s,%s,%s,1);',(req_type,DT_ID,API_ID,value)
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values ('+ req_type +','+ str(DT_ID)+','+str(API_ID)+','+str(value)+',0);'
            print("except: addExternalSub ", str(e))

    def getCurrentConnectionCount(self):
        allRows = self.readDB('select count(*) as con_count from subs_external_tbl where status=1;')
        return allRows

    
    def addInternalSub(self,req_type,DT_ID,API_ID,url,formula_position):
        try:
            connection = self.get_db_connection()
            cur = connection.cursor()
            cur.execute('insert into subs_internal_tbl (direction,req_type,DT_ID,API_ID,url,formula_position,status) values ("from","'+req_type+'",'+ str(DT_ID)+','+str(API_ID)+',"'+url+'",'+ str(formula_position)+',1);')
            connection.commit()
            connection.close()
        except Exception as e:
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values (%s,%s,%s,%s,1);',(req_type,DT_ID,API_ID,value)
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values ('+ req_type +','+ str(DT_ID)+','+str(API_ID)+','+str(value)+',0);'
            print("except: addInternalSub ", str(e))

    def getInternalGETSubs(self):
        allRows = self.readDB('select * from subs_internal_tbl where req_type="GET" and status=1;')
        return allRows

    def getExternalPOSTSubs(self):
        allRows = self.readDB('select * from subs_external_tbl where req_type="POST" and status=1;')
        return allRows
    
    def getvaluesToCalculate(self,DT_ID,API_ID):
        connection = self.get_db_connection()
        connection.row_factory = sqlite3.Row
        cur = connection.cursor()
        cur.execute('select * from data_tbl where DT_ID='+ str(DT_ID)+' and API_ID = '+str(API_ID)+' and used = 0 and status=1 LIMIT 1;')
        results = cur.fetchall()
        connection.close()
        return results

    def updateDataTable(self,id):
        try:
            connection = self.get_db_connection()
            cur = connection.cursor()
            cur.execute('update data_tbl set used = 1 where id = '+str(id)+';')
            #cur.execute('insert into subs_internal_tbl (direction,req_type,DT_ID,API_ID,url,formula_position,status) values ("from","'+req_type+'",'+ str(DT_ID)+','+str(API_ID)+',"'+url+'",'+ str(formula_position)+',1);')
            connection.commit()
            connection.close()
        except Exception as e:
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values (%s,%s,%s,%s,1);',(req_type,DT_ID,API_ID,value)
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values ('+ req_type +','+ str(DT_ID)+','+str(API_ID)+','+str(value)+',0);'
            print("except: updateDataTable ", str(e))
    
    def addFormulaCalculation(self,formula,value):
        for_id = 0
        formula = "formula"
        try:
            connection = self.get_db_connection()
            cur = connection.cursor()
            cur.execute('INSERT INTO formula_cal_tbl (calculated,status) VALUES ('+str(value)+',1);')
            for_id = cur.lastrowid
            connection.commit()
            connection.close()
            return for_id
        except Exception as e:
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values (%s,%s,%s,%s,1);',(req_type,DT_ID,API_ID,value)
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values ('+ req_type +','+ str(DT_ID)+','+str(API_ID)+','+str(value)+',0);'
            print("except: addFormulaCalculation ", str(e))
            return -1
    
    def addDTGenData(self,for_id,val_pos,value):
        try:
            connection = self.get_db_connection()
            cur = connection.cursor()
            cur.execute('INSERT INTO data_dt_gen_tbl (formula_cal_id,val_pos,value,status) VALUES ('+str(for_id)+','+str(val_pos)+','+str(value)+',1);')
            connection.commit()
            connection.close()
        except Exception as e:
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values (%s,%s,%s,%s,1);',(req_type,DT_ID,API_ID,value)
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values ('+ req_type +','+ str(DT_ID)+','+str(API_ID)+','+str(value)+',0);'
            print("except: addDTGenData ", str(e))
    
    def addCalValueData(self,for_id,val_pos,value,source):
        try:
            connection = self.get_db_connection()
            cur = connection.cursor()
            cur.execute('INSERT INTO cal_data_tbl (formula_cal_id,source,val_pos,value,status) VALUES ('+str(for_id)+',"'+str(source)+'",'+str(val_pos)+','+str(value)+',1);')
            connection.commit()
            connection.close()
        except Exception as e:
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values (%s,%s,%s,%s,1);',(req_type,DT_ID,API_ID,value)
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values ('+ req_type +','+ str(DT_ID)+','+str(API_ID)+','+str(value)+',0);'
            print("except: addCalValueData ", str(e))

    def getSampleDataforGraph(self):
        allRows = self.readDB('select id,value from data_tbl where status=1;')
        return allRows
    
    def getFormulaCalTbl(self):
        allRows = self.readDB('select id,calculated from formula_cal_tbl where calculated != -1111111.0 and status=1;')
        return allRows

    def getDataSentTbl(self):
        allRows = self.readDB('select id,value from data_sent_tbl where status=1;')
        return allRows

    def getQoSDataForDT(self):
        allRows = self.readDB('select DT_ID,max(elapsed_time),min(elapsed_time) from qos_tbl where status=1 GROUP BY DT_ID;')
        return allRows

    def insertDataSentTbl(self,req_type,DT_ID,API_ID,value):
        qu = ""
        try:
            connection = self.get_db_connection()
            cur = connection.cursor()
            qu = 'insert into data_sent_tbl (req_type,reciever_DT_ID,API_ID,value,status) values ("'+ req_type +'",'+ str(DT_ID)+','+str(API_ID)+','+str(value)+',1);'
            cur.execute('insert into data_sent_tbl (req_type,reciever_DT_ID,API_ID,value,status) values ("'+ req_type +'","'+ str(DT_ID)+'",'+str(API_ID)+','+str(value)+',1);')
            connection.commit()
            connection.close()
        except Exception as e:
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values (%s,%s,%s,%s,1);',(req_type,DT_ID,API_ID,value)
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values ('+ req_type +','+ str(DT_ID)+','+str(API_ID)+','+str(value)+',0);'
            print("except: insertDataSentTbl ", qu)
    
    def insertQoSTbl(self,DT_ID,API_ID,elapsed_time):
        qu = ""
        try:
            connection = self.get_db_connection()
            cur = connection.cursor()
            #qu = 'insert into data_sent_tbl (req_type,reciever_DT_ID,API_ID,value) values ("'+ req_type +'",'+ str(DT_ID)+','+str(API_ID)+','+str(value)+');'
            cur.execute('insert into qos_tbl (DT_ID,API_ID,elapsed_time,status) values ('+ str(DT_ID)+','+str(API_ID)+','+str(elapsed_time)+',1);')
            connection.commit()
            connection.close()
        except Exception as e:
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values (%s,%s,%s,%s,1);',(req_type,DT_ID,API_ID,value)
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values ('+ req_type +','+ str(DT_ID)+','+str(API_ID)+','+str(value)+',0);'
            print("except: insertQoSTbl ", str(e))

    def getQoSTbl(self):
        allRows = self.readDB('select DT_ID,round(avg(elapsed_time),4) as avg_time from qos_tbl  where status=1 GROUP BY DT_ID;')
        return allRows

    def getConnectedDTs(self):
        allRows = self.readDB('select DISTINCT DT_ID from data_tbl where status=1;')
        return allRows
    
    def getConnectedQoSDTs(self):
        allRows = self.readDB('select DISTINCT DT_ID from qos_tbl where status=1;')
        return allRows
    
    def getReputationAttackDTs(self):
        allRows = self.readDB('select DISTINCT attack_DT_ID from reputation_attack_config_tbl where status=1;')
        return allRows
    
    def getReputationAttackConfiguration(self,attack_DT_ID):
        allRows = self.readDB('select * from reputation_attack_config_tbl where attack_DT_ID = '+ str(attack_DT_ID)+' and status=1 order by created desc;')
        return allRows
    
    def getFinalValueTbl(self):
        allRows = self.readDB('select  DT_ID,data_type,stdev_value,min,max,avg from final_value_tbl where status=1;')
        return allRows
    
    def getAllValuesFromDT(self,DT_ID):
        q = 'select value from data_tbl where DT_ID='+ str(DT_ID)+' and status=1;'
        #print(q)
        allRows = self.readDB('select value from data_tbl where DT_ID='+ str(DT_ID)+' and status=1;')
        return allRows
    
    def getQoSFromDT(self,DT_ID):
        allRows = self.readDB('select elapsed_time from qos_tbl where DT_ID='+ str(DT_ID)+' and status=1;')
        return allRows

    def addFinalValueTbl(self,DT_ID,data_type,stdev_value,min,max,avg):
        try:
            connection = self.get_db_connection()
            cur = connection.cursor()
            #qu = 'insert into data_sent_tbl (req_type,reciever_DT_ID,API_ID,value) values ("'+ req_type +'",'+ str(DT_ID)+','+str(API_ID)+','+str(value)+');'
            cur.execute('insert into final_value_tbl (DT_ID,data_type,stdev_value,min,max,avg,status) values ('+ str(DT_ID)+',"'+ str(data_type)+'",'+str(stdev_value)+','+ str(min)+','+ str(max)+','+ str(avg)+',1);')
            connection.commit()
            connection.close()
        except Exception as e:
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values (%s,%s,%s,%s,1);',(req_type,DT_ID,API_ID,value)
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values ('+ req_type +','+ str(DT_ID)+','+str(API_ID)+','+str(value)+',0);'
            print("except: addFinalValueTbl ", str(e))

    def addStdevValue(self,DT_ID,stdev_value):
        try:
            connection = self.get_db_connection()
            cur = connection.cursor()
            #qu = 'insert into data_sent_tbl (req_type,reciever_DT_ID,API_ID,value) values ("'+ req_type +'",'+ str(DT_ID)+','+str(API_ID)+','+str(value)+');'
            cur.execute('insert into stdev_tbl (DT_ID,stdev_value,status) values ('+ str(DT_ID)+','+str(stdev_value)+',1);')
            connection.commit()
            connection.close()
        except Exception as e:
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values (%s,%s,%s,%s,1);',(req_type,DT_ID,API_ID,value)
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values ('+ req_type +','+ str(DT_ID)+','+str(API_ID)+','+str(value)+',0);'
            print("except: addStdevValue ", str(e))

    def addQoSStdevValue(self,DT_ID,stdev_value):
        try:
            connection = self.get_db_connection()
            cur = connection.cursor()
            #qu = 'insert into data_sent_tbl (req_type,reciever_DT_ID,API_ID,value) values ("'+ req_type +'",'+ str(DT_ID)+','+str(API_ID)+','+str(value)+');'
            cur.execute('insert into stdev_qos_tbl (DT_ID,stdev_value,status) values ('+ str(DT_ID)+','+str(stdev_value)+',1);')
            connection.commit()
            connection.close()
        except Exception as e:
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values (%s,%s,%s,%s,1);',(req_type,DT_ID,API_ID,value)
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values ('+ req_type +','+ str(DT_ID)+','+str(API_ID)+','+str(value)+',0);'
            print("except: addStdevValue ", str(e))
    
    def getStdValues(self):
        allRows = self.readDB('select * from stdev_tbl where status=1;')
        return allRows

    def getQoSStdValues(self):
        allRows = self.readDB('select * from stdev_qos_tbl where status=1;')
        return allRows

    def getStdValuesFromDT(self,DT_ID):
        allRows = self.readDB('select stdev_value from stdev_tbl where DT_ID='+ str(DT_ID)+' and status=1;')
        return allRows

    def getQoSStdValuesFromDT(self,DT_ID):
        allRows = self.readDB('select stdev_value from stdev_qos_tbl where DT_ID='+ str(DT_ID)+' and status=1;')
        return allRows

    def getFormulaValuePositions(self):
        allRows = self.readDB('select DISTINCT val_pos from cal_data_tbl where source = "e" and status=1;')
        return allRows
    
    def getFormulaValuesByPos(self,pos):
        allRows = self.readDB('select formula_cal_id,value from cal_data_tbl where val_pos='+str(pos)+' and status=1;')
        return allRows
    
    def getAllTables(self):
        allRows = self.readDB('SELECT name FROM sqlite_schema WHERE type ="table" AND name NOT LIKE "sqlite_%";')
        return allRows

    def saveDataAsCSV(self,dt_id):
        try:
            curr_dt=datetime.now()
            ts = int(round(curr_dt.timestamp()))
            save_location = "csv/"
            if not os.path.isdir(save_location):
                os.makedirs(save_location)
            allTables = self.getAllTables()
            for tbl in allTables:
                filename = str(dt_id)+"_"+tbl[0]+"_"+str(ts)+".csv"
                conn = self.get_db_connection()
                cursor = conn.cursor()
                data = pd.read_sql('select * from '+ tbl[0],conn)
                data.to_csv(save_location+filename,index=False)
            return True
        except Exception as e:
            print("except: saveDataAsCSV ", str(e))
            return False
    
    def addTrendResults(self,DT_ID,rec_type,trend_result):
        try:
            connection = self.get_db_connection()
            cur = connection.cursor()
            cur.execute('insert into trend_analysis_tbl (DT_ID,type,trend,h ,p ,z ,tau ,s ,var_s ,slope ,intercept,status) values ('+ str(DT_ID)+',"'+str(rec_type)+'","'+trend_result.trend+'",'+str(trend_result.h)+','+str(trend_result.p)+' ,'+str(trend_result.z)+' ,'+str(trend_result.Tau)+' ,'+str(trend_result.s)+' ,'+str(trend_result.var_s)+',"'+str(trend_result.slope)+'" ,'+str(trend_result.intercept)+',1);')
            connection.commit()
            connection.close()
        except Exception as e:
            print("except: addTrendResults ", str(e))

    def updateStatusOfUsedValues(self,iteration_counter):
        try:
            connection = self.get_db_connection()
            cur = connection.cursor()
            cur.execute('update qos_tbl set status ='+str(iteration_counter)+' where status = 1;')
            cur.execute('update trend_analysis_tbl set status ='+str(iteration_counter)+' where status = 1;')
            cur.execute('update stdev_tbl set status ='+str(iteration_counter)+' where status = 1;')
            cur.execute('update final_value_tbl set status ='+str(iteration_counter)+' where status = 1;')
            cur.execute('update stdev_qos_tbl set status ='+str(iteration_counter)+' where status = 1;')
            cur.execute('update data_tbl set status ='+str(iteration_counter)+' where status = 1;')
            cur.execute('update data_sent_tbl set status ='+str(iteration_counter)+' where status = 1;')
            cur.execute('update data_dt_gen_tbl set status ='+str(iteration_counter)+' where status = 1;')
            cur.execute('update cal_data_tbl set status ='+str(iteration_counter)+' where status = 1;')
            cur.execute('update formula_cal_tbl set status ='+str(iteration_counter)+' where status = 1;')
            #cur.execute('insert into subs_internal_tbl (direction,req_type,DT_ID,API_ID,url,formula_position,status) values ("from","'+req_type+'",'+ str(DT_ID)+','+str(API_ID)+',"'+url+'",'+ str(formula_position)+',1);')
            connection.commit()
            connection.close()
        except Exception as e:
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values (%s,%s,%s,%s,1);',(req_type,DT_ID,API_ID,value)
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values ('+ req_type +','+ str(DT_ID)+','+str(API_ID)+','+str(value)+',0);'
            print("except: updateDataTable ", str(e))
    
    def addAttackConfiguration(self,attack_dt_id,strength,attack,attack_type):
        try:
            connection = self.get_db_connection()
            cur = connection.cursor()
            cur.execute("insert into reputation_attack_config_tbl (attack_DT_ID,strength,attack,type,status) values ('"+ attack_dt_id +"','"+strength+"','"+attack+"','"+attack_type+"',1)")
            connection.commit()
            connection.close()
        except Exception as e:
            print("except: addAttackConfiguration ", str(e))
    
    def updateSubs(self,tbl_name,dt_id):
        try:
            connection = self.get_db_connection()
            cur = connection.cursor()
            if tbl_name == 'i':
                cur.execute('update subs_internal_tbl set status = -1 where DT_ID = '+str(dt_id)+';')
            else:
                cur.execute('update subs_external_tbl set status = -1 where DT_ID = '+str(dt_id)+';')
            connection.commit()
            connection.close()
        except Exception as e:
            print("except: updateSubs ", str(e))

    def getFormulaPositions(self,dt_id):
        allRows = self.readDB('SELECT formula_position FROM subs_internal_tbl where dt_id='+str(dt_id)+' and status=1;')
        return allRows


    




