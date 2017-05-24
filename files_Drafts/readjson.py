import json
import networkx as nx
from pprint import pprint
from graphviz import Digraph
from sys import argv


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
		digraph.add_node(i)						# add the node with the name of the port 
		if port["direction"] == "input":
			digraph.add_edge("origin", i)
		nodes[port["bits"][0]] = i
	return (digraph, nodes)

# function to parse the cells (Gates and flipflops)	
def readCells(jsonFile, digraph, nodes):
	cellNum = 1
	ffNum = 1
	for i in jsonFile["modules"]["simple_design1"]["cells"]:
		cell = jsonFile["modules"]["simple_design1"]["cells"][i]		# get each cell 
		name = cell["type"]			# get the cell name 	
		if name.find("DFF") != -1:	# check if a flipflop 
			for j in cell["connections"]:
				pin = cell["connections"][j]		# get the json pin
				pinName = j.lower() + str(ffNum)	# make the name	, special name for flipflops 
				digraph.add_node(pinName)
				if pin[0] >= len(nodes) or nodes[pin[0]] == '':			# check of new connection or an old one 
					nodes.extend(['']*(pin[0] - len(nodes) + 1))
					nodes[pin[0]] = pinName			# First node in edge
				elif j != 'Q':
					digraph.add_edge(nodes[pin[0]], pinName)		# in-direction 
				else:
					digraph.add_edge(pinName, nodes[pin[0]])		#out-direction 
			pinclk = "clk" + str(ffNum)
			pinD = "d" + str(ffNum)
			pinQ = "q" + str(ffNum)
			digraph.add_edge(pinD, pinQ)
			digraph.add_edge(pinclk, pinQ)
			ffNum += 1
		else:
			for j in cell["connections"]:			# first just create the nodes 
				pin = cell["connections"][j]
				pinName = name + str(cellNum) +j	# create a unique name for the pins 
				digraph.add_node(pinName)
				if pin[0] >= len(nodes) or nodes[pin[0]] == '':
					nodes.extend(['']*(pin[0] - len(nodes) + 1))
					nodes[pin[0]] = pinName
				elif j != 'Y': 
					digraph.add_edge(nodes[pin[0]], pinName)
				else: 
					digraph.add_edge(pinName, nodes[pin[0]])
			
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
	path = 'Graph_DD2/' + png + '.gv'
	dot.render(path, view=True)

if __name__ == "__main__":

	script, file , png = argv
	jsonFile = readJson(file)
				
	digraph = nx.DiGraph()
	digraph.add_node("origin")
	digraph, nodes = readPorts(jsonFile, digraph)
	
	digraph = readCells(jsonFile, digraph, nodes)
	drawGraph(digraph, png)

