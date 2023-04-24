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

        cur.execute("insert into trans_tbl (trans) values ('Database created')")

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
        allRows = self.readDB('select * from trans_tbl')
        return allRows
    
    def getAllDataTbl(self):
        allRows = self.readDB("select * from data_tbl;")
        return allRows

    def addTransaction(self,content):
        try:
            connection = self.get_db_connection()
            cur = connection.cursor()
            cur.execute("insert into trans_tbl (trans) values ('"+ content +"')")
            connection.commit()
            connection.close()
        except Exception as e:
            print("except: addTransaction ", str(e))
    
    def insertDataTbl(self,req_type,DT_ID,API_ID,value):
        try:
            connection = self.get_db_connection()
            cur = connection.cursor()
            cur.execute('insert into data_tbl (req_type,DT_ID,API_ID,value,used) values ("'+ req_type +'",'+ str(DT_ID)+','+str(API_ID)+','+str(value)+',0);')
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
            cur.execute('insert into dt_details_tbl (DT_ID,type,url) values ('+ str(dt_id)+',"'+str(dt_type)+'","'+dt_url+'");')
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
        cur.execute('select * from data_tbl where DT_ID='+ str(DT_ID)+' and API_ID = '+str(API_ID)+' and used = 0 LIMIT 1;')
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
            cur.execute('INSERT INTO formula_cal_tbl (calculated) VALUES ('+str(value)+');')
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
            cur.execute('INSERT INTO data_dt_gen_tbl (formula_cal_id,val_pos,value) VALUES ('+str(for_id)+','+str(val_pos)+','+str(value)+');')
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
            cur.execute('INSERT INTO cal_data_tbl (formula_cal_id,source,val_pos,value) VALUES ('+str(for_id)+',"'+str(source)+'",'+str(val_pos)+','+str(value)+');')
            connection.commit()
            connection.close()
        except Exception as e:
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values (%s,%s,%s,%s,1);',(req_type,DT_ID,API_ID,value)
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values ('+ req_type +','+ str(DT_ID)+','+str(API_ID)+','+str(value)+',0);'
            print("except: addCalValueData ", str(e))

    def getSampleDataforGraph(self):
        allRows = self.readDB('select id,value from data_tbl;')
        return allRows
    
    def getFormulaCalTbl(self):
        allRows = self.readDB('select id,calculated from formula_cal_tbl where calculated != -1111111.0;')
        return allRows

    def getDataSentTbl(self):
        allRows = self.readDB('select id,value from data_sent_tbl;')
        return allRows

    def getQoSDataForDT(self):
        allRows = self.readDB('select DT_ID,max(elapsed_time),min(elapsed_time) from qos_tbl GROUP BY DT_ID;')
        return allRows

    def insertDataSentTbl(self,req_type,DT_ID,API_ID,value):
        qu = ""
        try:
            connection = self.get_db_connection()
            cur = connection.cursor()
            qu = 'insert into data_sent_tbl (req_type,reciever_DT_ID,API_ID,value) values ("'+ req_type +'",'+ str(DT_ID)+','+str(API_ID)+','+str(value)+');'
            cur.execute('insert into data_sent_tbl (req_type,reciever_DT_ID,API_ID,value) values ("'+ req_type +'","'+ str(DT_ID)+'",'+str(API_ID)+','+str(value)+');')
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
            cur.execute('insert into qos_tbl (DT_ID,API_ID,elapsed_time) values ('+ str(DT_ID)+','+str(API_ID)+','+str(elapsed_time)+');')
            connection.commit()
            connection.close()
        except Exception as e:
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values (%s,%s,%s,%s,1);',(req_type,DT_ID,API_ID,value)
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values ('+ req_type +','+ str(DT_ID)+','+str(API_ID)+','+str(value)+',0);'
            print("except: insertQoSTbl ", str(e))

    def getQoSTbl(self):
        allRows = self.readDB('select DT_ID,round(avg(elapsed_time),4) as avg_time from qos_tbl GROUP BY DT_ID;')
        return allRows

    def getConnectedDTs(self):
        allRows = self.readDB('select DISTINCT DT_ID from data_tbl;')
        return allRows
    
    def getConnectedQoSDTs(self):
        allRows = self.readDB('select DISTINCT DT_ID from qos_tbl;')
        return allRows
    
    def getFinalValueTbl(self):
        allRows = self.readDB('select  DT_ID,data_type,stdev_value,min,max,avg from final_value_tbl;')
        return allRows
    
    def getAllValuesFromDT(self,DT_ID):
        q = 'select value from data_tbl where DT_ID='+ str(DT_ID)+';'
        #print(q)
        allRows = self.readDB('select value from data_tbl where DT_ID='+ str(DT_ID)+';')
        return allRows
    
    def getQoSFromDT(self,DT_ID):
        allRows = self.readDB('select elapsed_time from qos_tbl where DT_ID='+ str(DT_ID)+';')
        return allRows

    def addFinalValueTbl(self,DT_ID,data_type,stdev_value,min,max,avg):
        try:
            connection = self.get_db_connection()
            cur = connection.cursor()
            #qu = 'insert into data_sent_tbl (req_type,reciever_DT_ID,API_ID,value) values ("'+ req_type +'",'+ str(DT_ID)+','+str(API_ID)+','+str(value)+');'
            cur.execute('insert into final_value_tbl (DT_ID,data_type,stdev_value,min,max,avg) values ('+ str(DT_ID)+',"'+ str(data_type)+'",'+str(stdev_value)+','+ str(min)+','+ str(max)+','+ str(avg)+');')
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
            cur.execute('insert into stdev_tbl (DT_ID,stdev_value) values ('+ str(DT_ID)+','+str(stdev_value)+');')
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
            cur.execute('insert into stdev_qos_tbl (DT_ID,stdev_value) values ('+ str(DT_ID)+','+str(stdev_value)+');')
            connection.commit()
            connection.close()
        except Exception as e:
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values (%s,%s,%s,%s,1);',(req_type,DT_ID,API_ID,value)
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values ('+ req_type +','+ str(DT_ID)+','+str(API_ID)+','+str(value)+',0);'
            print("except: addStdevValue ", str(e))
    
    def getStdValues(self):
        allRows = self.readDB('select * from stdev_tbl;')
        return allRows

    def getQoSStdValues(self):
        allRows = self.readDB('select * from stdev_qos_tbl;')
        return allRows

    def getStdValuesFromDT(self,DT_ID):
        allRows = self.readDB('select stdev_value from stdev_tbl where DT_ID='+ str(DT_ID)+';')
        return allRows

    def getQoSStdValuesFromDT(self,DT_ID):
        allRows = self.readDB('select stdev_value from stdev_qos_tbl where DT_ID='+ str(DT_ID)+';')
        return allRows

    def getFormulaValuePositions(self):
        allRows = self.readDB('select DISTINCT val_pos from cal_data_tbl where source = "e";')
        return allRows
    
    def getFormulaValuesByPos(self,pos):
        allRows = self.readDB('select formula_cal_id,value from cal_data_tbl where val_pos='+str(pos)+';')
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
            cur.execute('insert into trend_analysis_tbl (DT_ID,type,trend,h ,p ,z ,tau ,s ,var_s ,slope ,intercept) values ('+ str(DT_ID)+',"'+str(rec_type)+'","'+trend_result.trend+'",'+str(trend_result.h)+','+str(trend_result.p)+' ,'+str(trend_result.z)+' ,'+str(trend_result.Tau)+' ,'+str(trend_result.s)+' ,'+str(trend_result.var_s)+',"'+str(trend_result.slope)+'" ,'+str(trend_result.intercept)+');')
            connection.commit()
            connection.close()
        except Exception as e:
            print("except: addTrendResults ", str(e))

    



