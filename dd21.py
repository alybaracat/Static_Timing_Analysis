import networkx as nx
import re
from graphviz import Digraph


G = nx.DiGraph([('origin','d1'),('d1','q1'),('q1','d2'),('q1','d3'),('d2','q2'),('d3','q3'),('q2','and1'),('q3','and2'),('and2','and3'),('and1','and3'),('and3','y'),('origin','inv1'),('inv1','inv2'),('inv2','and3')])   # or DiGraph, MultiGraph, MultiDiGraph, etc
list_nodes = G.nodes()

template = '^d([0-9]+)'
d = []
q = []

for node in list_nodes:
    search = re.search(template,node)
    if search:
        index = search.group(1)
        print(index)
        G.remove_edge('d'+ str(index),'q'+ str(index))
        d.append('d'+ str(index))
        q.append('q'+ str(index))
    else:
        print ('No')
    
# print  (G.number_of_nodes())
# print  (G.number_of_edges())

# print(list(nx.dfs_edges(G,'origin')))
# G.remove_edge('d','q')

for path in nx.all_simple_paths(G, source='origin', target='y'):
        print(path)

for i in q:
    for path in nx.all_simple_paths(G, source=i, target='y'):
        print(path)
        
for i in d:    
    for path in nx.all_simple_paths(G, source='origin', target=i):
        print(path)

for i in q:
    for j in d:
        for path in nx.all_simple_paths(G, source=i, target=j):
            print(path)
    
dot = Digraph(comment='Graph')

for node in list_nodes:
    dot.node(node, node)

list_edges = G.edges()

for edge_G in list_edges:
       dot.edge(edge_G[0],edge_G[1] )
        
# dot.edges(['AB', 'AL'])
# dot.edge('B', 'L', constraint='false')
print(dot.source)  # doctest: +NORMALIZE_WHITESPACE
dot.render('Graph_DD2/DAG1.gv', view=True)   

