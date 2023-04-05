# network = [
# 	[1,3,2],
# 	[4,1,1],
# 	[2,1,3],
# 	[3,2,1],
# 	[3,5,1]
# 	]

# trust_score = [10,10,10,10,10]
# dep = [0,0,0,0,0]
# con = [[],[],[],[],[]]
# influence = 0.5
# dep_sec = [0,0,0,0,0]

# def calIn(t_score,hop_count):
#   return t_score  * influence * (1/hop_count)
  

# for i in network:
# 	if i[0] == 1:
# 		dep[0] = dep[0] + trust_score[i[1]-1] * i[2]
# 		con[0].append(i[1])
# 	elif i[0] == 2:
# 		dep[1] = dep[1] + trust_score[i[1]-1] * i[2]
# 		con[1].append(i[1])
# 	elif i[0] == 3:
# 		dep[2] = dep[2] + trust_score[i[1]-1] * i[2]
# 		con[2].append(i[1])
# 	elif i[0] == 4:
# 		dep[3] = dep[3] + trust_score[i[1]-1] * i[2]
# 		con[3].append(i[1])
# 	elif i[0] == 5:
# 		dep[4] = dep[4] + trust_score[i[1]-1] * i[2]
# 		con[4].append(i[1])

# completed = False
# print("____")
# for i in range(1,6):
#     print("For Main DT: ", i)
#     direct_connects = con[i-1]
#     print("Direct connections ", direct_connects)
#     iteration_count = 0
#     considered_dts = []
#     while (iteration_count != len(direct_connects)):
#         for c in direct_connects:
#             print("For Sub DT ",c, " getting sub connections: ")
#             sub_con = con[c-1]
#             print(sub_con)
#             sub_con_count = 0
#             while sub_con_count != len(sub_con):
#                 hop_count = 1
#                 for cc in sub_con:
#                     print("considering sub connected DT ",cc)
#                     if cc != i or cc in considered_dts:
#                         print("calculating sub connected DT ",cc," hop count ",hop_count)
#                         considered_dts.append(cc)
#                         print("considered DTs ",considered_dts)
#                         dep_sec[i-1] = dep_sec[i-1] + calIn(trust_score[cc-1],hop_count)

#                         next_level_DTs = con[cc-1]
#                         while 
#                     print("")
#                 hop_count += 1
#                 sub_con_count += 1
#         iteration_count += 1

#         # connect_count = 0
#         # temp_connects = con[c-1]
#         # while(connect_count != len())
        
#         # for c in direct_connects:
#         #     print(con[c-1])
#         #     considered_dts.append(c)
#         #     hop_count = 1
#         #     dts = con[c-1]
#         #     for cc in dts:
#         #         print(cc)
                
#         #         hop_count += 1
#         #         for ccc in con[cc-1]:
#         #             if ccc == i or ccc in direct_connects or ccc in direct_connects:
#         #                 break 
#     print("____")
		


# print(dep)
# print(con)
# print(dep_sec)

network = [
	[1,3,2],
	[4,1,1],
	[2,1,3],
	[3,2,1],
	[3,5,1]
	]

trust_score = [10,10,10,10,10]
dep = [0,0,0,0,0]
con = [[],[],[],[],[]]
influence = 0.5
dep_sec = [0,0,0,0,0]

def calIn(t_score,hop_count):
  return t_score  * influence * (1/hop_count)
  

for i in network:
	if i[0] == 1:
		dep[0] = dep[0] + trust_score[i[1]-1] * i[2]
		con[0].append(i[1])
	elif i[0] == 2:
		dep[1] = dep[1] + trust_score[i[1]-1] * i[2]
		con[1].append(i[1])
	elif i[0] == 3:
		dep[2] = dep[2] + trust_score[i[1]-1] * i[2]
		con[2].append(i[1])
	elif i[0] == 4:
		dep[3] = dep[3] + trust_score[i[1]-1] * i[2]
		con[3].append(i[1])
	elif i[0] == 5:
		dep[4] = dep[4] + trust_score[i[1]-1] * i[2]
		con[4].append(i[1])

completed = False
print("____")
for i in range(1,6):
    print("For Main DT: ", i)
    direct_connects = con[i-1]
    print("Direct connections ", direct_connects)
    iteration_count = 0
    considered_dts = []
    while (iteration_count != len(direct_connects)):
        for c in direct_connects:
            print("For direct DT ",c, " getting sub connections: ")
            considered_dts.append(c)
            sub_con = con[c-1]
            print(sub_con)
            sub_con_count = 0
            # if len(sub_con) == 0:
            #     break
            while sub_con_count != len(sub_con):
                hop_count = 1
                for cc in sub_con:
                    print("considering sub connected DT ",cc)

                    if cc != i or cc in considered_dts:
                        print("calculating sub connected DT ",cc," hop count ",hop_count)
                        considered_dts.append(cc)
                        print("considered DTs ",considered_dts)
                        dep_sec[i-1] = dep_sec[i-1] + calIn(trust_score[cc-1],hop_count)
                        hop_count += 1
                        next_level_DTs = con[cc-1]
                        next_level_DT_count = 0
                        while next_level_DT_count != len(next_level_DTs):
                            for d in next_level_DTs:
                                print("next level DT",d)
                                if d == i :
                                    print("stoping condition DT=I")
                                    continue
                                elif d in considered_dts:
                                    print("stoping condition DT in considering DT")
                                    continue
                                
                                next_level_DT_count += 1

                    print("sub_con_count",sub_con_count)
                    print("")
                    sub_con_count += 1
                
                
            iteration_count += 1


    print("____")
		


print(dep)
print(con)
print(dep_sec)