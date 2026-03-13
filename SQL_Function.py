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
    
    cursor.execute("SHOW TABLES LIKE 'devices'")
    tableExists = cursor.fetchone() is not None
    
    if not tableExists:
        cursor.execute("""
            CREATE TABLE devices (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                deviceType VARCHAR(50) NOT NULL,
                IPaddress VARCHAR(15),
                SubnetMask VARCHAR(15),
                Gateway VARCHAR(15),
                WildcardMask VARCHAR(15),
                IPType VARCHAR(10),
                IPClass VARCHAR(10),
                IPv6address VARCHAR(50),
                state VARCHAR(10),
                totalPorts INT,
                usedPorts INT,
                unusedPorts INT,
                model VARCHAR(10)
            )
        """)
    
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
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return not tableExists

def saveDevices(devices):
    conn = connect()
    cursor = conn.cursor()
    
    cursor.execute("TRUNCATE TABLE devices")
    
    for device in devices.values():
        total, used, unused = device.getPortStatistics()
        
        cursor.execute("""
            INSERT INTO devices (
                name, deviceType, IPaddress, SubnetMask, Gateway, WildcardMask, IPType, IPClass, IPv6address, state, totalPorts, usedPorts, unusedPorts, model
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            device.name,
            device.deviceType,
            device.ip,
            device.subnet,
            device.gateway,
            device.wildcard,
            device.ipType,
            device.ipClass,
            device.ipv6,
            device.state,
            total,
            used,
            unused,
            device.model
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
        for port, connection in device.ports.items():
            if connection is not None:
                connDevice, connPort = connection
                
                connectionID = tuple(sorted([
                    (device.name, port),
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
                    port,
                    connDevice,
                    connPort
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

def loadNetwork():
    devices = {}
    conn = connect()
    cursor = conn.cursor(dictionary = True)
    
    cursor.execute("SELECT * FROM devices")
    deviceRows = cursor.fetchall()
    
    for row in deviceRows:
        name = row["name"]
        deviceType = row["deviceType"]
        
        if deviceType == "Router":
            device = Router(name)
        elif deviceType == "L2Switch":
            device = L2Switch(name)
        elif deviceType == "L3Switch":
            device = L3Switch(name)
        elif deviceType == "Server":
            device = Server(name)
        elif deviceType == "PC":
            device = PC(name)
        elif deviceType == "Firewall":
            device = PC(name)
        else:
            continue
        
        device.ip = row["IPaddress"]
        device.subnet = row["SubnetMask"]
        device.gateway = row["Gateway"]
        device.wildcard = row["WildcardMask"]
        device.ipType = row["IPType"]
        device.ipClass = row["IPClass"]
        device.ipv6 = row["IPv6address"]
        device.state = row["state"]
        
        devices[name] = device
        
    cursor.execute("SELECT * FROM connections")
    connectionRows = cursor.fetchall()
    
    for row in connectionRows:
        d1 = devices.get(row["device1"])
        d2 = devices.get(row["device2"])
        
        if d1 and d2:
            p1 = row["port1"]
            p2 = row["port2"]
            
            if d1.ports[p1] is None and d2.ports[p2] is None:
                d1.ports[p1] = (d2.name, p2)
                d2.ports[p2] = (d1.name, p1)
    
    cursor.close()
    conn.close()
    
    return devices

def getInput(prompt):
    value = input(prompt)
    if not value.strip():
        return None
    return value.strip()