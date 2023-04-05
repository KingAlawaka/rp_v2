import random


class Simulation:
    def __init__(self,num_iterations,num_DTs,CDT_goal,dt_type):
        self.num_iterations = num_iterations
        self.num_DTs = num_DTs
        self.CDT_goal = CDT_goal
        self.dt_type = dt_type
    
    def generateFormula(self):
        numVariables = random.randint(2,int(self.num_DTs/3))
        #print(numVariables)
        operatorList = ['+','-','/','*']
        operators = []
        for x in range(numVariables-1):
            operators.append(operatorList[random.randint(0,3)])
        #print(operators)
        if numVariables == 2:
            num_internal_variable = 1
            num_external_variable = 1
        else:
            num_external_variable = random.randint(1,numVariables-1)
            num_internal_variable = numVariables - num_external_variable
        #print(num_external_variable)
        #print(num_internal_variable)
        formula = ['f','=']
        count = 0
        # internal variables = $ 
        # external variable = @
        nInternal = num_internal_variable
        nExternal = num_external_variable
        for x in operators:
            if count == 0:
                formula.append("$")
                nInternal = nInternal - 1
            formula.append(x)
            if nExternal > 0:
                formula.append("@")
                nExternal = nExternal -1
            else:
                formula.append("$")
            count = count + 1
        #print(formula)
        #print(num_external_variable)
        #print(num_internal_variable)
        #print("_____")
        externalVariableLocations = []
        for i in range(num_external_variable):
            #print(i)
            if len(externalVariableLocations)==0:
                externalVariableLocations.append(i+4)
            else:
                externalVariableLocations.append(i+4+i)
        return numVariables,num_internal_variable,num_external_variable,formula,externalVariableLocations #int,int,int,list,list
    
    '''
    normal DTs will generate one random value range
    malicious DTs will randomly generate value using same logic in changing DTs
    Change DTs will generate upto 3 value ranges and use one of them to generate value 
    '''
    def generateRandomValueRanges(self):
        randomValueRanges = []

        if self.dt_type == 'c':
            num_of_ranges = random.randint(1,3)
            for x in range (num_of_ranges):
                min = random.randint(1,10)
                max = random.randint(min,min+10)
                temp_range = [min,max]
                randomValueRanges.append(temp_range)
        elif self.dt_type == 'n':
            min = random.randint(1,10)
            max = random.randint(min,min+10)
            temp_range = [min,max]
            randomValueRanges.append(temp_range)
        return randomValueRanges
    
    def generateValue(self,min,max):
        return random.randint(min,max)

    '''
    If DT have external variables that DT will expose to get values from other DTs
    If not based on the exposeServices() it will decide whether to provide values to other DTs
    '''
    def exposeServices(self):
        return random.randint(0,1)
    
    '''
    Checking for fixing API vulnerbilities.
    For normal DT there is a 
    '''
    def fixAPISecurityVulnerbilities(self):
        v = random.randint(1,4) 

        if self.dt_type == 'n':
            if v in [2,3,4]:
                return True
        elif self.dt_type == 'c':
            if v in [1,3]:
                return True
        else:
            if v == 2:
                return True
        
    

def value(c):
    if c == '$':
        return 1
    else:
        return 2    

def calculatevalues(v1,v2,operator):
    if operator == '+':
        total = v1 + v2               
    elif operator == '-':
        total = v1 - v2            
    elif operator == '*':
        total = v1 * v2          
    else:
        total = v1 / v2
    return total
 
def main():
    # sim = Simulation(10,12,'max','n')
    # numVariables,num_internal_variable,num_external_variable,formula = sim.generateFormula() #int,int,int,list
    # print(str(numVariables)+"  "+str(num_internal_variable)+"  "+str(num_external_variable)+"  "+str(formula))
    # externalVariableLocations = []
    # for i in range(num_external_variable):
    #     if len(externalVariableLocations)==0:
    #         externalVariableLocations.append(i+4)
    #     else:
    #         externalVariableLocations.append(i+4+i)
    # print(externalVariableLocations)

    # valueRanges = sim.generateRandomValueRanges()
    # print(valueRanges)
    # for i in valueRanges:
    #     print("gen value" + str(sim.generateValue(i[0],i[1])))
    # print(sim.exposeServices())


    # sim = Simulation(10,12,'max','c')
    # numVariables,num_internal_variable,num_external_variable,formula = sim.generateFormula() #int,int,int,list
    # print(str(numVariables)+"  "+str(num_internal_variable)+"  "+str(num_external_variable)+"  "+str(formula))
    # externalVariableLocations = []
    # for i in range(num_external_variable):
    #     #print(i)
    #     if len(externalVariableLocations)==0:
    #         externalVariableLocations.append(i+4)
    #     else:
    #         externalVariableLocations.append(i+4+i)
    # print(externalVariableLocations)

    # valueRanges = sim.generateRandomValueRanges()
    # print(valueRanges)
    # print("-----")
    # selectRange = random.randint(0,len(valueRanges)-1)
    # print(selectRange)
    # print(valueRanges[selectRange][0],valueRanges[selectRange][1])
    # for i in valueRanges:
    #     print("gen value" + str(sim.generateValue(valueRanges[selectRange][0],valueRanges[selectRange][1])))
    # #for i in range(5):
    # print(sim.exposeServices())

    # for i in range(12):
    #     sim = Simulation(10,21,'max','c')
    #     numVariables,num_internal_variable,num_external_variable,formula = sim.generateFormula() #int,int,int,list
    #     print(str(numVariables)+"  "+str(num_internal_variable)+"  "+str(num_external_variable)+"  "+str(formula))
    #     externalVariableLocations = []
    #     for i in range(num_external_variable):
    #         #print(i)
    #         if len(externalVariableLocations)==0:
    #             externalVariableLocations.append(i+4)
    #         else:
    #             externalVariableLocations.append(i+4+i)
    #     print(externalVariableLocations)

    formula = [
    'f',
    '=',
    '$',
    '+',
    '@',
    '+',
    '@',
    '-',
    '$',
    ]
    
    total = 0
    for i in range(2, len(formula) - 1):
        if i == 2:
            total = calculatevalues(value(formula[i]),value(formula[i + 2]),formula[i + 1])         
        if i >= 5:
            if i % 2 != 0:
                total = calculatevalues(total,value(formula[i + 1]),formula[i])

    print (total)

        



if __name__ == '__main__':
    args = ""
    main()




