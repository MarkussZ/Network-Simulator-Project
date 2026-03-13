import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from IpCalcClass import IpCalc

def visualizer(devices):
    G = nx.MultiGraph()
    
    for device in devices.values():
        if device.ip:
            ipClass = device.ipClass or "None"
            ipType = device.ipType or "None"
            prefix = IpCalc.subnetToPrefix(device.subnet)
            wildcard = IpCalc.wildcardMask(device.subnet)
            gateway = device.gateway or "None"
            IPlabel = f"{device.ip}{prefix} ({ipClass}, {ipType})\nSubnet Wildcard: {wildcard}\nGateway: {gateway}"
        else:
            IPlabel = "No IP"
        label =f"{device.name}\n({device.deviceType})\n{IPlabel}\n{device.state.upper()}"
        G.add_node(device.name, label=label)
        
    addedConnections = set()
    for device in devices.values():
        for port, connection in device.ports.items():
            if connection is not None:
                connDevice, connPort = connection
                
                cableKey = tuple(sorted([
                    (device.name, port),
                    (connDevice, connPort)
                ]))
                
                if cableKey not in addedConnections:
                    G.add_edge(device.name, connDevice, label=f"{port}={connPort}")
                    addedConnections.add(cableKey)
    
    
    pos = nx.spring_layout(G)
    
    labels = nx.get_node_attributes(G, 'label')
    edgeLabels = nx.get_edge_attributes(G, 'label')
    
    colourMap = []
    for node in G.nodes():
        device = devices[node]
        
        if device.deviceType == "Router":
            colourMap.append("red")
        elif device.deviceType == "L2Switch":
            colourMap.append("yellow")
        elif device.deviceType == "L3Switch":
            colourMap.append("orange")
        elif device.deviceType == "Server":
            colourMap.append("green")
        elif device.deviceType == "PC":
            colourMap.append("lightblue")
        elif device.deviceType == "Firewall":
            colourMap.append("purple")
        else:
            colourMap.append("black")
    
    nx.draw_networkx_nodes(G, pos, node_size=5000, node_color=colourMap)
    nx.draw_networkx_labels(G, pos, labels, font_size = 7)
    
    edgeGroup = {}
    
    for i, (u, v, key, data) in enumerate(G.edges(keys = True, data = True)):
        pair = tuple(sorted([u, v]))
        edgeGroup.setdefault(pair, []).append((u, v, key, data))
        
    for pair, edges in edgeGroup.items():
        numEdges = len(edges)
        
        if numEdges == 1:
            u,v,key,data = edges[0]
            deviceU = devices[u]
            deviceV = devices[v]
                
            if deviceU.state == 'on' and deviceV.state == 'on':
                edge_color = 'green'
            else:
                edge_color = 'red'
            nx.draw_networkx_edges(
                G,
                pos,
                edgelist=[(u, v)],
                edge_color=edge_color,
                width=2
            )
            
            x1, y1 = pos[u]
            x2, y2 = pos[v]
            
            plt.text((x1+x2)/2, (y1+y2)/2,
            data['label'],
            fontsize = 8,
            horizontalalignment = 'center')
            
            #portLabels = data['label'].split('=')
            #offset = 0.03
            
            #plt.text(x1 - offset, y1 - offset, portLabels[0], fontsize=8, horizontalalignment='right', verticalalignment='top')
            #plt.text(x2 + offset, y2 + offset, portLabels[1], fontsize=8, horizontalalignment='left', verticalalignment='bottom')
        
        else:
            step = 0.25
            start = -step * (numEdges - 1)/2
            
            for i, (u, v, key, data) in enumerate(edges):
                rad = start+ i * step
                
                deviceU = devices[u]
                deviceV = devices[v]
                
                if deviceU.state == 'on' and deviceV.state == 'on':
                    edge_color = 'green'
                else:
                    edge_color = 'red'
                
                nx.draw_networkx_edges(
                    G,
                    pos,
                    edgelist = [(u, v)],
                    connectionstyle=f'arc3,rad={rad}',
                    edge_color = edge_color,
                    width=2
                )
                
                x1, y1 = pos[u]
                x2, y2 = pos[v]
                
                midX = (x1 + x2)/2
                midY = (y1 + y2)/2
                
                dx = y2-y1
                dy = x1-x2
                
                plt.text(midX + dx * rad,
                         midY + dy * rad,
                         data['label'],
                         fontsize=8,
                         horizontalalignment='center')
                
                #portLabels = data['label'].split('=')
                #offset = 0.03
                
                #plt.text(midX + dx * rad - offset, midY + dy * rad - offset, portLabels[0], fontsize=8, horizontalalignment='right', verticalalignment='top')
                #plt.text(midX + dx * rad + offset, midY + dy * rad + offset, portLabels[1], fontsize=8, horizontalalignment='left', verticalalignment='bottom')
                
    legendHandles = [
        mpatches.Patch(color='red', label='Router'),
        mpatches.Patch(color='yellow', label='L2Switch'),
        mpatches.Patch(color='orange', label='L3Switch'),
        mpatches.Patch(color='green', label='Server'),
        mpatches.Patch(color='lightblue', label='PC'),
        mpatches.Patch(color='purple', label='Firewall'),
        Line2D([0], [0], color='green', lw=3, label='Active Link'),
        Line2D([0], [0], color='red', lw=3, label='Inactive Link'),
    ]
    plt.legend(handles=legendHandles, loc='best')
    
    plt.title("Network Topology")
    plt.show()