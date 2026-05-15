from menuOptions import *

def deviceMenu(devices):
    while True:
        print("""
Device Management
1. Add Device
2. Remove Device
3. Power On/Off
4. Show Devices
B. Back
""")

        choice = input("Select option: ").lower()

        if choice == "1":
            deviceType(devices)
        elif choice == "2":
            deleteDevices(devices)
        elif choice == "3":
            power(devices)
        elif choice == "4":
            displayDevices(devices)
        elif choice == "b":
            return
        else:
            print("Invalid choice")
            
def connectionMenu(devices):
    while True:
        print("""
Connections
1. Connect Devices
2. Disconnect Devices
3. Show Connections
B. Back
""")

        choice = input("Select option: ").lower()

        if choice == "1":
            connect(devices)
        elif choice == "2":
            disconnect(devices)
        elif choice == "3":
            showConnections(devices)
        elif choice == "b":
            return
        else:
            print("Invalid choice")

def ipMenu(devices):
    while True:
        print("""
IP Configuration
1. Assign IP
2. Remove IP
B. Back
""")

        choice = input("Select option: ").lower()

        if choice == "1":
            assignIP(devices)
        elif choice == "2":
            removeIP(devices)
        elif choice == "b":
            return
        else:
            print("Invalid choice")
            
def switchingMenu(devices):
    while True:
        print("""
Switching
1. Configure VLANs
2. Create EtherChannel
3. Remove EtherChannel
4. Setup HSRP
5. Setup ACL
B. Back
""")

        choice = input("Select option: ").lower()

        if choice == "1":
            configureVLAN(devices)
        elif choice == "2":
            etherChannel(devices)
        elif choice == "3":
            removeEtherChannel(devices)
        elif choice == "4":
            menu_hsrp(devices)
        elif choice == "5":
            pass  # your ACL function
        elif choice == "b":
            return
        else:
            print("Invalid choice")
            
def networkMenu(devices):
    while True:
        print("""
Network Tools
1. Ping Devices
B. Back
""")

        choice = input("Select option: ").lower()

        if choice == "1":
            ping(devices)
        elif choice == "b":
            return
        else:
            print("Invalid choice")
            
def databaseMenu(devices):
    while True:
        print("""
Database
1. Connect to SQL
2. Create Database/Table
3. Upload Data
4. Show Table
5. Load Network
B. Back
""")

        choice = input("Select option: ").lower()

        if choice == "1":
            connectToSQL()
        elif choice == "2":
            createDatabaseTable(devices)
        elif choice == "3":
            saveNetwork(devices)
        elif choice == "4":
            showTable()
        elif choice == "5":
            loadInto(devices)
        elif choice == "b":
            return
        else:
            print("Invalid choice")
            
