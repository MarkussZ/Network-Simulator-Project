import mysql.connector
from Devices import *

dbConfig = {
    "host": None,
    "user": None,
    "password": None,
    "database": None,
    "port": None
}

def connectToDatabase():
    try:
        dbConfig["host"] = getInput("Enter the host (Default: localhost)") or "localhost"
        dbConfig["user"] = getInput("Enter the user (Default: root)") or "root"
        dbConfig["password"] = getInput("Enter the password (Can be blank)") or ""
        dbConfig["port"] = int(getInput("Enter the port number (Default: 3306)") or 3306)
        
        print(dbConfig)
        
        try:
            conn = mysql.connector.connect(
                host=dbConfig["host"],
                user=dbConfig["user"],
                password=dbConfig["password"],
                port=dbConfig["port"]
            )
            conn.close()
        except mysql.connector.Error as e:
            print(f"Error occured while connecting: {e}")
            return False
    except KeyboardInterrupt:
        print("\nConnection attempt cancelled by user")
        return False
    print("Successfully connected to the database")
    return True
        
def createDatabase():    
    dbName = getInput("Please enter a database name: ")
    if dbName is None:
        return
    dbConfig["database"] = dbName

    conn = mysql.connector.connect(
            host=dbConfig["host"],
            user=dbConfig["user"],
            password=dbConfig["password"],
            port=dbConfig["port"]
    )
    cursor = conn.cursor()
    
    cursor.execute(f"SHOW DATABASES LIKE '{dbConfig['database']}'")
    dbExists = cursor.fetchone() is not None
    
    if not dbExists:
        cursor.execute(f"CREATE DATABASE {dbConfig['database']}")
    cursor.close()
    conn.close()
    
    return not dbExists

def connect():
    if any(v is None for v in dbConfig.values()):
        raise ValueError("Database info not set. Run connectToDatabase() first.")
    return mysql.connector.connect(
        host=dbConfig["host"],
        user=dbConfig["user"],
        password=dbConfig["password"],
        database=dbConfig["database"],
        port=dbConfig["port"]
    )

def prepareDatabase():
    if dbConfig["database"] is None:
        return

    conn = connect()  
    cursor = conn.cursor()

    # Check/create devices table
    cursor.execute("SHOW TABLES LIKE 'devices'")
    tableExists = cursor.fetchone() is not None
    if not tableExists:
        cursor.execute("""
            CREATE TABLE devices (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                deviceType VARCHAR(50) NOT NULL,
                state VARCHAR(10),
                totalPorts INT,
                usedPorts INT,
                unusedPorts INT,
                model VARCHAR(10)
            )
        """)

    # Check/create ports table
    cursor.execute("SHOW TABLES LIKE 'ports'")
    portsTableExists = cursor.fetchone() is not None
    if not portsTableExists:
        cursor.execute("""
            CREATE TABLE ports (
                id INT AUTO_INCREMENT PRIMARY KEY,
                deviceName VARCHAR(100) NOT NULL,
                portName VARCHAR(20) NOT NULL,
                ipAddress VARCHAR(15),
                subnetMask VARCHAR(15),
                gateway VARCHAR(15),
                wildcardMask VARCHAR(15),
                vlan INT,
                trunk BOOLEAN
            )
        """)

    # Check/create connections table
    cursor.execute("SHOW TABLES LIKE 'connections'")
    connTableExists = cursor.fetchone() is not None
    if not connTableExists:
        cursor.execute("""
            CREATE TABLE connections (
                id INT AUTO_INCREMENT PRIMARY KEY,
                device1 VARCHAR(100) NOT NULL,
                port1 VARCHAR(15) NOT NULL,
                device2 VARCHAR(100) NOT NULL,
                port2 VARCHAR(15) NOT NULL
            )
        """)

    # Check/create etherchannels table
    cursor.execute("SHOW TABLES LIKE 'etherchannels'")
    etherTableExists = cursor.fetchone() is not None
    if not etherTableExists:
        cursor.execute("""
            CREATE TABLE etherchannels (
                id INT AUTO_INCREMENT PRIMARY KEY,
                deviceName VARCHAR(100) NOT NULL,
                groupName VARCHAR(20) NOT NULL,
                ipAddress VARCHAR(15),
                subnetMask VARCHAR(15),
                gateway VARCHAR(15),
                status VARCHAR(10),
                members TEXT,
                connected_to VARCHAR(100)
            )
        """)
    # Check/create VLANs table
    cursor.execute("SHOW TABLES LIKE 'vlans'")
    vlanTableExists = cursor.fetchone() is not None
    if not vlanTableExists:
        cursor.execute("""
            CREATE TABLE vlans (
                id INT AUTO_INCREMENT PRIMARY KEY,
                deviceName VARCHAR(100) NOT NULL,
                vlanID INT NOT NULL,
                name VARCHAR(50),
                ipAddress VARCHAR(15),
                subnetMask VARCHAR(15)
            )
        """)
        
    cursor.execute("SHOW TABLES LIKE 'hsrp'")
    hsrpTableExists = cursor.fetchone() is not None
    if not hsrpTableExists:
        cursor.execute("""
            CREATE TABLE hsrp (
                id INT AUTO_INCREMENT PRIMARY KEY,
                deviceName VARCHAR(100) NOT NULL,
                vlanID INT NOT NULL,
                virtualIP VARCHAR(15),
                priority INT,
                state VARCHAR(10)
            )
        """)

    conn.commit()
    cursor.close()
    conn.close()

    # Return True if devices table was created, False if it existed
    return not tableExists

def saveDevices(devices):
    conn = connect()
    cursor = conn.cursor()
    
    cursor.execute("TRUNCATE TABLE devices")
    
    for device in devices.values():
        total, used, unused = device.getPortStatistics()
        
        cursor.execute("""
            INSERT INTO devices (
                name, deviceType, state, totalPorts, usedPorts, unusedPorts, model
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            device.name,
            device.deviceType,
            device.state,
            total,
            used,
            unused,
            device.model
        ))
        
    conn.commit()
    cursor.close()
    conn.close()
    
def savePorts(devices):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("TRUNCATE TABLE ports")

    for device in devices.values():
        for portName, data in device.ports.items():
            cursor.execute("""
                INSERT INTO ports (
                    deviceName, portName, ipAddress, subnetMask, gateway, wildcardMask, vlan, trunk
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                device.name,
                portName,
                data["ip"],
                data["subnet"],
                data["gateway"],
                data["wildcard"],
                data.get("vlan"),
                data.get("trunk", False)
            ))

    conn.commit()
    cursor.close()
    conn.close()
    
def saveConnections(devices):
    conn = connect()
    cursor = conn.cursor()
    
    cursor.execute("TRUNCATE TABLE connections")
    
    connections = set()
    
    for device in devices.values():
        for portName, portData in device.ports.items():
            connection = portData["connection"]
            
            if connection is not None:
                # Handle both 2-tuple and 3-tuple connections
                if len(connection) == 3:
                    connDevice, connPort, group = connection
                else:
                    connDevice, connPort = connection
                
                connectionID = tuple(sorted([
                    (device.name, portName),
                    (connDevice, connPort)
                ]))
                
                if connectionID in connections:
                    continue
                
                connections.add(connectionID)
                
                cursor.execute("""
                    INSERT INTO connections (
                        device1, port1, device2, port2
                    )
                    VALUES (%s, %s, %s, %s)
                """, (
                    device.name,
                    portName,
                    connDevice,
                    connPort
                ))
    
    conn.commit()
    cursor.close()
    conn.close()
    
def saveEtherChannels(devices):
    conn = connect()
    cursor = conn.cursor()
    
    cursor.execute("TRUNCATE TABLE etherchannels")
    
    for device in devices.values():
        for groupName, data in device.etherchannels.items():
            members = ",".join(data.get("members", []))
            cursor.execute("""
                INSERT INTO etherchannels (
                    deviceName, groupName, ipAddress, subnetMask, gateway, status, members, connected_to
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                device.name,
                groupName,
                data.get("ip"),
                data.get("subnet"),
                data.get("gateway"),
                data.get("status"),
                members,
                data.get("connected_to")
            ))
    
    conn.commit()
    cursor.close()
    conn.close()
    
def saveVLANs(devices):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("TRUNCATE TABLE vlans")

    for device in devices.values():
        if not hasattr(device, "vlans"):
            continue

        for vlanID, data in device.vlans.items():
            cursor.execute("""
                INSERT INTO vlans (
                    deviceName, vlanID, name, ipAddress, subnetMask
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
                device.name,
                vlanID,
                data.get("name"),
                data.get("ip"),
                data.get("subnet")
            ))

    conn.commit()
    cursor.close()
    conn.close()

def saveHSRP(devices):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("TRUNCATE TABLE hsrp")

    for device in devices.values():
        if not isinstance(device, L3Switch):
            continue

        for vlanID, group in device.hsrp_groups.items():
            cursor.execute("""
                INSERT INTO hsrp (
                    deviceName, vlanID, virtualIP, priority, state
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
                device.name,
                vlanID,
                group.get("virtual_ip"),
                group.get("priority"),
                group.get("state")
            ))

    conn.commit()
    cursor.close()
    conn.close()
    
def getDevices():
    conn = connect()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM devices")
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    
    for row in results:
        for k, v in row.items():
            if v is None:
                row[k] = "Null"
    return results

def getConnectionsInSQL():
    conn = connect()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM connections")
    connResults = cursor.fetchall()
    cursor.close()
    conn.close()
    
    for row in connResults:
        for k, v in row.items():
            if v is None:
                row[k] = "Null"
    return connResults

def getPorts():
    conn = connect()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM ports")
    portResults = cursor.fetchall()
    cursor.close()
    conn.close()
    
    for row in portResults:
        for k, v in row.items():
            if v is None:
                row[k] = "Null"
    return portResults

def getEtherchannels():
    conn = connect()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM etherchannels")
    etherResults = cursor.fetchall()
    cursor.close()
    conn.close()
    
    for row in etherResults:
        for k, v in row.items():
            if v is None:
                row[k] = "Null"
    return etherResults

def getVlans():
    conn = connect()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM vlans")
    vlanResults = cursor.fetchall()
    cursor.close()
    conn.close()
    
    for row in vlanResults:
        for k, v in row.items():
            if v is None:
                row[k] = "Null"
    return vlanResults

def getHSRP():
    conn = connect()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM hsrp")
    hsrpResults = cursor.fetchall()
    cursor.close()
    conn.close()
    
    for row in hsrpResults:
        for k, v in row.items():
            if v is None:
                row[k] = "Null"
    return hsrpResults

def loadNetwork():
    devices = {}
    conn = connect()
    cursor = conn.cursor(dictionary=True)

    # ---------------------------
    # 1. LOAD DEVICES
    # ---------------------------
    cursor.execute("SELECT * FROM devices")
    deviceRows = cursor.fetchall()

    for row in deviceRows:
        name = row["name"]
        deviceType = row["deviceType"]
        model = row.get("model")

        if deviceType == "Router":
            device = Router(name, model=model)
        elif deviceType == "L2Switch":
            device = L2Switch(name, model=model)
        elif deviceType == "L3Switch":
            device = L3Switch(name, model=model)
        elif deviceType == "Server":
            device = Server(name)
        elif deviceType == "PC":
            device = PC(name)
        elif deviceType == "Firewall":
            device = Firewall(name)
        else:
            continue

        device.state = row["state"]

        # IMPORTANT: wipe default VLANs so SQL becomes source of truth
        if hasattr(device, "vlans"):
            device.vlans = {}

        devices[name] = device

    # ---------------------------
    # 2. LOAD VLANs
    # ---------------------------
    cursor.execute("SELECT * FROM vlans")
    vlanRows = cursor.fetchall()

    for row in vlanRows:
        device = devices.get(row["deviceName"])
        if not device or not hasattr(device, "vlans"):
            continue

        vlanID = row["vlanID"]

        device.vlans[vlanID] = {
            "name": row.get("name"),
            "ip": row.get("ipAddress"),
            "subnet": row.get("subnetMask"),
            "ports": []
        }

    # ---------------------------
    # 3. LOAD PORTS
    # ---------------------------
    cursor.execute("SELECT * FROM ports")
    portRows = cursor.fetchall()

    for row in portRows:
        device = devices.get(row["deviceName"])
        if not device:
            continue

        portName = row["portName"]

        if portName in device.ports:
            portData = device.ports[portName]

            portData["ip"] = row.get("ipAddress")
            portData["subnet"] = row.get("subnetMask")
            portData["gateway"] = row.get("gateway")
            portData["wildcard"] = row.get("wildcardMask")

            # VLAN + trunk handling
            portData["vlan"] = row.get("vlan") or 1
            portData["trunk"] = bool(row.get("trunk"))

    # ---------------------------
    # 4. REBUILD VLAN PORT MEMBERSHIP
    # ---------------------------
    for device in devices.values():
        if not hasattr(device, "vlans"):
            continue

        for portName, data in device.ports.items():
            vlanID = data.get("vlan")

            # Only assign access ports to VLANs (NOT trunks)
            if not data.get("trunk") and vlanID in device.vlans:
                device.vlans[vlanID]["ports"].append(portName)

        # Safety: ensure VLAN 1 exists if nothing loaded
        if not device.vlans:
            device.vlans[1] = {
                "name": "default",
                "ip": None,
                "subnet": None,
                "ports": list(device.ports.keys())
            }

    # ---------------------------
    # 5. LOAD CONNECTIONS
    # ---------------------------
    cursor.execute("SELECT * FROM connections")
    connectionRows = cursor.fetchall()

    for row in connectionRows:
        d1 = devices.get(row["device1"])
        d2 = devices.get(row["device2"])

        if d1 and d2:
            p1 = row["port1"]
            p2 = row["port2"]

            if (
                p1 in d1.ports and
                p2 in d2.ports and
                d1.ports[p1]["connection"] is None and
                d2.ports[p2]["connection"] is None
            ):
                d1.ports[p1]["connection"] = (d2.name, p2)
                d2.ports[p2]["connection"] = (d1.name, p1)

    # ---------------------------
    # 6. LOAD ETHERCHANNELS
    # ---------------------------
    cursor.execute("SELECT * FROM etherchannels")
    etherRows = cursor.fetchall()

    for row in etherRows:
        device = devices.get(row["deviceName"])
        if not device:
            continue

        groupName = row["groupName"]
        members = row["members"].split(",") if row["members"] else []

        device.etherchannels[groupName] = {
            "members": members,
            "ip": row["ipAddress"],
            "subnet": row["subnetMask"],
            "gateway": row["gateway"],
            "status": row["status"],
            "connected_to": row["connected_to"]
        }

        for port in members:
            if port in device.ports:
                device.ports[port]["etherchannel"] = groupName

    # ---------------------------
    # 7. LOAD HSRP
    # ---------------------------
    cursor.execute("SELECT * FROM hsrp")
    hsrpRows = cursor.fetchall()

    for row in hsrpRows:
        device = devices.get(row["deviceName"])
        if not device or not isinstance(device, L3Switch):
            continue

        vlanID = row["vlanID"]

        device.hsrp_groups[vlanID] = {
            "virtual_ip": row.get("virtualIP"),
            "priority": row.get("priority"),
            "state": row.get("state")
        }
    vlans_with_hsrp = set()

    for dev in devices.values():
        if isinstance(dev, L3Switch):
            vlans_with_hsrp.update(dev.hsrp_groups.keys())

    for vlanID in vlans_with_hsrp:
        L3Switch.determine_hsrp_for_vlan(devices, vlanID)

    cursor.close()
    conn.close()

    return devices

def getInput(prompt):
    value = input(prompt)
    if not value.strip():
        return None
    return value.strip()