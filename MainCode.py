from menuOptions import *

devices = {}

def Menu():
    print("""
Ip Menu
1. Add Device
2. Add IP address
3. Show Devices
4. Remove Devices
5. Power on/off Devices
6. Connect Devices
7. Show connections
8. Ping Devices
9. Disconnect Devices
10. Display Network
11. Connect to SQL
12. Create Database and Table
13. Upload Data to Database
14. Show Table
15. Load Network from Database
X. Exit Program
""")

while True:
    Menu()
    choice = input("What would you like to do? (1-X): ")
    if choice == "1":
        deviceType(devices)
    elif choice == "2":
        assignIP(devices)
    elif choice == "3":
        displayDevices(devices)
    elif choice == "4":
        deleteDevices(devices)
    elif choice == "5":
        power(devices)
    elif choice == "6":
        connect(devices)
    elif choice == "7":
        showConnections(devices)
    elif choice == "8":
        ping(devices)
    elif choice == "9":
        disconnect(devices)
    elif choice == "10":
        showVisual(devices)
    elif choice == "11":
        connectToSQL()
    elif choice == "12":
        createDatabaseTable(devices)
    elif choice == "13":
        saveNetwork(devices)
    elif choice == "14":
        showTable()
    elif choice == "15":
        loadInto(devices)
    elif choice.lower() == "x":
        print("\n Exiting program...")
        break 
    else:
        print("Invalid Choice")
    

#add items to sql database
#DNS server
#IpCalcClass factory pattern
#255.255.255.255 not valid subnet
#Make all features in seperate files
#Power on + off feature
#Connections on ports
#ACLs
#lookup feature
#error with dashes //