
# coding: utf-8

# In[48]:

import json
import networkx as nx
from pprint import pprint
from graphviz import Digraph
from sys import argv
from random import randint

import sys
import re #importing Regex Expressions



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
            digraph.add_edge("origin", name)
        else:
            digraph.add_edge(name, "endpoint")
        nodes[port["bits"][0]] = name
    return (digraph, nodes)

# function to parse the cells (Gates and flipflops)	
def readCells(jsonFile, digraph, nodes):
    cellNum = 1
    ffNum = 1
    pinName = ""
    for i in jsonFile["modules"]["simple_design1"]["cells"]:
        cell = jsonFile["modules"]["simple_design1"]["cells"][i]		# get each cell 
        name = cell["type"]			# get the cell name 
    	capacitance = 0	

        for j in cell["connections"]:			# first just create the nodes 
            pin = cell["connections"][j]
            if name.find("DFF") != -1:
                pinName = j.lower() + str(ffNum)
            else: 
                pinName = name + str(cellNum) + j
            
            digraph.add_node(pinName)
            digraph.node[pinName]['realName'] = j
            if pin[0] >= len(nodes) or nodes[pin[0]] == '':
                nodes.extend(['']*(pin[0] - len(nodes) + 1))
                nodes[pin[0]] = pinName
            elif j != 'Y' and j != 'Q': 
                digraph.node[pinName]['nodeType'] = 'gateInput'
                digraph.add_edge(nodes[pin[0]], pinName, weight = randint(0,9))
                capacitance = libFile["cells"][name]["pins"][j]['capacitance']
            else: 
                digraph.node[pinName]['nodeType'] = 'gateOutput'
                digraph.add_edge(pinName, nodes[pin[0]], weight = randint(0,9))		#out-direction
                
            digraph.node[pinName]['gateType'] = name					# name of the gate of the graph 
            digraph.node[pinName]['capacitance'] = capacitance

        if name.find("DFF") != -1:
        	pinclk = "clk" + str(ffNum)
        	pinD = "d" + str(ffNum)
        	pinQ = "q" + str(ffNum)
        	digraph.add_edge(pinD, pinQ)
        	digraph.add_edge(pinclk, pinQ)
        	ffNum += 1
        else:
            pinY = name + str(cellNum) + 'Y'	
            for j in cell["connections"]:
                pinName = name + str(cellNum) +j
                if j != 'Y':
                    digraph.add_edge(pinName, pinY)
            cellNum += 1
    return digraph

# function to draw the graph using the graphviz library 
def drawGraph(digraph, png):
    listNodes = digraph.nodes()
    listEdges = digraph.edges()
    dot = Digraph(comment="Graph")
    for node in listNodes:
        dot.node(node, node)
    for edge in listEdges:
        dot.edge(edge[0], edge[1])
    path = 'SD1.gv'
    dot.render(path, view=True)

if __name__ == "__main__":

    script, file, png = argv
    jsonFile = readJson(file)

    digraph = nx.DiGraph()
    digraph.add_node("origin")
    digraph.add_node("endpoint")
    digraph, nodes = readPorts(jsonFile, digraph)

    digraph = readCells(jsonFile, digraph, nodes)
    drawGraph(digraph, png)
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
        print(path)
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
            print(path)
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
            print(path)
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
                print(path)
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




