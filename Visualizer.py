import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from IpCalcClass import IpCalc

def visualizer(devices):
    G = nx.MultiGraph()

    for device in devices.values():
        portInfo = []

        # --- Port IPs (existing logic) ---
        if device.canHaveIP:
            for port, data in device.ports.items():
                if data["ip"]:
                    prefix = IpCalc.subnetToPrefix(data["subnet"])
                    ipClass = IpCalc(data["ip"]).ipClass()
                    ipType = IpCalc(data["ip"]).ipType()

                    portInfo.append(
                        f"{port}: {data['ip']}{prefix} ({ipClass}, {ipType})"
                    )

        # --- VLAN IPs (NEW for L3 switches) ---
        if device.deviceType == "L3Switch":
            for vlan_id, vlan_data in device.vlans.items():
                if vlan_data.get("ip"):
                    prefix = IpCalc.subnetToPrefix(vlan_data.get("subnet"))
                    portInfo.append(
                        f"VLAN {vlan_id}: {vlan_data['ip']}{prefix}"
                    )

        # Final label decision
        IPlabel = "\n".join(portInfo) if portInfo else ""

        label = f"{device.name}\n({device.deviceType})\n{IPlabel}\n{device.state.upper()}"
        G.add_node(device.name, label=label)

    addedConnections = set()
                    
    for device in devices.values():
        for port, data in device.ports.items():
            connection = data["connection"]

            if connection is not None:
                connDevice = connection[0]
                connPort = connection[1]

                if hasattr(connDevice, "name"):
                    connDeviceName = connDevice.name
                else:
                    connDeviceName = connDevice

                # EtherChannel labels
                portLabel = data.get("etherchannel") or port

                otherDevice = devices[connDeviceName]
                otherPortData = otherDevice.ports[connPort]
                connPortLabel = otherPortData.get("etherchannel") or connPort

                cableKey = tuple(sorted([
                    (device.name, portLabel),
                    (connDeviceName, connPortLabel)
                ]))

                if cableKey not in addedConnections:
                    G.add_edge(
                        device.name,
                        connDeviceName,
                        label=f"{portLabel} ↔ {connPortLabel}"
                    )
                    addedConnections.add(cableKey)

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

    plt.figure(figsize=(14, 9))
    for device in devices.values():
        if device.deviceType == "Router":
            G.nodes[device.name]["layer"] = 0
        elif device.deviceType == "Firewall":
            G.nodes[device.name]["layer"] = 1
        elif device.deviceType == "L3Switch":
            G.nodes[device.name]["layer"] = 2
        elif device.deviceType == "L2Switch":
            G.nodes[device.name]["layer"] = 3
        else:
            G.nodes[device.name]["layer"] = 4
            
    pos = nx.spring_layout(G, k=2, iterations=100, seed=77)
    for node in pos:
        layer = G.nodes[node]["layer"]
        pos[node] = (pos[node][0], -layer)

    labels = nx.get_node_attributes(G, 'label')

    nx.draw_networkx_nodes(G, pos, node_size=4000, node_color=colourMap)
    nx.draw_networkx_labels(G, pos, labels, font_size=7)

    for u, v, key, data in G.edges(keys=True, data=True):
        deviceU = devices[u]
        deviceV = devices[v]

        # Determine edge color
        if deviceU.state == "on" and deviceV.state == "on":
            edge_color = "green"
        else:
            edge_color = "red"

        # Count how many edges exist between these nodes
        all_edges = G.get_edge_data(u, v)
        num_edges = len(all_edges)

        # Offset edges if there are multiple
        if num_edges == 1:
            rad = 0  # straight line
        else:
            # Spread edges evenly, e.g., [-0.2, 0, 0.2] for 3 edges
            keys = list(all_edges.keys())
            index = keys.index(key)
            step = 0.2
            start = -step * (num_edges - 1) / 2
            rad = start + index * step

        nx.draw_networkx_edges(
            G,
            pos,
            edgelist=[(u, v)],
            edge_color=edge_color,
            width=2,
            connectionstyle=f"arc3,rad={rad}"
        )

        # Edge labels
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        midX = (x1 + x2) / 2
        midY = (y1 + y2) / 2
        dx = y2 - y1
        dy = x1 - x2

        plt.text(
            midX + dx * rad,
            midY + dy * rad,
            data["label"],
            fontsize=6,
            horizontalalignment="center"
        )

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