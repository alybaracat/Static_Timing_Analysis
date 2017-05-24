import networkx as nx 
import re #importing Regex Expressions
from graphviz import Digraph 

G = nx.DiGraph([('origin','d1'),('d1','q1'),('q1','d2'),('q1','d3'),('d2','q2'),('d3','q3'),('q2','and1'),('q3','and2'),('and2','and3'),('and1','and3'),('and3','y'),('origin','inv1'),('inv1','inv2'),('inv2','and3')])   # or DiGraph, MultiGraph, MultiDiGraph, etc
#e7na mo3taberin en el format beta3it el graph betigi keda we en ay FLIP FLOP hayeb2a maktoob d(we ba3dh number) we q(we ba3dih number)

# G = nx.DiGraph([('origin','a'),('origin','b'),('a','d1'),('b','d2'),('d1','q1'),('d2','q2'),('q1','y'),('q2','y')])   # or DiGraph, MultiGraph, MultiDiGraph, etc

list_nodes = G.nodes() #creates a list of all the nodes

template = '^d([0-9]+)' #Regex Template yedawar 3la d we ba3dih rakam 
# "^" means en el string bey start be d


for node in list_nodes: #iterate over the different nodes
    search = re.search(template,node) #search for D pins of Flip-flops
    if search:
        index = search.group(1) #group 1 extracts the index
        G.remove_edge('d'+ str(index),'q'+ str(index)) #remove edge between d and q 3alashan e7na 2olna
        #d yo3tabar output we q yo3tabar input
        G.add_edge ('origin','q'+ str(index)) #connect q to source
        G.add_edge ('d'+ str(index),'y')#connect d to output
   

for path in nx.all_simple_paths(G, source='origin', target='y'): #traverse the graph and print all paths
        print(path)

dot = Digraph(comment='Graph') #Digraph is for the Graphviz library

for node in list_nodes:
    dot.node(node, node) #adding the nodes to the Digraph

list_edges = G.edges()

for edge_G in list_edges:
       dot.edge(edge_G[0],edge_G[1] ) #adding the edges to the Digraph
        
print(dot.source)  # doctest: +NORMALIZE_WHITESPACE
dot.render('Graph_DD2/DAG2.gv', view=True)