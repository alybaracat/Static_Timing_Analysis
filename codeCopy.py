import json
import networkx as nx
from pprint import pprint
from graphviz import Digraph
from sys import argv
import sys
import re #importing Regex Expressions
from random import randint

transition = [0.06, 0.18, 0.42, 0.6, 1.2]
capacitance = [0.015, 0.04, 0.08, 0.2, 0.4]
libFile = 0
digraph = 0

# function to read the json data 
def readJson(fileName):
    with open(fileName) as data_file:
        data = json.load(data_file)
    return data

# function to read the input ports 
def readPorts(jsonFile, digraph):
    nodes = [None]* (len(jsonFile["modules"]["simple_design1"]["ports"]) + 2)
    nodes[0] = "nope"
    nodes[1] = "origin"
    for i in jsonFile["modules"]["simple_design1"]["ports"]:		# get the names of the ports 
        port = jsonFile["modules"]["simple_design1"]["ports"][i]
        name = i
        if port["direction"] == "output":
            name = "out_" + i
        digraph.add_node(name)						# add the node with the name of the port 
        if port["direction"] == "input":
            digraph.add_edge("origin",name, weight = randint(0,9))
        else:
            digraph.add_edge(name, "endpoint", weight = randint(0,9))		# connect the outputs to the end points 
        nodes[port["bits"][0]] = name
        
        digraph.node[name]['capacitance'] = 0		# inputs and outputs have no capacitance 
        digraph.node[name]['nodeType'] = port['direction']		# add the directions 
        digraph.node[name]['gateType'] = 'no gate'					# no gate type 
        digraph.node[name]['realName'] = i
        digraph.node[name]['delay'] = 0
        digraph.node[name]['out_transition'] = 0
        
    return nodes

# function to parse the cells (Gates and flipflops)	
def readCells(jsonFile, libFile, digraph, nodes):
    cellNum = 1
    ffNum = 1
    for i in jsonFile["modules"]["simple_design1"]["cells"]:
        cell = jsonFile["modules"]["simple_design1"]["cells"][i]		# get each cell 
        name = cell["type"]	
        pinName = ''											# get the cell name 	
        if name.find("DFF") != -1:										# check if a flipflop 
            for j in cell["connections"]:
                pin = cell["connections"][j]				# get the json pin
                pinName = j.lower() + str(ffNum)			# make the name	, special name for flipflops 
                digraph.add_node(pinName)
                digraph.node[pinName]['realName'] = j
                if pin[0] >= len(nodes) or nodes[pin[0]] == '':			# check of new connection or an old one 
                    nodes.extend(['']*(pin[0] - len(nodes) + 1))
                    nodes[pin[0]] = pinName							# First node in edge
                elif j != 'Q':
                	digraph.node[pinName]['nodeType'] = 'gateInput'
                	digraph.add_edge(nodes[pin[0]], pinName, weight = randint(0,9))
                	capacitance = libFile["cells"][name]["pins"][j]['capacitance']
                         
                else:
                	digraph.node[pinName]['nodeType'] = 'gateOutput'
                	digraph.add_edge(pinName, nodes[pin[0]], weight = randint(0,9))		#out-direction
                	capacitance = 0
                    
                digraph.node[pinName]['gateType'] = name					# name of the gate of the graph 
                digraph.node[pinName]['capacitance'] = capacitance
                    
            pinclk = "clk" + str(ffNum)
            pinD = "d" + str(ffNum)
            pinQ = "q" + str(ffNum)
            digraph.add_edge(pinD, pinQ, weight = randint(0,9))
            digraph.add_edge(pinclk, pinQ, weight = randint(0,9))
            ffNum += 1            
        else:
            for j in cell["connections"]:			# first just create the nodes 
                pin = cell["connections"][j]
                pinName = name + str(cellNum) +j	# create a unique name for the pins 
                digraph.add_node(pinName)
                digraph.node[pinName]['realName'] = j
                
                if j != 'Y':					# specify the input type. 
                	digraph.node[pinName]['nodeType'] = 'gateInput'
                	capacitance = libFile["cells"][name]["pins"][j]['capacitance']
                else:
                	digraph.node[pinName]['nodeType'] = 'gateOutput'
                	capacitance = 0
                	
                if pin[0] >= len(nodes) or nodes[pin[0]] == '':
                    nodes.extend(['']*(pin[0] - len(nodes) + 1))
                    nodes[pin[0]] = pinName
                elif j != 'Y':
                	digraph.add_edge(nodes[pin[0]], pinName, weight = randint(0,9))
                else:
                	digraph.add_edge(pinName, nodes[pin[0]], weight = randint(0,9))
                    
                digraph.node[pinName]['gateType'] = name					# name of the gate of the graph 
                digraph.node[pinName]['capacitance'] = capacitance					# the capacitance of the pin


            pinY = name + str(cellNum) + 'Y'	
            for j in cell["connections"]:
                pinName = name + str(cellNum) +j
                if j != 'Y':
                    digraph.add_edge(pinName, pinY, weight = randint(0,9))
            cellNum += 1
            
def extrapolate(value, array):				# extrapolate the output transition or the capacitance load 
	extr = array[0];
	diff = abs(array[0] - float(value))
	for i in range(1, len(array)):
		if abs(array[i] - value) < diff:
			diff = abs(array[i] - value)
			extr = array[i]
	return extr
		
                 
def getDelay(cLoad, inTrans, toNode, fromNode):
	table = libFile["cells"][digraph.node[toNode]["gateType"]]\
	["pins"][digraph.node[toNode]["realName"]]["timing"][digraph.node[fromNode]["realName"]]
		
	cLoad = extrapolate(cLoad, capacitance)			# extrapolate the capacitance
	cellRise = table["cell_rise"]["table"][str(cLoad)][str(inTrans)]		
	cellFall = table["cell_fall"]["table"][str(cLoad)][str(inTrans)]
	inputDelay = max(cellRise, cellFall)			# get the worst of 2 delays 
	#if inputDelay > digraph.node[toNode]["delay"]:		# update if needed 
		#digraph.node[toNode]["delay"] = inputDelay
		    
def get_node_capacitance_load(node): #function to calculate load capacitance for a given node
	sum = 0
	if 'nodeType' in digraph.node[node]: #Check if nodetype exists in struct digraph.node[node] 3ashan fih sa3at structs beteb2a empty "NOPE"
		if digraph.node[node]['nodeType'] == 'gateOutput': #check if Gate Output
			for neighbor in digraph.neighbors(node): #iterate over the neighbors
				sum += digraph[node][neighbor]['weight'] + digraph.node[neighbor]['capacitance'] #add the wire load (edge weight) + pin capacitance
			for prenode in digraph.predecessors(node):
				getDelay(sum, 0.06, node, prenode)
				
#function to draw the graph using the graphviz library 
def drawGraph(digraph, png, libFile):
    listNodes = digraph.nodes()
    listEdges = digraph.edges()
    dot = Digraph(comment="Graph")
    for node in listNodes:
#         print (digraph.node[node])
        dot.node(node, node)
        cLoad = get_node_capacitance_load(node)
        print cLoad
    for edge in listEdges:
        dot.edge(edge[0], edge[1], label = str(digraph[edge[0]][edge[1]]['weight'])) #Added label for the weight of the Edge
    path = 'SD4.gv'
    dot.render(path, view=True)

if __name__ == "__main__":

    script, file, png = argv
    gateLevel = readJson(file)		# read the gate level net list json file  
    libFile = readJson('osu350.json')		# read the liberty json file
    digraph = nx.DiGraph()
    digraph.add_node("origin")
    digraph.add_node("endpoint")
    nodes = readPorts(gateLevel, digraph)
    readCells(gateLevel,libFile,  digraph, nodes)
    
    drawGraph(digraph, png, libFile)
    list_nodes = digraph.nodes()
    template = '^d([0-9]+)'
    d = []
    q = []

    for node in list_nodes:
        search = re.search(template,node)
        if node == 'clk':
            digraph.remove_edge('origin','clk')          
        if search:
            index = search.group(1)
            digraph.remove_edge('d'+ str(index),'q'+ str(index))
            d.append('d'+ str(index))
            q.append('q'+ str(index))

            
    file = open("Timing_Paths_SD1.txt","w") 


    file.write("\nInput to Output Paths: \n ")   
    for path in nx.all_simple_paths(digraph, source='origin', target='endpoint'):
        #print(path)
        out = str(path).replace(",", "->")
        out = out.replace("[", "")
        out = out.replace("]", "")
        out = out.replace("'", " ")
        file.write( "\n" + out + "\n") 
        
    if not nx.all_simple_paths(digraph, source='origin', target='endpoint'):
        file.write("NONE \n")

    file.write("\nReg to Output Paths: \n")   
    for i in q:
        for path in nx.all_simple_paths(digraph, source=i, target='endpoint'):
            out = str(path).replace(",", "->")
            out = out.replace("[", "")
            out = out.replace("]", "")
            out = out.replace("'", " ")
            #print(path)
            file.write("\n" + out + "\n") 
    if not q:
        file.write("NONE \n")

    file.write("\nInput to Reg Paths: \n")   
    for i in d:    
        for path in nx.all_simple_paths(digraph, source='origin', target=i):
            out = str(path).replace(",", "->")
            out = out.replace("[", "")
            out = out.replace("]", "")
            out = out.replace("'", " ")
            #print(path)
            file.write("\n" + out + "\n")
    if not d:
        file.write("NONE \n")

    file.write("\nReg to Reg Paths: \n")   
    for i in q:
        for j in d:
            for path in nx.all_simple_paths(digraph, source=i, target=j):
                out = str(path).replace(",", "->")
                out = out.replace("[", "")
                out = out.replace("]", "")
                out = out.replace("'", " ")
                #print(path)
                file.write("\n" + out + "\n") 
    if not q: 
        file.write("NONE \n")
    else:
        if not d:
            file.write("NONE \n")
        else:
             for i in q:
                for j in d:            
                    if not nx.all_simple_paths(digraph, source=i, target=j):
                        file.write("NONE \n")

    file.close() 
