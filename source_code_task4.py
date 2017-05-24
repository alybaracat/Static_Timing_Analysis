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
trans_flipflop =  [0.06,0.24,0.48,0.9,1.2,1.8]
transition_related = [0.06, 0.3, 0.6]
libFile = 0
digraph = 0

# function to read the json data
def readJson(fileName):
    with open(fileName) as data_file:
        data = json.load(data_file)
    return data

def readConstraints(constraintFile):

    clk_period = constraintFile["clock_period"] - constraintFile["uncertainty"]

    return clk_period, constraintFile["input_delay"]

# function to read the input ports
def readPorts(jsonFile, capFile):
    input_trans = capFile["input_transition"]
    nodes = [None]* (len(jsonFile["modules"]["simple_design1"]["ports"]) + 2)
    nodes[0] = "nope"
    nodes[1] = "origin"
    digraph.node["origin"]['max_delay'] = 0
    digraph.node["origin"]['min_delay'] = 0
    for i in jsonFile["modules"]["simple_design1"]["ports"]:        # get the names of the ports
        port = jsonFile["modules"]["simple_design1"]["ports"][i]
        name = i
        if port["direction"] == "output":
            name = "out_" + i
        digraph.add_node(name)                      # add the node with the name of the port
        digraph.node[name]['trans'] = 0
        digraph.node[name]['max_delay'] = 0
        digraph.node[name]['min_delay'] = 0

        if port["direction"] == "input":
            digraph.add_edge("origin",name)
            digraph["origin"][name]['weight'] = 0
            digraph.node[name]['trans'] = input_trans
        else:
            digraph.add_edge(name, "endpoint")      # connect the outputs to the end points
            digraph[name]["endpoint"]['weight'] = 0
        nodes[port["bits"][0]] = name

        digraph.node[name]['capacitance'] = 0       # inputs and outputs have no capacitance
        digraph.node[name]['nodeType'] = port['direction']      # add the directions
        digraph.node[name]['gateType'] = 'no gate'                  # no gate type
        digraph.node[name]['realName'] = i
    return nodes

# function to parse the cells (Gates and flipflops)
def readCells(jsonFile, nodes):
    cellNum = 1
    ffNum = 1
    pinName = ""
    for i in jsonFile["modules"]["simple_design1"]["cells"]:
        cell = jsonFile["modules"]["simple_design1"]["cells"][i]        # get each cell
        name = cell["type"]         # get the cell name
        capacitance = 0

        for j in cell["connections"]:           # first just create the nodes
            pin = cell["connections"][j]

            isFlipFlop = False          # default, not a flipflop
            if name.find("DFF") != -1:
                pinName = j.lower() + str(ffNum)
                isFlipFlop = True
            else:
                pinName = name + str(cellNum) + j

            digraph.add_node(pinName)
            digraph.node[pinName]['realName'] = j
            digraph.node[pinName]['isflipflop'] = isFlipFlop

            if j!= 'Y' and j != 'Q':
                digraph.node[pinName]['nodeType'] = 'gateInput'
            else:
                digraph.node[pinName]['nodeType'] = 'gateOutput'


            if pin[0] >= len(nodes) or nodes[pin[0]] == '':
                nodes.extend(['']*(pin[0] - len(nodes) + 1))
                nodes[pin[0]] = pinName
            elif j != 'Y' and j != 'Q':
                digraph.add_edge(nodes[pin[0]], pinName)
                digraph[nodes[pin[0]]][pinName]['weight'] = 0
                capacitance = libFile["cells"][name]["pins"][j]['capacitance']
            else:
                digraph.add_edge(pinName, nodes[pin[0]])        #out-direction
                digraph[pinName][nodes[pin[0]]]['weight'] = 0

            digraph.node[pinName]['gateType'] = name                    # name of the gate of the graph
            digraph.node[pinName]['capacitance'] = capacitance
            digraph.node[pinName]['max_delay'] = 0
            digraph.node[pinName]['min_delay'] = 0
            digraph.node[pinName]['trans'] = 0

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

def dag_longest_path(G, weight='weight', default_weight=1):
    dist = {} # stores {v : (length, u)}
    for v in nx.topological_sort(G):
        us = [(dist[u][0] + G.node[u]['max_delay'], u) for u, data in G.pred[v].items()]
        maxu = max(us, key=lambda x: x[0]) if us else (0, v)
        dist[v] = maxu if maxu[0] >= 0 else (0, v)
        distance = dist[v][0]
    u = None
    v = max(dist, key=lambda x: dist[x][0])
    path = []
    while u != v:
        path.append(v)
        u = v
        v = dist[v][1]
    path.reverse()
    return path, distance

def setCapacitance(capFile):
    table = capFile["wires"]
    for point in table:
        digraph[point["input"]][point["output"]]['weight'] = point["value"]


def extrapolate(value, array):              # extrapolate the output transition or the capacitance load
    extr = array[0];
    diff = abs(array[0] - float(value))
    for i in range(1, len(array)):
        if abs(array[i] - value) < diff:
            diff = abs(array[i] - value)
            extr = array[i]
    return extr

def getConstraints(table, qNode):
    pre = digraph.predecessors(qNode)
    clk = pre[0]            # pre has the clk and the data
    data = pre[1]

    rise_constraint = table["rise_constraint"]["table"]
    fall_constraint = table["fall_constraint"]["table"]

    relatedPinTransition = str(extrapolate(digraph.node[clk]['trans'], transition_related))
    constrainedTransition = str(extrapolate(digraph.node[data]['trans'], transition))

    rise = rise_constraint[relatedPinTransition][constrainedTransition]
    fall = fall_constraint[relatedPinTransition][constrainedTransition]
    Time = max(rise, fall)

    return Time


def getSetupAndHold(qNode):

    holdtable = libFile["cells"][digraph.node[qNode]["gateType"]]["hold_rising"]
    digraph.node[qNode]['hold'] = getConstraints(holdtable, qNode)

    setuptable = libFile["cells"][digraph.node[qNode]["gateType"]]["setup_rising"]
    digraph.node[qNode]['setup'] = getConstraints(setuptable, qNode)


def setDelay_getOutTrans(cLoad, inTrans, toNode, fromNode):
    table = libFile["cells"][digraph.node[toNode]["gateType"]]\
    ["pins"][digraph.node[toNode]["realName"]]["timing"]#[digraph.node[fromNode]["realName"]]

    if digraph.node[fromNode]["realName"] in table:     # only the CLK in Flip Flop will get in
        table = table[digraph.node[fromNode]["realName"]]
        cLoad = extrapolate(cLoad, capacitance)
        inTrans_ex = 0
        isFlipFlop = digraph.node[toNode]['gateType'].find("DFF") != -1
        if isFlipFlop:          # a flip flop, extrapolate to a different array
            inTrans_ex = extrapolate(inTrans, trans_flipflop)
        else:
            inTrans_ex = extrapolate(inTrans, transition)

        cellRise = table["cell_rise"]["table"][str(cLoad)][str(inTrans_ex)]
        cellFall = table["cell_fall"]["table"][str(cLoad)][str(inTrans_ex)]


        maxInputDelay = max(cellRise, cellFall)         # get the worst of 2 delays
        minInputDelay = min(cellRise, cellFall)

        if isFlipFlop:          # a flip flop, extrapolate to a different array
            digraph.node[toNode]['tcqmax'] = maxInputDelay
            digraph.node[toNode]['tcqmin'] = minInputDelay

        digraph.node[toNode]['max_delay'] = max(maxInputDelay, digraph.node[toNode]['max_delay'])
        digraph.node[toNode]['min_delay'] = min(minInputDelay, digraph.node[toNode]['min_delay'])



        rise_trans = table["rise_transition"]["table"][str(cLoad)][str(inTrans_ex)]
        fall_trans = table["fall_transition"]["table"][str(cLoad)][str(inTrans_ex)]
        out_trans = max(rise_trans, fall_trans)

        return out_trans                # return the output transition , they are getting the max

def setSkews(skewFile):

	listNodes = digraph.nodes()

	for skews in skewFile:
		if skews in listNodes:
			digraph.node[skews]['skew'] = skewFile[skews]
			print skewFile[skews]


def get_node_capacitance_load(node): #function to calculate load capacitance for a given node
    sum = 0
    if 'nodeType' in digraph.node[node]: #Check if nodetype exists in struct digraph.node[node] for origin and endpoint
        if digraph.node[node]['nodeType'] == 'gateOutput': #check if Gate Output
            for neighbor in digraph.neighbors(node): #iterate over the neighbors
                sum += digraph[node][neighbor]['weight'] + digraph.node[neighbor]['capacitance'] #add the wire load (edge weight) + pin capacitance
            maxim = 0
            for prenode in digraph.predecessors(node):
                maxim = max(maxim, setDelay_getOutTrans(sum, digraph.node[prenode]['trans'], node, prenode))
            digraph.node[node]['trans'] = maxim

            # get the setup and hold times
            if digraph.node[node]['isflipflop'] == True:
                getSetupAndHold(node)

        if digraph.node[node]['nodeType'] == 'gateInput' or digraph.node[node]['nodeType'] == 'output':
            maxim = 0
            for prenode in digraph.predecessors(node):
                maxim = max(maxim, digraph.node[prenode]['trans'])
            digraph.node[node]['trans'] = maxim


def apply_styles(graph, styles):
    graph.graph_attr.update(
        ('graph' in styles and styles['graph']) or {}
    )
    graph.node_attr.update(
        ('nodes' in styles and styles['nodes']) or {}
    )
    graph.edge_attr.update(
        ('edges' in styles and styles['edges']) or {}
    )
    return graph
#function to draw the graph using the graphviz library
def drawGraph(digraph, png, libFile):
    listNodes = digraph.nodes()
    listEdges = digraph.edges()
    dot = Digraph(comment="Graph")
    styles = {
    'graph': {
        'label': 'Graph',
        'fontsize': '12',
        'fontcolor': 'white',
        'bgcolor': '#ffffff',
    },
    'nodes': {
        'fontname': 'Helvetica',
        'shape': 'circle',
        'fontcolor': 'white',
        'fontsize': '6',
        'radius':'2',
        'color': 'white',
        'style': 'filled',
        'fillcolor': '#222f49',
    },
    'edges': {
        'color': '#333333',
        'arrowhead': 'open',
        'fontname': 'Courier',
        'fontsize': '12',
        'fontcolor': 'white',
    }
    }

    for node in nx.topological_sort(digraph):
        #print("NODE ________ : ) " + node)
        string = ""
        print node
        if 'max_delay' in digraph.node[node]:
            string += "Max Delay= " + str(digraph.node[node]['max_delay'])
        if 'min_delay' in digraph.node[node]:
            string += "\n Min Delay= " + str(digraph.node[node]['min_delay'])
        if 'hold' in digraph.node[node]:
            string += "\n Hold = " + str(digraph.node[node]['hold'])
        if 'setup' in digraph.node[node]:
            string += "\n Setup = " + str(digraph.node[node]['setup'])
        if 'tcqmin' in digraph.node[node]:
            string += "\n Setup = " + str(digraph.node[node]['tcqmin'])
        if 'tcqmax' in digraph.node[node]:
            string += "\n Setup = " + str(digraph.node[node]['tcqmax'])

        print(string)
        #print digraph.node[node] , "\n\n"
        #string = str(digraph.node[node])
        dot.node(node, node + '\n\n' + string)
        get_node_capacitance_load(node)

    for edge in listEdges:
        dot.edge(edge[0], edge[1]) #Added label for the weight of the Edge
    path = 'SD4.gv'
    dot = apply_styles(dot, styles)
    dot.render(path, view=True)


if __name__ == "__main__":

    script, file, png = argv
    gateLevel = readJson('SD4.json')        # read the gate level net list json file
    libFile = readJson('osu350.json')       # read the liberty json file
    capFile = readJson('CF4.json')
    skewFile = readJson('skew_file.json')
    constraintFile = readJson('timing_constraints.json')
    digraph = nx.DiGraph()
    digraph.add_node("origin")
    digraph.add_node("endpoint")
    nodes = readPorts(gateLevel, capFile)
    clk_period, inDelay = readConstraints(constraintFile)   #function to read constraint file
    readCells(gateLevel,nodes)
    setCapacitance(capFile)
    setSkews(skewFile)

    for node in nx.topological_sort(digraph):
		get_node_capacitance_load(node)


    list_nodes = digraph.nodes()

    path, distance = dag_longest_path(digraph)
    print path
    print str(distance)

    template = '^d([0-9]+)'
    d = []
    q = []

    for node in list_nodes:
        search = re.search(template,node)
        # if node == 'clk':
#             #digraph.remove_edge('origin','clk')
        if search:
            index = search.group(1)
            #digraph.remove_edge('d'+ str(index),'q'+ str(index))
            d.append('d'+ str(index))
            q.append('q'+ str(index))


    file = open("Timing_Paths_SD4.txt","w")
    file1 = open("CriticalPath_SD4.txt","w")
    file2 = open("Check_Violations_SD4.txt", "w")

    file1.write("Longest Path: " + str(path) + "\n\n")
    file1.write("Delay: " + str(distance))

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
        file2.write("No FlipFlops in this design")

    file.write("\nInput to Reg Paths: \n")

    for i in q:
        for path in nx.all_simple_paths(digraph, source='origin', target=i):
            setup_violation = 0
            hold_violation = 0
            for node in path:
                setup_violation += digraph.node[node]['max_delay']
                hold_violation += digraph.node[node]['min_delay']

            pre = digraph.predecessors(node)
            clk = pre[0]
            print digraph.node[clk]['skew']
            setup_violation += digraph.node[node]['setup'] + inDelay - clk_period
            hold_violation += digraph.node[node]['tcqmin'] - digraph.node[node]['hold'] - digraph.node[clk]['skew']

            print "setup_violation= ", setup_violation
            print "hold_violation= "  , hold_violation

            out = str(path).replace(",", "->")
            out = out.replace("[", "")
            out = out.replace("]", "")
            out = out.replace("'", " ")

            if setup_violation > 0:

                file2.write("There is a setup violations\n")
                file2.write(str(out) + "\n\n")

            else:
                file2.write("0 >= " + str(setup_violation) + " ==> No Setup Time Violation\n")
                file2.write(str(out) + "\n\n")

            if hold_violation < 0:
            	file2.write("There is a hold violation\n")
            	file2.write(str(out) + "\n\n")

            else:
                file2.write("0 <= " + str(hold_violation) + " ==> No Hold Time Violation\n")
                file2.write(str(out) + "\n\n")

            file.write("\n" + out + "\n")
    if not d:
        file.write("NONE \n")

    file.write("\nReg to Reg Paths: \n")
    for i in q:
        for j in d:
            for path in nx.all_simple_paths(digraph, source=i, target=j):
                setup_violation = 0
                hold_violation = 0
                for node in path:
                   setup_violation += digraph.node[node]['max_delay']
                   hold_violation += digraph.node[node]['min_delay']

                pre = digraph.predecessors(node)
                clk = pre[0]

                if 'setup' in digraph.node[node]:
                    setup_violation += digraph.node[node]['setup'] + inDelay - clk_period
                if 'hold' in digraph.node[node]:
                    hold_violation += digraph.node[node]['tcqmin'] - digraph.node[node]['hold'] + digraph.node[clk]['skew']

                print "setup_violation= ", setup_violation
                print "hold_violation= "  , hold_violation

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
    drawGraph(digraph, png, libFile)
