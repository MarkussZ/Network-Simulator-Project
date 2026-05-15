from collections import deque
from Devices import Factory
from IpCalcClass import *
from Visualizer import visualizer
from SQL_Function import *
from tabulate import tabulate
import time

def deviceType(devices):
    while True:
        deviceType = getInput("What device would you like to add (PC, Server, Router, L2Switch, L3Switch, Firewall): ")
        if deviceType is None:
            return
        
        if not Factory.validType(deviceType):
            print("Invalid device type")
            continue
        
        while True:
            name = getInput("What is the device name: ")
            if name is None:
                return
            elif name in devices:
                print("Device already in network")
                continue
            elif name.isdigit():
                print("Name cannot be a number")
                continue
            
            available_models = Factory.getAvailableModels(deviceType)
            model = None
            if available_models:
                while True:
                    model = getInput(f"Choose a model {available_models}: ")
                    if model is None:
                        return
                    if model in available_models:
                        break
                    print("Invalid model. Please choose from the list.")
            
            device = Factory.buildDevice(deviceType, name, model)
            devices[name] = device
            print(f"{device.deviceType} '{device.name}' (model {device.model}) added to the network")
            return

def assignIP(devices):
    while True:
        if not devices:
            print("No devices to assign IP addresses to")
            return

        print("\nDevices on the network:")
        for name, dev in devices.items():
            print(name)

        deviceName = getInput("Select a device to assign an IP to: ")
        if deviceName is None:
            return
        if deviceName not in devices:
            print("Device doesn't exist. Please add it first")
            continue

        device = devices[deviceName]
        if not device.canHaveIP:
            print("This device type cannot have IP addresses")
            return

        # Choose between port or EtherChannel
        choice = getInput("Assign IP to a (P)ort or (E)therChannel pr (V)lan? [P/E/V]: ")
        if choice is None:
            return
        choice = choice.strip().lower()
        if choice not in ["p", "e", "v"]:
            print("Invalid choice, enter 'P' for port or 'E' for EtherChannel or 'V' for VLAN")
            continue

        if choice == "p":
            # Assign IP to individual port
            available_ports = [p for p, data in device.ports.items() if data.get("etherchannel") is None]
            if not available_ports:
                print("No available ports to assign an IP (all ports are EtherChannel members)")
                return

            print("\nAvailable ports:")
            for port in available_ports:
                print(port)

            portName = getInput("Select port to assign IP to: ")
            if portName is None:
                return
            portName = portName.lower()
            if portName not in available_ports:
                print("Invalid port or port is part of an EtherChannel")
                continue

            port = device.ports[portName]
            target = port  # IP will be assigned here

        elif choice == "e":  # choice == 'e'
            if not device.etherchannels:
                print(f"No EtherChannels exist on {device.name}")
                return

            print("\nAvailable EtherChannels:")
            for po, data in device.etherchannels.items():
                members = ", ".join(data["members"])
                ip = data.get("ip", "Not assigned")
                print(f"{po}: Members [{members}], IP: {ip}")

            poName = getInput("Select EtherChannel to assign IP to: ")
            if poName is None:
                return
            if poName not in device.etherchannels:
                print("Invalid EtherChannel")
                continue

            target = device.etherchannels[poName]  # IP will be assigned here
            
        elif choice == "v":  # assign IP to VLAN interface
            if not device.vlans:
                print(f"No VLANs exist on {device.name}")
                return

            print("\nAvailable VLANs:")
            for vlanID, vlanData in device.vlans.items():
                ip = vlanData.get("ip", "Not assigned")
                print(f"VLAN {vlanID}: IP {ip}")

            vlan_input = getInput("Select VLAN to assign IP: ")
            if vlan_input is None or not vlan_input.isdigit():
                print("Invalid VLAN selection")
                return

            vlanID = int(vlan_input)

            if vlanID not in device.vlans:
                print("Invalid VLAN")
                return

            target = device.vlans[vlanID]  # now safe to assign IP

        # --- IP Assignment ---
        while True:
            ip = getInput("Enter IP address: ")
            if ip is None:
                return

            # Check if IP is already in use
            ip_in_use = False
            for dev in devices.values():
                # Check ports
                for pdata in dev.ports.values():
                    if pdata.get("ip") == ip:
                        ip_in_use = True
                        break
                # Check EtherChannels
                for edata in dev.etherchannels.values():
                    if edata.get("ip") == ip:
                        ip_in_use = True
                        break
                # Check VLANs
                for vdata in dev.vlans.values():
                    if vdata.get("ip") == ip:
                        ip_in_use = True
                        break
                if ip_in_use:
                    break

            if ip_in_use:
                print(f"IP {ip} is already in use. Choose a different IP.")
                continue

            try:
                calc = IpCalc(ip)
                target["ip"] = calc.ipAddress
                target["ipType"] = calc.ipType()
                target["ipClass"] = calc.ipClass()
                print("IP set to:", calc.ipAddress)
                break
            except ValueError as e:
                print("Invalid IP:", e)
                continue

        # --- Subnet Assignment ---
        while True:
            subnet = getInput("Enter subnet mask or prefix (e.g., /24 or 255.255.255.0): ")
            if subnet is None:
                return
            if subnet.startswith("/"):
                prefix = subnet[1:]
                if not prefix.isdigit():
                    print("Invalid prefix")
                    continue
                subnetObj = prefixes(prefix)
                subnetMask = subnetObj.preToSub()
                if not subnetMask:
                    print("Invalid prefix range")
                    continue
                target["subnet"] = subnetMask
            else:
                try:
                    calc = IpCalc(subnet)
                    if not calc.subnetChecker():
                        print("Invalid subnet mask")
                        continue
                    target["subnet"] = calc.ipAddress
                except ValueError:
                    print("Invalid subnet mask")
                    continue
            break

        # --- Network/Broadcast Validation ---
        result = IpCalc.calculateNetwork(target["ip"], target["subnet"])
        if result["IP Int"] == result["Network Int"] or result["IP Int"] == result["Broadcast Int"]:
            print("IP cannot be network or broadcast address")
            continue
        if result["Broadcast Int"] - result["Network Int"] <= 1:
            print("Subnet too small for usable hosts")
            continue

        print("Network Address:", result["Network"])
        print("Broadcast Address:", result["Broadcast"])
        print("Valid Host Range:", result["First Host"], "-", result["Last Host"])

        wildcard = IpCalc.wildcardMask(target["subnet"])
        target["wildcard"] = wildcard
        print("Wildcard Mask:", wildcard)

        # --- Default Gateway ---
        if device.canHaveGateway:
            suggested = IpCalc.defaultGateway(target["ip"], target["subnet"])
            print("Suggested Default Gateway:", suggested)
            while True:
                gateway = getInput("Enter default gateway (press Enter for suggested): ")
                if gateway is None or gateway.strip() == "":
                    gateway = suggested
                try:
                    netIP = IpCalc.calculateNetwork(target["ip"], target["subnet"])["Network"]
                    netGate = IpCalc.calculateNetwork(gateway, target["subnet"])["Network"]
                    if netIP != netGate:
                        print("Gateway must be in the same subnet")
                        continue
                    target["gateway"] = gateway
                    print(f"Default Gateway set to {gateway}")
                    return
                except ValueError:
                    print("Invalid gateway IP")
        else:
            target["gateway"] = None
            return
            

def displayDevices(devices):
    if not devices:
        print("No devices on the network")
        return

    for device in devices.values():
        print(f"\n Name: {device.name}")
        print(f" Device Type: {device.deviceType}")
        print(f" IPv6 Address: {device.ipv6 or 'Not assigned'}")
        print(f" Model: {device.model or 'N/A'}")

        #print("\nAvailable Ports:")
        #print(device.showPorts())

        # ---- EtherChannels ----
        if device.etherchannels:
            print("\nEtherChannels:")
            print(f"{'Po':6} | {'IP Address':18} | Connection | Members | Status")
            print("-" * 70)

            for po, data in device.etherchannels.items():
                if not device.canHaveIP:
                    ipInfo = "N/A"
                else:
                    ip = data.get("ip") or "No IP"
                    subnet = data.get("subnet") or ""
                    ipInfo = f"{ip}/{subnet}" if subnet else ip

                connection = data.get("connected_to") or "Not connected"
                members = ", ".join(data.get("members") or [])
                status = data.get("status") or "down"

                print(f"{str(po):6} | {str(ipInfo):18} | {str(connection):10} | {str(members):15} | {str(status)}")


        # ---- VLANs (ALWAYS SHOW IF PRESENT) ----
        if hasattr(device, "vlans") and device.vlans:
            print("\nVLANs:")
            print(f"{'VLAN':6} | {'Name':12} | {'IP Address':18} | Ports")
            print("-" * 60)

            for vlanID, vlanData in device.vlans.items():
                name = vlanData.get("name", "")
                ip = vlanData.get("ip") or "No IP"
                subnet = vlanData.get("subnet") or ""
                ipInfo = f"{ip}/{subnet}" if subnet else ip
                ports = ", ".join(vlanData.get("ports", [])) or "-"

                print(f"{str(vlanID):6} | {name:12} | {ipInfo:18} | {ports}")

        # ---- Ports Table ----
        print("\nPorts:")
        print(f"{'Port':6} | {'IP Address':18} | {'VLAN':10} | Connection")
        print("-" * 70)
        
        # ---- HSRP (ONLY FOR L3 SWITCHES) ----
        if isinstance(device, L3Switch) and device.hsrp_groups:
            print("\nHSRP:")
            print(f"{'VLAN':6} | {'Virtual IP':15} | {'Priority':8} | State")
            print("-" * 50)

            for vlanID, group in device.hsrp_groups.items():
                if not group or "virtual_ip" not in group:
                    continue

                vip = group.get("virtual_ip") or "N/A"
                priority = group.get("priority") or "-"
                state = group.get("state") or "unknown"

                state_display = "ACTIVE" if state == "active" else "standby"

                print(f"{str(vlanID):6} | {vip:15} | {str(priority):8} | {state_display}")

            print("\n")  # 👈 IMPORTANT separator

        for port, data in device.ports.items():
            # Skip unused ports without IP or connection
            if data["connection"] is None and data["ip"] is None and data.get("etherchannel") is None:
                continue

            # IP info
            if not device.canHaveIP:
                ipInfo = "N/A"
            else:
                ip = data.get("ip") or "No IP"
                subnet = data.get("subnet") or ""
                ipInfo = f"{ip}/{subnet}" if subnet else ip

            # Connection info
            connection = data.get("connection")
            if connection is None:
                connInfo = "Not connected"
            else:
                # Handle 2- or 3-element tuples (peer, peerPort[, Po])
                if len(connection) == 3:
                    peer, peerPort, po = connection
                    connInfo = f"{peer}:{peerPort} (Po: {po})"
                else:
                    peer, peerPort = connection
                    connInfo = f"{peer}:{peerPort}"

            # VLAN display: trunk vs access
            if data.get("trunk"):
                vlanDisplay = "trunk"
            else:
                vlanDisplay = str(data.get("vlan") or "-")

            # Mark if the port is part of an EtherChannel
            etherch = data.get("etherchannel")
            if etherch:
                vlanDisplay += f" (Po: {etherch})"

            print(f"{port:6} | {ipInfo:18} | {vlanDisplay:10} | {connInfo}")

def deleteDevices(devices):
    if not devices:
        print("No devices to remove")
        return
    print("\nDevices on the network:")
    for name in devices:
        print(name)
    while True:
        name = getInput("\nEnter what device you want to remove: ")
        if name is None:
            return
        
        
        if name not in devices:
            print("Device not found")
            continue
        while True:
            confirm = input(f"Are you sure you want to remove {name}? (y/n): ")

            if confirm == "y":
                break
            elif confirm == "n":
                print("Removal cancelled")
                return
            else:
                print("Please enter 'y' or 'n'")
        
        print(f"{devices[name].deviceType} '{devices[name].name}' has been removed from the network")
        del devices[name] #deletes object
        return

def power(devices):
    if not devices:
        print("No devices to power on/off")
        return
    print("\nDevices on the network:")
    for device in devices.values():
        print(f"{device.name} : ({device.state})")
    while True:
        deviceName = getInput("Which device are you powering on/off ")
        if deviceName is None:
            return
        
        if deviceName not in devices:
            print("Device doesn't exist. Please add the device in first")
            continue
        
        device = devices[deviceName]
        
        if device.state == "off":
            device.state = "on"
            print(f"{device.name} is now ON")
            return
        elif device.state == "on":
            device.state = "off"
            print(f"{device.name} is now OFF")
            return
        
def connect(devices):
    if not devices or len(devices) < 2:
        print("Not enough devices on the network")
        return

    print("\nDevices on the network:")
    for name in devices:
        print(name)

    # --- Select first device and port ---
    while True:
        device1_name = getInput("What device do you want to connect from: ")
        if device1_name is None:
            return
        if device1_name not in devices:
            print("Device doesn't exist. Please add it first")
            continue
        device1 = devices[device1_name]

        print("\nAvailable ports:")
        for port, data in device1.ports.items():
            status = "free" if data["connection"] is None else "used"
            print(f"{port} ({status})")

        port1 = getInput("What port do you want to use: ")
        if port1 is None:
            return
        port1 = port1.lower()
        if port1 not in device1.ports:
            print("This port does not exist on this device")
            continue
        if device1.ports[port1]["connection"] is not None:
            print("Port already taken")
            continue
        break

    # --- Select second device and port ---
    while True:
        device2_name = getInput("What device do you want to connect to: ")
        if device2_name is None:
            return
        if device2_name not in devices:
            print("Device doesn't exist. Please add it first")
            continue
        if device2_name == device1_name:
            print("Cannot connect device to itself")
            continue
        device2 = devices[device2_name]

        print("\nAvailable ports:")
        for port, data in device2.ports.items():
            status = "free" if data["connection"] is None else "used"
            print(f"{port} ({status})")

        port2 = getInput("What port do you want to use: ")
        if port2 is None:
            return
        port2 = port2.lower()
        if port2 not in device2.ports:
            print("This port does not exist on this device")
            continue
        if device2.ports[port2]["connection"] is not None:
            print("Port already taken")
            continue
        break

    # --- Connect the ports ---
    device1.ports[port1]["connection"] = (device2_name, port2)
    device2.ports[port2]["connection"] = (device1_name, port1)
    print(f"\nConnected {device1_name}:{port1} to {device2_name}:{port2}")

    # --- Automatic trunking / VLAN updates ---
    # If connecting switch to switch/router/firewall → mark ports as trunk
    switch_types = ["L2Switch", "L3Switch"]
    other_types = ["Router", "Firewall"]

    # If connecting switch to switch/router/firewall → mark ports as trunk
    if (device1.deviceType in switch_types and device2.deviceType in switch_types + other_types) or \
       (device2.deviceType in switch_types and device1.deviceType in switch_types + other_types):
        device1.ports[port1]["trunk"] = True
        device2.ports[port2]["trunk"] = True
        print(f"Ports {device1_name}:{port1} and {device2_name}:{port2} set to trunk mode")

    # --- Update PC VLAN if connected to a switch access port ---
    if device1.deviceType == "PC" and device2.deviceType in switch_types:
        # only assign VLAN if switch port is not trunk
        if not device2.ports[port2].get("trunk"):
            device1.vlan = device2.ports[port2].get("vlan")
            device1.ports[port1]["vlan"] = device1.vlan
            print(f"{device1.name} VLAN set to {device1.vlan} to match {device2_name}:{port2}")

    elif device2.deviceType == "PC" and device1.deviceType in switch_types:
        if not device1.ports[port1].get("trunk"):
            device2.vlan = device1.ports[port1].get("vlan")
            device2.ports[port2]["vlan"] = device2.vlan
            print(f"{device2.name} VLAN set to {device2.vlan} to match {device1_name}:{port1}")
    
def etherChannel(devices):
    if not devices:
        print("No devices on the network")
        return
    
    while True:
        print("\nDevices on the network:")
        for name, dev in devices.items():
            print(f"{name} ({dev.deviceType})")

        # Select first device
        while True:
            device1 = getInput("Select the first device for EtherChannel: ")
            if device1 is None:
                return
            if device1 not in devices:
                print("Device doesn't exist")
                continue
            d1 = devices[device1]
            if d1.deviceType.lower() in ["pc", "server", "firewall"]:
                print(f"{d1.deviceType} cannot be part of an EtherChannel")
                continue
            break

        # Select second device
        while True:
            device2 = getInput("Select the second device for EtherChannel: ")
            if device2 is None:
                return
            if device2 not in devices:
                print("Device doesn't exist")
                continue
            if device2 == device1:
                print("Cannot EtherChannel a device with itself")
                continue
            d2 = devices[device2]
            if d2.deviceType.lower() in ["pc", "server", "firewall"]:
                print(f"{d2.deviceType} cannot be part of an EtherChannel")
                continue
            break
        
        alreadyExists = False
        for port in d1.ports.values():
            conn = port["connection"]
            if conn and len(conn) == 3 and conn[0] == d2.name:
                alreadyExists = True
                break

        if alreadyExists:
            print("An EtherChannel already exists between these devices")
            continue

        # Find connected ports between the two devices
        allowedPorts1 = [p for p, data in d1.ports.items()
                         if data["connection"] is not None and data["connection"][0] == d2.name]
        allowedPorts2 = [p for p, data in d2.ports.items()
                         if data["connection"] is not None and data["connection"][0] == d1.name]

        if not allowedPorts1 or not allowedPorts2:
            print(f"No existing connection between {d1.name} and {d2.name} to create EtherChannel")
            return

        if len(allowedPorts1) < 2 or len(allowedPorts2) < 2:
            print("EtherChannel requires at least 2 ports on each device")
            return

        print(f"\nPorts on {d1.name} connected to {d2.name}: {allowedPorts1}")
        print(f"Ports on {d2.name} connected to {d1.name}: {allowedPorts2}")
        
        while True:
            ports1Input = getInput(f"Select ports on {d1.name} to include in EtherChannel (comma-separated): ")
            if ports1Input is None:
                return
            ports1 = [p.strip().lower() for p in ports1Input.split(",")]
            
            if len(set(ports1)) != len(ports1):
                print("Duplicate ports are not allowed")
                continue
                        
            if all(p in allowedPorts1 for p in ports1):
                break

            print("One or more selected ports are invalid")
        while True:
            ports2Input = getInput(f"Select ports on {d2.name} to include in EtherChannel (comma-separated): ")
            if ports2Input is None:
                return
            ports2 = [p.strip().lower() for p in ports2Input.split(",")]
            
            if len(set(ports2)) != len(ports2):
                print("Duplicate ports are not allowed")
                continue
                        
            
            if all(p in allowedPorts2 for p in ports2):
                break

            print("One or more selected ports are invalid")
            
        if len(ports1) < 2 or len(ports2) < 2:
            print("EtherChannel requires at least 2 ports on each device")
            continue

        if len(ports1) != len(ports2):
            print("Number of ports must match for EtherChannel")
            continue

        groupName = Device.getNextGlobalPoNumber(devices)

        # Create EtherChannel on both devices
        d1.etherchannels[groupName] = {
            "members": ports1,
            "connected_to": d2.name,
            "status": "up",
            "ip": None,
            "subnet": None,
            "gateway": None
        }

        d2.etherchannels[groupName] = {
            "members": ports2,
            "connected_to": d1.name,
            "status": "up",
            "ip": None,
            "subnet": None,
            "gateway": None
        }

        # Assign ports to EtherChannel (Device 1)
        for p in ports1:
            if d1.ports[p]["etherchannel"] is not None:
                print(f"Port {p} on {d1.name} is already in an EtherChannel")
                return

            d1.ports[p]["etherchannel"] = groupName
            d1.ports[p]["ip"] = None
            d1.ports[p]["subnet"] = None
            d1.ports[p]["gateway"] = None

        # Assign ports to EtherChannel (Device 2)
        for p in ports2:
            if d2.ports[p]["etherchannel"] is not None:
                print(f"Port {p} on {d2.name} is already in an EtherChannel")
                return

            d2.ports[p]["etherchannel"] = groupName
            d2.ports[p]["ip"] = None
            d2.ports[p]["subnet"] = None
            d2.ports[p]["gateway"] = None

        print(f"\nEtherChannel '{groupName}' created between {d1.name} ports {ports1} and {d2.name} ports {ports2}")

        return
    
    
def ping(devices):
    if not devices:
        print("No devices on the network")
        return
    if len(devices) < 2:
        print("Not enough devices on the network")
        return

    print("\nDevices on the network:")
    for name in devices:
        print(name)

    # --- Select source device ---
    device1, p1 = select_device_port(devices, "ping from")
    if not device1: return

    # --- Select destination device ---
    device2, p2 = select_device_port(devices, "ping to")
    if not device2: return

    print("\nChecking network connectivity and route...")

    src_ip = p1["ip"]
    dst_ip = p2["ip"]

    visited = set()
    # Queue entries: (current_device, path_taken)
    queue = deque([(device1, [device1.name])])
    found = False
    final_path = []

    while queue:
        current_dev, path = queue.popleft()
        visited.add(current_dev.name)

        # Gather all IP interfaces for routing (ports, EtherChannels, VLANs)
        interfaces = []
        for data in list(current_dev.ports.values()) + list(current_dev.etherchannels.values()):
            if data.get("ip") and data.get("subnet"):
                interfaces.append(data)
        if hasattr(current_dev, "vlans"):
            for vlan in current_dev.vlans.values():
                if vlan.get("ip") and vlan.get("subnet"):
                    interfaces.append(vlan)

        # Check if destination IP is in any interface's subnet
        for iface in interfaces:
            if IpCalc.ipInNetwork(dst_ip, iface["ip"], iface["subnet"]):
                final_path = path + [current_dev.name + f"({iface['ip']})"]
                found = True
                break
        if found:
            break

        # Enqueue all physically connected neighbors (L2 & L3)
        for port, data in current_dev.ports.items():
            conn = data.get("connection")
            if conn:
                neighbor_name = conn[0]
                neighbor_dev = devices.get(neighbor_name)
                if neighbor_dev and neighbor_dev.name not in visited:
                    queue.append((neighbor_dev, path + [neighbor_dev.name]))

        for po, data in current_dev.etherchannels.items():
            neighbor_name = data.get("connected_to")
            if neighbor_name:
                neighbor_dev = devices.get(neighbor_name)
                if neighbor_dev and neighbor_dev.name not in visited:
                    queue.append((neighbor_dev, path + [neighbor_dev.name]))

    if not found:
        print(f"Ping failed: no route from {device1.name} to {device2.name}")
        return

    # Print the traced route
    print("\nRoute taken:")
    print(" → ".join(final_path))

    # Simulate ping replies
    print(f"\nPinging {dst_ip} with 32 bytes of data:")
    for _ in range(4):
        time.sleep(1)
        print(f"Reply from {dst_ip}: bytes=32 time=1ms")

    print(f"Ping successful! {device1.name} can reach {device2.name}")


def select_device_port(devices, action_str):
    """
    Helper to select a device and port/EtherChannel with IP/subnet
    Returns (device_object, port_data)
    """
    while True:
        device_name = getInput(f"What device do you want to {action_str}: ")
        if device_name is None:
            return None, None
        if device_name not in devices:
            print("Device doesn't exist. Please add the device first")
            continue

        dev = devices[device_name]
        if dev.state != "on":
            print(f"{dev.name} is powered off")
            continue

        valid_ports = []
        print("\nAvailable ports with IPs:")
        for port, data in dev.ports.items():
            if data.get("ip"):
                print(f"{port} ({data['ip']})")
                valid_ports.append(port)
        if dev.etherchannels:
            print("\nAvailable EtherChannels with IPs:")
            for po, data in dev.etherchannels.items():
                if data.get("ip"):
                    print(f"{po} ({data['ip']})")
                    valid_ports.append(po)

        if not valid_ports:
            print(f"{dev.name} has no ports or EtherChannels with IP addresses")
            return None, None

        port_name = getInput(f"Which port or EtherChannel are you pinging {action_str}: ")
        if port_name is None:
            return None, None
        if port_name not in dev.ports and port_name not in dev.etherchannels:
            print("Invalid port or EtherChannel")
            continue

        if port_name in dev.ports:
            port_data = dev.ports[port_name]
        else:
            port_data = dev.etherchannels[port_name]

        if not port_data.get("ip") or not port_data.get("subnet"):
            print("Selected interface missing IP or subnet")
            continue

        return dev, port_data
    
    
    
def disconnect(devices):
    connections = getConnections(devices)
    
    if not devices:
        print("No devices on the network")
        return
    if not connections:
        print("No connections on the network")
        return
    
    while True:
        devName = getInput("What device would you like to disconnect: ")
        if devName is None:
            return
        if devName not in devices:
            print("Device name not found")
            continue

        device = devices[devName]

        # Only ports that actually have connections
        ports = {
            p: data for p, data in device.ports.items()
            if data["connection"] is not None
        }

        if not ports:
            print("This device does not have any active connections")
            return

        print("Connected ports:")
        for p in ports:
            print(p)

        break

    while True:
        portName = getInput("What port do you want to disconnect: ")
        if portName is None:
            return
        portName = portName.lower()

        if portName not in device.ports:
            print("Port doesn't exist on this device")
            continue

        if device.ports[portName]["connection"] is None:
            print("Port has no active connections")
            continue

        break

    # Get connection info
    neighbourName, neighbourPort = device.ports[portName]["connection"]

    # Remove both sides
    device.ports[portName]["connection"] = None
    devices[neighbourName].ports[neighbourPort]["connection"] = None

    print(f"Disconnected {devName}:{portName} from {neighbourName}:{neighbourPort}")
    
def removeEtherChannel(devices):
    if not devices:
        print("No devices on the network")
        return

    # List devices with EtherChannels
    devicesWithPo = [d for d in devices.values() if d.etherchannels]
    if not devicesWithPo:
        print("No EtherChannels exist on any device")
        return

    print("\nDevices with EtherChannels:")
    for d in devicesWithPo:
        print(f"{d.name}: {', '.join(d.etherchannels.keys())}")

    while True:
        devName = getInput("Select a device to remove an EtherChannel from: ")
        if devName is None:
            return
        if devName not in devices:
            print("Device not found")
            continue
        device = devices[devName]
        if not device.etherchannels:
            print("Device has no EtherChannels")
            continue
        break

    while True:
        poName = getInput(f"Select EtherChannel to remove from {devName} ({', '.join(device.etherchannels.keys())}): ")
        if poName is None:
            return
        if poName not in device.etherchannels:
            print("Invalid EtherChannel name")
            continue
        break

    # Get connected device
    connectedTo = device.etherchannels[poName]["connected_to"]
    if connectedTo not in devices:
        print(f"Connected device {connectedTo} not found")
        return
    otherDevice = devices[connectedTo]

    # Remove EtherChannel from both devices
    for p in device.etherchannels[poName]["members"]:
        # Reset EtherChannel
        device.ports[p]["etherchannel"] = None
        # Reset connection if it includes the EtherChannel
        conn = device.ports[p]["connection"]
        if conn is not None and len(conn) == 3:
            device.ports[p]["connection"] = conn[:2]  # keep only (peer, peerPort)
    for p in otherDevice.etherchannels.get(poName, {}).get("members", []):
        otherDevice.ports[p]["etherchannel"] = None
        conn = otherDevice.ports[p]["connection"]
        if conn is not None and len(conn) == 3:
            otherDevice.ports[p]["connection"] = conn[:2]

    device.etherchannels.pop(poName)
    otherDevice.etherchannels.pop(poName, None)

    print(f"Removed EtherChannel {poName} between {devName} and {connectedTo}")
    
def getConnections(devices):
    connections = set()
    seen = set()
    
    if not devices:
        return connections

    for device in devices.values():
        for portName, portData in device.ports.items():
            connection = portData["connection"]
            
            if connection is None:
                continue
            
            connDevice, connPort = connection
            
            connectionID = tuple(sorted([
                (device.name, portName),
                (connDevice, connPort)
            ]))
            
            if connectionID in seen:
                continue
            
            seen.add(connectionID)
            connections.add(connectionID)
                
    return connections

def showConnections(devices):
    connections = getConnections(devices)

    if not connections:
        print("No connections on the network")
        return

    print("\nConnections on the network:")

    seen = set()  # track displayed connections to avoid duplicates

    for (d1, p1), (d2, p2) in connections:
        dev1 = devices[d1]
        dev2 = devices[d2]

        # Use EtherChannel if exists
        p1_label = dev1.ports[p1].get("etherchannel") or p1
        p2_label = dev2.ports[p2].get("etherchannel") or p2

        # Make a unique key for deduplication
        conn_key = tuple(sorted([
            (d1, p1_label),
            (d2, p2_label)
        ]))

        if conn_key in seen:
            continue  # skip duplicates

        seen.add(conn_key)
        print(f"{d1}:{p1_label} <--> {d2}:{p2_label}")

def showVisual(devices):
    if not devices:
        print("No devices on the network")
        return
    visualizer(devices)
    return

def connectToSQL():
    connectToDatabase()

def createDatabaseTable(devices=None):
    if dbConfig["host"] == None or dbConfig["user"] == None or dbConfig["password"] == None:
        print("No SQL connection made")
        return
    dbCreated = createDatabase()
    if dbConfig["database"] == None:
        print("Database cannot be null")
        return
    tableCreated = prepareDatabase()
    
    if dbCreated and tableCreated:
        message = "Database and Tables have been created"
    elif dbCreated and not tableCreated:
        message = "Database created. Tables already exists"
    elif not dbCreated and tableCreated:
        message = "Database already exists. Tables has been created"
    else:
        message = "Database and Tables already exist"
        
    print(message)
    
    #if devices:
        #saveNetwork(devices) used to automatically populate table

def saveNetwork(devices):
    if not devices:
        print("No devices on the network")
        return
    if dbConfig["database"] == None:
        print("No database selected")
        return
    saveDevices(devices)
    savePorts(devices)
    saveConnections(devices)
    saveEtherChannels(devices)
    saveVLANs(devices)
    saveHSRP(devices)
    print("Network saved to database")
    return

def showTable():
    if dbConfig["database"] is None:
        print("No database selected")
        return

    print("\nDEVICES TABLE:")
    deviceRows = getDevices()
    if deviceRows:
        print(tabulate(deviceRows, headers="keys", tablefmt="grid"))
    else:
        print("No device data found")


    print("\nPORTS TABLE:")
    portRows = getPorts()
    if portRows:
        print(tabulate(portRows, headers="keys", tablefmt="grid"))
    else:
        print("No port data found")

    print("\nCONNECTIONS TABLE:")
    connectionRows = getConnectionsInSQL()
    if connectionRows:
        print(tabulate(connectionRows, headers="keys", tablefmt="grid"))
    else:
        print("No connection data found")
        
    print("\nETHERCHANNEL TABLE:")
    etherRows = getEtherchannels()
    if etherRows:
        print(tabulate(etherRows, headers="keys", tablefmt="grid"))
    else:
        print("No etherchannel data found")
        
    print("\nVLAN TABLE:")
    vlanRows = getVlans()
    if vlanRows:
        print(tabulate(vlanRows, headers="keys", tablefmt="grid"))
    else:
        print("No VLAN data found")
        
    print("\nHSRP TABLE:")
    hsrpRows = getHSRP()
    if hsrpRows:
        print(tabulate(hsrpRows, headers="keys", tablefmt="grid"))
    else:
        print("No HSRP data found")
    
def loadInto(devices):
    if dbConfig["database"] == None:
        print("No database selected")
        return
    loadedDevices = loadNetwork()
    if not loadedDevices:
        print("No devices to upload")
        return
    devices.clear()
    devices.update(loadedDevices)
    print("Network Successfully loaded from Database")
    
def configureVLAN(devices):
    if not devices:
        print("No devices on the network")
        return

    # Show all switches
    switches = {name: dev for name, dev in devices.items() if dev.deviceType.lower() in ["l2switch", "l3switch"]}
    if not switches:
        print("No switches available to configure VLANs")
        return

    print("\nSwitches on the network:")
    for name in switches:
        print(name)

    # Select switch
    while True:
        switch_name = getInput("Select a switch to configure VLANs: ")
        if switch_name is None:
            return
        if switch_name not in switches:
            print("Switch not found")
            continue
        switch = switches[switch_name]
        break

    # Show existing VLANs
    if switch.vlans:
        print("\nExisting VLANs on this switch:")
        for vlan_id, info in switch.vlans.items():
            ports = ", ".join(info.get("ports", []))
            ip = info.get("ip", "N/A")
            print(f"VLAN {vlan_id} -> Ports: {ports}, IP: {ip}")
    else:
        print("\nNo VLANs configured yet")

    # Menu for VLAN actions
    while True:
        print("\nVLAN Menu:")
        print("1. Add VLAN")
        print("2. Assign ports to VLAN")
        print("3. Delete VLAN")
        print("X. Exit VLAN Menu")

        choice = getInput("Select an option: ")
        if choice is None or choice.lower() == "x":
            return

        # ---- Add VLAN ----
        if choice == "1":
            vlan_id = getInput("Enter VLAN ID (number): ")
            if not vlan_id:
                return
            elif not vlan_id.isdigit():
                print("VLAN ID must be a number")
                continue
            vlan_id = int(vlan_id)

            name = getInput("Enter VLAN name (optional): ") or f"VLAN{vlan_id}"
            if vlan_id in switch.vlans:
                print("VLAN already exists")
                continue

            switch.vlans[vlan_id] = {"name": name, "ports": [], "ip": None, "subnet": None}
            print(f"VLAN {vlan_id} ({name}) added to {switch_name}")

        # ---- Assign ports to VLAN ----
        elif choice == "2":
            if not switch.vlans:
                print("No VLANs to assign ports to")
                continue

            vlan_input = getInput("Enter VLAN ID to assign ports to: ")
            if vlan_input is None or not vlan_input.isdigit():
                print("Invalid VLAN ID")
                continue

            vlan_id = int(vlan_input)

            if vlan_id not in switch.vlans:
                print("VLAN does not exist")
                continue

            print("Available ports:")
            print(", ".join(switch.ports.keys()))

            ports_input = getInput("Enter ports to assign (comma-separated): ")
            if ports_input is None:
                continue

            ports = [p.strip().lower() for p in ports_input.split(",")]

            for port in ports:
                if port not in switch.ports:
                    print(f"{port} does not exist on this switch")
                    continue

                current_vlan = switch.ports[port].get("vlan")

                # Already in same VLAN → skip
                if current_vlan == vlan_id:
                    print(f"{port} is already in VLAN {vlan_id}")
                    continue

                # Remove from old VLAN
                if current_vlan and current_vlan in switch.vlans:
                    if port in switch.vlans[current_vlan]["ports"]:
                        switch.vlans[current_vlan]["ports"].remove(port)

                # Assign new VLAN
                switch.ports[port]["vlan"] = vlan_id
                switch.vlans[vlan_id]["ports"].append(port)

                port_vlan = switch.ports[port]["vlan"]

                # Update connected device if applicable
                conn = switch.ports[port].get("connection")
                if conn:
                    peer_name, peer_port = conn[:2]
                    peer_dev = devices.get(peer_name)
                    if peer_dev:
                        peer_dev.vlan = port_vlan
                        if peer_port in peer_dev.ports:
                            peer_dev.ports[peer_port]["vlan"] = port_vlan
                
        elif choice == "3":
            if not switch.vlans:
                print("No VLANs to delete")
                continue

            print("\nExisting VLANs:")
            for vlanID in switch.vlans:
                print(f"VLAN {vlanID}")

            vlan_input = getInput("Enter VLAN ID to delete: ")
            if vlan_input is None or not vlan_input.isdigit():
                print("Invalid VLAN ID")
                continue

            vlan_id = int(vlan_input)

            if vlan_id not in switch.vlans:
                print("VLAN does not exist")
                continue

            # Clear VLAN from ports
            ports_to_clear = switch.vlans[vlan_id]["ports"][:]
            for port in ports_to_clear:
                switch.ports[port]["vlan"] = None

            # Delete VLAN
            del switch.vlans[vlan_id]

            print(f"VLAN {vlan_id} deleted")

def removeIP(devices):
    if not devices:
        print("No devices available")
        return

    print("\nDevices on the network:")
    for name in devices:
        print(name)

    deviceName = getInput("Select a device: ")
    if deviceName is None or deviceName not in devices:
        print("Invalid device")
        return

    device = devices[deviceName]

    choice = getInput("Remove IP from (P)ort, (E)therChannel, or (V)LAN? [P/E/V]: ")
    if choice is None:
        return
    choice = choice.lower()

    # ---- PORT ----
    if choice == "p":
        ports_with_ip = [p for p, d in device.ports.items() if d.get("ip")]
        if not ports_with_ip:
            print("No ports with IP addresses")
            return

        print("Ports with IPs:")
        for p in ports_with_ip:
            print(p)

        portName = getInput("Select port: ")
        if portName not in ports_with_ip:
            print("Invalid port")
            return

        target = device.ports[portName]

    # ---- ETHERCHANNEL ----
    elif choice == "e":
        ecs = [po for po, d in device.etherchannels.items() if d.get("ip")]
        if not ecs:
            print("No EtherChannels with IPs")
            return

        print("EtherChannels with IPs:")
        for po in ecs:
            print(po)

        poName = getInput("Select EtherChannel: ")
        if poName not in ecs:
            print("Invalid EtherChannel")
            return

        target = device.etherchannels[poName]

    # ---- VLAN ----
    elif choice == "v":
        if not hasattr(device, "vlans") or not device.vlans:
            print("No VLANs on this device")
            return

        vlans_with_ip = [v for v, d in device.vlans.items() if d.get("ip")]
        if not vlans_with_ip:
            print("No VLANs with IP addresses")
            return

        print("VLANs with IPs:")
        for v in vlans_with_ip:
            print(f"VLAN {v}")

        vlan_input = getInput("Select VLAN: ")
        if vlan_input is None or not vlan_input.isdigit():
            print("Invalid VLAN")
            return

        vlanID = int(vlan_input)
        if vlanID not in device.vlans or not device.vlans[vlanID].get("ip"):
            print("Invalid VLAN")
            return

        target = device.vlans[vlanID]

    else:
        print("Invalid selection")
        return

    # ---- Remove IP Info ----
    target["ip"] = None
    target["subnet"] = None
    target["wildcard"] = None
    target["gateway"] = None
    target["ipType"] = None
    target["ipClass"] = None

    print("IP configuration removed successfully")
    
def menu_hsrp(devices):
    switch_name = getInput("Enter the L3 Switch to configure HSRP on: ")
    if not switch_name:
        return
    if switch_name not in devices:
        print("Switch not found")
        return
    
    sw = devices[switch_name]
    if not isinstance(sw, L3Switch):
        print("This device is not an L3 switch")
        return
    
    vlan_input = getInput("Enter VLAN ID for HSRP: ")
    if not vlan_input:
        return
    try:
        vlan_id = int(vlan_input)
    except ValueError:
        print("Invalid VLAN ID")
        return
    
    virtual_ip = getInput("Enter virtual IP for HSRP: ")
    if not virtual_ip:
        return
    try:
        IpCalc(virtual_ip)  # Validate IP
    except ValueError:
        print("Invalid IP address format")
        return
    
    priority_input = getInput("Enter HSRP priority (higher = active): ")
    if not priority_input:
        return
    try:
        priority = int(priority_input)
    except ValueError:
        print("Invalid priority value")
        return
    
    sw.configure_hsrp(vlan_id, virtual_ip, priority)
    sw.determine_hsrp_for_vlan(devices, vlan_id)
    
    print(f"HSRP configured on {sw.name} for VLAN {vlan_id}, virtual IP {virtual_ip}")
    
def getInput(prompt):
    value = input(prompt)
    if not value.strip():
        return None
    return value.strip()

def get_vlan(device, interface):
    if interface in device.ports:
        return device.ports[interface].get("vlan")
    return None