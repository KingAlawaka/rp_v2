from dt_db import DBHelper
import configparser
from dt_simulation_helper import Simulation
import random
import statistics
import numpy as np
import pymannkendall as mk
import pandas as pd

class DTLogic:
    def __init__(self,dbHelper,num_iterations,num_DTs,CDT_goal,dt_type,rand_seed):
        self.dbHelper = dbHelper
        self.config = configparser.ConfigParser()
        self.config.read('environment_config.ini')
        self.simHelper = Simulation(num_iterations,num_DTs,CDT_goal,dt_type,rand_seed)
        self.dt_type = dt_type
        self.num_iterations =num_iterations
        self.num_DTs = num_DTs
        self.CDT_goal = CDT_goal
        self.dt_id = -1
        self.valueRanges = self.simHelper.generateRandomValueRanges()
        random.seed(rand_seed)
        self.reputation_attack = False
        self.reputation_attack_strength = 1
        pass

    def enableReputationAttacks(self,flag):
        self.reputation_attack = flag

    def setReputationAttackStrength(self,strength):
        self.reputation_attack_strength=strength
    
    def setDTID(self,dt_id):
        self.dt_id=dt_id

    def getInternalSubs(self):
        subList = self.dbHelper.getSubscriptionInfo("i")
        subs = [
            {
                "id": sub[0],
                "direction": sub[1],
                "req_type": sub[2],
                "DT_ID": sub[3],
                "API_ID": sub[4],
                "url": sub[5],
                "formula_position": sub[6]
            } for sub in subList]
        return subs
    
    def getExternalSubs(self):
        subList = self.dbHelper.getSubscriptionInfo("e")
        subs = [
            {
                "id": sub[0],
                "direction": sub[1],
                "req_type": sub[2],
                "DT_ID": sub[3],
                "API_ID": sub[4],
                "url": sub[5]
            } for sub in subList]
        return subs
    
    def findMax(self,l):
        temp_max = l[0]
        for n in l:
            if n > temp_max:
                temp_max = n
        return temp_max

    def findMin(self,l):
        temp_min = l[0]
        for n in l:
            if n < temp_min:
                temp_min = n
        return temp_min

    def generateValue(self):
        print("DT type: ",self.dt_type)
        normalDT_value_selection_limit = int(self.config['sim_parameters']['normalDT_value_selection_limit'])
        changingDT_value_selection_limit = int(self.config['sim_parameters']['changingDT_value_selection_limit'])
        if self.dt_type == "m":
            min = random.randint(1,10)
            max = random.randint(min,min+10)
            value = random.randint(min,max)
        else:
            if len(self.valueRanges) == 1:
                valueList = []
                for i  in range(normalDT_value_selection_limit):
                    valueList.append(self.simHelper.generateValue(self.valueRanges[0][0],self.valueRanges[0][1]))
                if len(valueList) > 0:
                    if self.CDT_goal == "max":
                        value = self.findMax(valueList)
                    else:
                        value = self.findMin(valueList)
                else:
                    value = -1
            elif len(self.valueRanges) > 1:
                selectRange = random.randint(0,len(self.valueRanges)-1)
                valueList = []
                for i in range(changingDT_value_selection_limit):
                    valueList.append(self.simHelper.generateValue(self.valueRanges[selectRange][0],self.valueRanges[selectRange][1]))
                    #print(valueList)
                #print(valueList)
                if len(valueList)>0:
                    if self.CDT_goal == "max":
                        value = self.findMax(valueList)
                    else:
                        value = self.findMin(valueList)
                else:
                    value = -1
        return value

    def delayResponse(self):
        if self.dt_type == "c":
            v = random.randint(1,4) #1,4 no delay 2,3 delay
            if v== 1 or v==4:
                return False
            else:
                return True
        elif self.dt_type == "n":
            v = random.randint(1,4) #1,2,4 no delay 3 delay
            if v== 1 or v==4 or v == 2:
                return False
            else:
                return True
        else:
            return True

    def delayTime(self):
        m_min = int(self.config['sim_parameters']['m_min'])
        m_max = int(self.config['sim_parameters']['m_max'])
        c_min = int(self.config['sim_parameters']['c_min'])
        c_max = int(self.config['sim_parameters']['c_max'])
        n_min = int(self.config['sim_parameters']['n_min'])
        n_max = int(self.config['sim_parameters']['n_max'])
        if self.dt_type == "m":
            return random.randint(m_min,m_max)
        elif self.dt_type == "c":
            return random.randint(c_min,c_max)
        else:
            return random.randint(n_min,n_max)

    def value(self,c):
        if c == '$':
            return self.generateValue()
        else:
            return     

    def calculatevalues(self,v1,v2,operator):
        if operator == '+':
            total = v1 + v2               
        elif operator == '-':
            total = v1 - v2            
        elif operator == '*':
            total = v1 * v2          
        else:
            total = v1 / v2
        return total

    def createResponseHeaders(self,resObj):
        # TODO change it if want to fix api issues all the time
        alwaysTrue = False #for testing purposes and override the random selection, use 'and' to run complete malicious API behaviour
        if self.simHelper.fixAPISecurityVulnerbilities() or alwaysTrue:
            resObj.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            resObj.headers['Content-Security-Policy'] = "default-src 'self'"
            resObj.headers['X-Content-Type-Options'] = 'nosniff'
            resObj.headers['X-Frame-Options'] = 'SAMEORIGIN'
            resObj.headers['X-XSS-Protection'] = '1; mode=block'
            resObj.headers['Server'] = 'ASD'
        return resObj
    
    def calculateStdev(self):
        try:
            connectedDTs = self.dbHelper.getConnectedDTs()
            for c in connectedDTs:
                #print(c[0])
                values = self.dbHelper.getAllValuesFromDT(c[0])
                val = []
                for v in  values:
                    val.append(v[0])
                #print(values[0]["value"])
                stdValue = round(statistics.stdev(val),3)
                # print("std values")
                # print(stdValue)
                # if(self.reputation_attack):
                #     stdValue = stdValue + 1
                # print(stdValue)
                self.dbHelper.addStdevValue(str(c[0]),stdValue)
                print("DT ID ", str(c[0])," STDEV ", str(stdValue))
        except Exception as e:
            print("calculateStdev ",str(e))
    
    def calculateQoSStdev(self):
        try:
            connectedDTs = self.dbHelper.getConnectedQoSDTs()
            for c in connectedDTs:
                #print(c[0])
                values = self.dbHelper.getQoSFromDT(c[0])
                val = []
                for v in  values:
                    val.append(v[0])
                #print(values[0]["value"])
                stdValue = round(statistics.stdev(val),3)
                # print("std values")
                # print(stdValue)
                # if(self.reputation_attack):
                #     stdValue = stdValue + 1
                # print(stdValue)
                self.dbHelper.addQoSStdevValue(str(c[0]),stdValue)
                print("QoS DT ID ", str(c[0])," STDEV ", str(stdValue))
        except Exception as e:
            print("calculateStdevQoS ",str(e))
    
    def generateFinalValues(self):
        try:
            qos_connectedDTs = self.dbHelper.getConnectedQoSDTs()
            connectedDTs = self.dbHelper.getConnectedDTs()
            getRepAttackDTs = self.dbHelper.getReputationAttackDTs()
            rep_attack_DT_IDs = []
            for a in getRepAttackDTs:
                rep_attack_DT_IDs.append(a[0])
            print(rep_attack_DT_IDs)
            resQoS = []
            for c in qos_connectedDTs:
                qos_values = self.dbHelper.getQoSFromDT(c[0])
                val = []
                for v in qos_values:
                    val.append(v[0])
                stdValue = round(statistics.stdev(val),4)
                avgQoS = round(statistics.mean(val),3)
                print(avgQoS)
                # print(getRepAttackDTs)
                # print(c[0])
                # print(c[0] in rep_attack_DT_IDs)
                if(self.reputation_attack and (c[0] in rep_attack_DT_IDs)):
                    rep_attack_config = self.dbHelper.getReputationAttackConfiguration(c[0])
                    print("inside rep attack")
                    print(rep_attack_config[0][3])
                    if (rep_attack_config[0][3] == 1):
                        diff = float(self.config['repattack']['qos_mid']) - avgQoS
                        if diff < 0:
                            # avgQoS = avgQoS - (diff * -1) - float(self.config['repattack']['qos_increment_factor'])
                            if rep_attack_config[0][2] == "sp":
                                avgQoS = float(self.config['repattack']['qos_mid']) + diff
                            else:
                                avgQoS = (diff * -1) + float(self.config['repattack']['qos_mid'])
                        else:
                            if rep_attack_config[0][2] == "sp":
                                avgQoS = float(self.config['repattack']['qos_mid']) - diff
                            else:
                                avgQoS = diff + float(self.config['repattack']['qos_mid'])
                    else:
                        diff = float(self.config['repattack']['qos_high']) - avgQoS
                        if diff < 0:
                            if rep_attack_config[0][2] == "sp":
                                avgQoS = diff  + float(self.config['repattack']['qos_high'])
                            else:
                                avgQoS = (diff * -1) + float(self.config['repattack']['qos_high'])
                        else:
                            if rep_attack_config[0][2] == "sp":
                                avgQoS =  float(self.config['repattack']['qos_high']) - diff 
                            else:
                                avgQoS = diff + float(self.config['repattack']['qos_high'])
                print(avgQoS)
                self.dbHelper.addFinalValueTbl(str(c[0]),'QoS',stdValue,str(min(val)),str(max(val)),str(avgQoS))
                # resQoS.append("DT_ID "+str(c[0])+" QoS STD: "+str(stdValue))
                # resQoS.append("DT_ID "+str(c[0])+" QoS min: "+str(min(val)))
                # resQoS.append("DT_ID "+str(c[0])+" QoS max: "+str(max(val)))
                # resQoS.append("DT_ID "+str(c[0])+" QoS avg: "+str(round(statistics.mean(val),3)))
            resDTValues = []
            for c in connectedDTs:
                dt_values = self.dbHelper.getAllValuesFromDT(c[0])
                val = []
                for v in dt_values:
                    val.append(v[0])
                stdValue = round(statistics.stdev(val),4)
                print(stdValue)
                # print(getRepAttackDTs)
                # print(c[0])
                # print(c[0] in getRepAttackDTs)
                if(self.reputation_attack and (c[0] in rep_attack_DT_IDs)):
                    rep_attack_config = self.dbHelper.getReputationAttackConfiguration(c[0])
                    print("inside rep attack")
                    print(rep_attack_config[0][3])
                    if (rep_attack_config[0][3] == 1):
                        diff = float(self.config['repattack']['value_mid']) - stdValue
                        if diff < 0:
                            if rep_attack_config[0][2] == "sp":
                                stdValue =  diff + float(self.config['repattack']['value_mid'])
                            else:
                                stdValue =  (diff * -1) + float(self.config['repattack']['value_mid'])
                        else:
                            if rep_attack_config[0][2] == "sp":
                                stdValue = float(self.config['repattack']['value_mid']) -  diff
                            else:
                                stdValue = float(self.config['repattack']['value_mid']) +  diff
                    else:
                        diff = float(self.config['repattack']['value_high']) - stdValue
                        if diff < 0:
                            if rep_attack_config[0][2] == "sp":
                                stdValue =  diff  + float(self.config['repattack']['value_high'])
                            else:
                                stdValue =  (diff * -1) + float(self.config['repattack']['value_high'])
                        else:
                            if rep_attack_config[0][2] == "sp":
                                stdValue =  float(self.config['repattack']['value_high']) - diff
                            else:
                                stdValue = diff + float(self.config['repattack']['value_high'])
                print(stdValue) 
                self.dbHelper.addFinalValueTbl(str(c[0]),'Values',stdValue,str(min(val)),str(max(val)),str(round(statistics.mean(val),3)))
                # resDTValues.append("DT_ID "+str(c[0])+" Val STD: "+str(stdValue))
                # resDTValues.append("DT_ID "+str(c[0])+" Val min: "+str(min(val)))
                # resDTValues.append("DT_ID "+str(c[0])+" Val max: "+str(max(val)))
                # resDTValues.append("DT_ID "+str(c[0])+" Val avg: "+str(round(statistics.mean(val),3)))
            
            formula_final_values = self.dbHelper.getFormulaCalTbl()
            temp = []
            res_formula_values=[]
            for v in formula_final_values:
                temp.append(v[1])
            stdValue = round(statistics.stdev(temp),4)
            self.dbHelper.addFinalValueTbl(self.dt_id,'Final',stdValue,str(min(temp)),str(max(temp)),str(round(statistics.mean(temp),3)))



            # res_formula_values.append("Final Val STD: "+str(stdValue))
            # res_formula_values.append("Final Val min: "+str(min(temp)))
            # res_formula_values.append("Final Val max: "+str(max(temp)))
            # res_formula_values.append("Final Val avg: "+str(round(statistics.mean(temp),3)))
            # print(resQoS)
            # print(resDTValues)
            # print(res_formula_values)
            print("Final Results created.")
            return "okay"
        except Exception as e:
            print("generateFinalValues ",str(e))
            return "Failed"
    
    def DT_evaluation(self):
        connectedDTs = self.dbHelper.getConnectedDTs()
        value_std_low_counter = 0
        value_std_mid_counter = 0
        value_std_high_counter = 0
        qos_std_low_counter = 0
        qos_std_mid_counter = 0
        qos_std_high_counter = 0

        std_low_mark = 2
        std_mid_mark = 5

        evaluation = ""
        for c in connectedDTs:
            #print(c[0])
            std_values = self.dbHelper.getStdValuesFromDT(c[0])
            qos_values = self.dbHelper.getStdValuesFromDT(c[0])
            val = []
            evaluation = " "
            for v in  std_values:
                if v[0] <= std_low_mark:
                    value_std_low_counter = value_std_low_counter + 1
                elif v[0] <= std_mid_mark:
                    value_std_mid_counter = value_std_mid_counter + 1
                else:
                    value_std_high_counter = value_std_high_counter +1
            
            for v in qos_values:
                if v[0] <= std_low_mark:
                    qos_std_low_counter = qos_std_low_counter + 1
                elif v[0] <= std_mid_mark:
                    qos_std_mid_counter = qos_std_mid_counter + 1
                else:
                    qos_std_high_counter = qos_std_high_counter +1
            
            evaluation = evaluation + "DT_ID: "+str(c[0])+" std value evaluation=> low: "+str(value_std_low_counter)+" mid: "+str(value_std_mid_counter)+" high: "+str(value_std_high_counter)
            evaluation = evaluation + "________________"
            evaluation = evaluation + "  DT_ID: "+str(c[0])+" QoS std value evaluation=> low: "+str(qos_std_low_counter)+" mid: "+str(qos_std_mid_counter)+" high: "+str(qos_std_high_counter)
            evaluation = evaluation + "________________"
        
        print("evaluation done")
            # stdValue = round(statistics.stdev(val),3)
            # dbHelper.addQoSStdevValue(str(c[0]),stdValue)
            # print("QoS DT ID ", str(c[0])," STDEV ", str(stdValue))
        return "okay"

    def trendAnalysisExDTData(self):
        try:
            conn = self.dbHelper.get_db_connection()
            cursor = conn.cursor()
            data = pd.read_sql('select * from data_tbl where value != -111111111.0;',conn)
            dts = data.DT_ID.unique()
            for dt in dts:
                temp_df = data[data['DT_ID'] == dt]
                result = mk.original_test(temp_df.value)
                self.dbHelper.addTrendResults(dt,"data_tbl",result)
        except Exception as e:
            print("trendAnalysisExDTData ",str(e))

    
