# infinity = float("inf")

# def make_graph():
#     # identical graph as the YouTube video: https://youtu.be/_lHSawdgXpI
#     # tuple = (cost, to_node)
#     return {
#         'DT1': [(1, 'DT4'),(3,'DT2')],
#         'DT2': [(1, 'DT3')],
#         'DT3': [(2, 'DT1')],
#         'DT4': [],
#         'DT5': [(1, 'DT3')],
#     }


# def dijkstras_heap(G, start='DT1'):
#     shortest_paths = {} 
#     visited = {} 
#     history = {} 
#     heap = [] 
#     path = []

#     for node in list(G.keys()):
#         shortest_paths[node] = infinity
#         visited[node] = False

#     shortest_paths[start] = 0 
#     visited[start] = True

#     heapq.heappush(heap, (0, start))

#     while heap:
#         (distance, node) = heapq.heappop(heap)
#         visited[node] = True

#         for edge in G[node]:
#             cost = edge[0]
#             to_node = edge[1]

#             if (not visited[to_node]) and (distance + cost < shortest_paths[to_node]):
#                 shortest_paths[to_node] = distance + cost
#                 heapq.heappush(heap, (shortest_paths[to_node], to_node))

#     return shortest_paths


# def dijkstras(G, start='DT1'):
#     shortest_paths = {}
#     unvisited = list(G.keys())

#     for node in unvisited:
#         shortest_paths[node] = infinity

#     shortest_paths[start] = 0

#     while unvisited:
#         min_node = None

#         for node in unvisited:
#             if min_node is None:
#                 min_node = node
#             elif shortest_paths[node] < shortest_paths[min_node]:
#                 min_node = node

#         for edge in G[min_node]:
#             cost = edge[0]
#             to_node = edge[1]

#             if cost + shortest_paths[min_node] < shortest_paths[to_node]:
#                 shortest_paths[to_node] = cost + shortest_paths[min_node]

#         unvisited.remove(min_node)

#     return shortest_paths


# def main():
#     G = make_graph()
#     DTs = ['DT1','DT2','DT3','DT4','DT5']
#     for dt in DTs:
#         start = dt

#         shortest_paths = dijkstras(G, start)
#         shortest_paths_using_heap = dijkstras(G, start)

#         print(f'Shortest path from {start}: {shortest_paths}')
#         # print(f'Shortest path from {start} using heap: {shortest_paths}')

# main()
# import networkx as nx
# G = nx.path_graph(5)
# print(nx.shortest_path(G, source=0, target=4))
# p = nx.shortest_path(G, source=0)  # target not specified
# p[3] # shortest path from source=0 to target=3
# [0, 1, 2, 3]
# p = nx.shortest_path(G, target=4)  # source not specified
# p[1] # shortest path from source=1 to target=4
# [1, 2, 3, 4]
# p = nx.shortest_path(G)  # source, target not specified
# p[2][4] # shortest path from source=2 to ta
import random

trust_score = []
te = []
p = {'1': {'1': ['1'], '4': ['1', '4'], '2': ['1', '4', '2']}, '4': {'4': ['4'], '2': ['4', '2'], '1': ['4', '2', '1']}, '2': {'2': ['2'], '1': ['2', '1'], '4': ['2', '1', '4']}, '3': {'3': ['3'], '1': ['3', '1'], '4': ['3', '1', '4'], '2': ['3', '1', '4', '2']}, '5': {'5': ['5'], '2': ['5', '2'], '4': ['5', '4'], '1': ['5', '2', '1']}}
hop_count = 0
influence = 0.5
DTs = p.keys()
for dt in DTs:
    trust_score.append(random.randint(1,10))
    te.append(0)
#print(DTs)
for dt in DTs:
    #print(p[dt])
    indirect_connets = p[dt].keys()
    #print(indirect_connets)
    for con in indirect_connets:
        #print(con)
        #print(len(p[dt][con]))
        if con != dt:
            te[int(con)-1] = te[int(con)-1] + trust_score[int(dt)-1] * influence / (len(p[dt][con])-1)
            #print(te)
    #print("___")
# for a in p:
#     print(p[a])
#     considered_dts = []
#     for b in p[a]:
#         print(p[a][b])
#         if len(p[a][b]) != 1:
#             for c in p[a][b]:
#                 print(c)
#                 if c==a:
#                     hop_count = 1
#                     considered_dts.append(c)
#                 else:
#                     if c not in considered_dts:
#                         trust_score[int(a)-1] = trust_score[int(a)-1] + trust_score[int(c)-1] * influence * (1/hop_count)
#                     hop_count += 1

#         considered_dts=[]
#         hop_count=0
                

#     print("___")
print(trust_score)
print(te)