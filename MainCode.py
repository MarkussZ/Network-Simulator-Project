from Menus import *
from menuOptions import *

devices = {}

def Menu():
    print("""
Main Menu
1. Device Management
2. Connections
3. IP Configuration
4. Switching
5. Network Tools
6. Database
7. Visualizer
X. Exit
""")

while True:
    try:
        Menu()
        choice = input("What would you like to do? (1-X): ")
        if choice == "1":
            deviceMenu(devices)
        elif choice == "2":
            connectionMenu(devices)
        elif choice == "3":
            ipMenu(devices)
        elif choice == "4":
            switchingMenu(devices)
        elif choice == "5":
            networkMenu(devices)
        elif choice == "6":
            databaseMenu(devices)
        elif choice == "7":
            showVisual(devices)
        elif choice.lower() == "x":
            print("\n Exiting program...")
            break 
        else:
            print("Invalid Choice")
    
    except KeyboardInterrupt:
        print("\nOperation cancelled. Returning to menu.")
    except Exception as e:
        print("Unexpected error:", e)
    

#DNS server
#255.255.255.255 not valid subnet
#Make all features in seperate files
#ACLs
#NAT translation
#check for errors
#DHCP
#VLANs
#IPv6
#warning for etherchannel removing IP
#disconnecting device and running visualizer causes error