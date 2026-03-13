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
        for name in devices:
            print(name)
        deviceName = getInput("Which device are you assigning an IP to: ")
        if deviceName is None:
            return
        if deviceName not in devices:
            print("Device doesn't exist. Please add the device in first")
            continue
        
        device = devices[deviceName]
        
        while True:
        
            while True:
                ip = getInput("\nPlease enter an IP address: ")
                if ip is None:
                    return

                try:
                    calc = IpCalc(ip)
                    device.ip = calc.ipAddress
                    device.ipType = calc.ipType()
                    device.ipClass = calc.ipClass()
                    print("\nIP:", calc.ipAddress)
                    print("Binary:", calc.ipToBinary())
                    print("IP Class:", calc.ipClass())
                    print("IP Type:", calc.ipType())
                    break

                except ValueError as e:
                    print("Invalid IP:", e)
                    continue
            while True:
                subnet = getInput("\nPlease enter the Subnet Mask or prefix: ")
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
                    device.subnet = subnetMask
                    print("Subnet Mask:", subnetMask)
                    calc = IpCalc(subnetMask)
                    print("Binary:", calc.ipToBinary())
                        
                else:
                    try:
                        calc = IpCalc(subnet)
                            
                        if not calc.subnetChecker():
                            print("Invalid subnet mask")
                            continue
                        device.subnet = calc.ipAddress
                        print("Subnet Mask:", calc.ipAddress)
                        print("Binary:", calc.ipToBinary())
                                
                    except ValueError as e:
                        print("Invalid Subnet Mask:")
                        continue
                break
        
            result = IpCalc.calculateNetwork(device.ip, device.subnet)
            if result["IP Int"] == result["Network Int"]:
                print("IP cannot be the network address")
                continue
            if result ["IP Int"] == result["Broadcast Int"]:
                print("IP cannot be the broadcast address")
                continue
            if result["Broadcast Int"] - result["Network Int"] <= 1:
                print("Subnet too small for usable hosts")
                continue
                    
            print("Network Address:", result["Network"])
            print("Broadcast Address:", result["Broadcast"])
            print("Valid Host Range:",
                        result["First Host"], "-",
                        result["Last Host"])
            wildcard = IpCalc.wildcardMask(device.subnet)
            print("Wildcard Mask:", wildcard)
            device.wildcard = wildcard
            
            suggestGateway = IpCalc.defaultGateway(device.ip, device.subnet)
            print("Suggested Default Gateway", suggestGateway)
            
            while True:
                gateway = getInput("Enter the default gateway IP (press Enter to use suggested gateway)")
                if gateway is None or gateway.strip =="":
                    gateway = suggestGateway
                try:
                    gateCalc = IpCalc(gateway)
                    netIP = IpCalc.calculateNetwork(device.ip, device.subnet)["Network"]
                    netGate = IpCalc.calculateNetwork(gateway, device.subnet)["Network"]
                    if netIP != netGate:
                        print("Gateway must be in the same subnet as the device IP")
                        continue
                    device.gateway = gateway
                    print(f"Default Gateway set tp {device.gateway}")
                    return
                except ValueError:
                    print("Invalid IP address gateway")
            

def displayDevices(devices):
    if not devices:
        print("No devices on the network")
        return
    else:
        for device in devices.values():
            print(f"\n Name: {device.name}")
            print(f" Device Type: {device.deviceType}")
            print(f" IP Address: {device.ip or 'Not assigned'}")
            print(f" Subnet Mask: {device.subnet or 'Not assigned'}")
            print(f" Gateway: {device.gateway or 'Not assigned'}")
            print(f" wildcard: {device.wildcard or 'Not assigned'}")
            print(f" IP Type: {device.ipType or 'Not assigned'}")
            print(f" IP Class: {device.ipClass or 'Not assigned'}")
            print(f" IPv6 Address: {device.ipv6 or 'Not assigned'}")
            print(f" Ports: {device.showPorts()}")
            print(f" Model: {device.model or 'N/A'}")

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
    if not devices:
        print("No devices on the network")
        return
    if len(devices) < 2:
        print("Not enough devices on the network")
        return
    print("\nDevices on the network:")
    for name in devices:
        print(name)
    while True:
        device1 = getInput("What device do you want to connect from: ")
        if device1 is None:
            return
        if device1 not in devices:
            print("Device doesn't exist. Please add the device in first")
            continue
        d1 = devices[device1]
        while True:
            p1 = getInput("What port do you want to use: ")
            if p1 is None:
                return
            p1 = p1.lower()
            if p1 not in d1.ports:
                print("This port does not exist on this device")
                continue
            if d1.ports[p1] is not None:
                print("Port already taken")
                continue
            else:
                #print(p1) debugging
                break
        break
    while True:
        device2 = getInput("What device do you want to connect to: ")
        if device2 is None:
            return
        if device2 not in devices:
            print("Device doesn't exist. Please add the device in first")
            continue
        if device2 == device1:
            print("Cannot connect device to itself")
            continue
        d2 = devices[device2]
        while True:
            p2 = getInput("What port do you want to use: ")
            if p2 is None:
                return
            p2 = p2.lower()
            if p2 not in d2.ports:
                print("This port does not exist on this device")
                #print(p2) debugging
                continue
            if d2.ports[p2] is not None:
                print("Port already taken")
                continue
            else:
                break
        break
    
    d1.ports[p1] = (d2.name, p2)
    d2.ports[p2] = (d1.name, p1)
    
    print(f"\nConnected {d1.name}:{p1} to {d2.name}:{p2}")
    
def showConnections(devices):
    connections = getConnections(devices)
    
    if not devices:
        print("No devices on the network")
        return
    if not connections:
        print("No connections on the network")
        return
    
    for connection in connections:
        (dev1, port1),(dev2, port2) = connection
        print(f"{dev1}:{port1} is connected to {dev2}:{port2}")
    
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
    
    while True:
        device1 = getInput("What device do you want to ping from: ")
        if device1 is None:
            return
        if device1 not in devices:
            print("Device doesn't exist. Please add the device in first")
            continue
        d1 = devices[device1]
        if d1.state != "on":
            print(f"{d1.name} is powered off")
            continue
        if not d1.ip or not d1.subnet:
            print(f"{d1.name} is missing an IP address or subnet mask")
            continue
        else:
            break
    
    while True:
        device2 = getInput("What device do you want to ping: ")
        if device2 is None:
            return
        if device2 not in devices:
            print("Device doesn't exist. Please add the device in first")
            continue
        d2 = devices[device2]
        if d2.state != "on":
            print(f"{d2.name} is powered off")
            continue
        if not d2.ip or not d2.subnet:
            print(f"{d2.name} is missing an IP address or subnet mask")
            continue
        else:
            break
    
    checked = set()
    queue = [device1]
    reachable = False

    while queue:
        current = queue.pop(0)

        if current == device2:
            reachable = True
            break
        
        checked.add(current)
        currentDevice = devices[current]

        for port, connection in currentDevice.ports.items():
            if connection is not None:
                neighbor, _ = connection

                if neighbor not in checked:
                    queue.append(neighbor)
    if not reachable:
        print(f"\nPing failed. {device1} cannot reach {device2} physically")
        return
    
    net1 = IpCalc.calculateNetwork(d1.ip, d1.subnet)["Network"]
    net2 = IpCalc.calculateNetwork(d2.ip, d2.subnet)["Network"]
    
    if net1 != net2:
        if d1.gateway is None:
            print(f"Ping failed: {device1} and {device2} are on different subnets")
            return
        else:
            print(f"Routing through gateway {d1.gateway}...")
            return
        
    i = 0
    print(f"\nPinging {d2.ip} with 32 bytes of data:")
    while i < 4:
        time.sleep(1)
        print(f"Reply from {d2.ip}: bytes=32 time=1ms")
        i += 1
    print(f"Ping successful! {device1} can reach {device2}")
    return

def disconnect(devices):
    connections = getConnections(devices)
    
    if not devices:
        print("No devices on the network")
        return
    if not connections:
        print("No connections on the network")
    
    while True:
        devName = getInput("What device would you like to disconnect: ")
        if devName is None:
            return
        if devName not in devices:
            print("Device name not found")
            continue
        device = devices[devName]
        
        ports = {p: c for p, c in device.ports.items() if c is not None}
        
        if not ports:
            print("This device does not have any active connections")
            return
        break
    while True:
        portName = getInput("What port do you want to disconnect: ")
        if portName is None:
            return
        portName = portName.lower()
        
        if portName not in device.ports:
            print("Port doesn't exist on this device")
            continue
        if device.ports[portName] is None:
            print("Port has no active connections")
            continue
        break
    
    neighbourName, neighbourPort = device.ports[portName]
    device.ports[portName] = None
    devices[neighbourName].ports[neighbourPort] = None
    
    print(f"Disconnected {devName}:{portName} from {neighbourName}:{neighbourPort}")
            
    
def getConnections(devices):
    connections = set()
    
    if not devices:
        return connections
    for device in devices.values():
        for port, connection in device.ports.items():
            if connection is not None:
                connDevice, connPort = connection
                
                connectionID = tuple(sorted([
                    (device.name, port),
                    (connDevice, connPort)
                ]))
                
                connections.add(connectionID)
                
    return connections

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
    saveConnections(devices)
    print("Network saved to database")
    return

def showTable():
    if dbConfig["database"] == None:
        print("No database selected")
        return
    rows = getDevices()
    if not rows:
        print("No device data found")
        return
    print(tabulate(rows, headers = "keys", tablefmt="grid"))
    rows = getConnectionsInSQL()
    if not rows:
        print("No connection data found")
        return
    print(tabulate(rows, headers = "keys", tablefmt="grid"))
    
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
    
def getInput(prompt):
    value = input(prompt)
    if not value.strip():
        return None
    return value.strip()