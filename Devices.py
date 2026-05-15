class Device:
    canHaveIP = False
    canHaveGateway = False
    
    def __init__(self, name, deviceType, ports, state = "off", model=None, vlanID=None):
        self.name = name
        self.deviceType = deviceType
        self.ports = {
            port: {
                "connection": None,
                "ip": None,
                "subnet": None,
                "gateway": None,
                "wildcard": None,
                "etherchannel": None,
                "vlan": None
            }
            for port in ports
        }
        self.etherchannels = {}
        self.vlans = {}
        if vlanID is not None:
            self.vlans[vlanID] = {
                "ip": None,
                "subnet": None,
                "gateway": None,
                "members": []
            }
        self.ipType = None
        self.ipClass = None
        self.model = model
        self.ipv6 = None
        self.state = state
        
        
    def showPorts(self):
        return ", ".join(
            f"{p}: ({'used' if d.connection else 'free'}, IP: {d.ip or 'No IP' if self.canHaveIP else 'N/A'})"
            for p, d in self.ports.items()
        )
    #takes items and returns them as pairs, then joins them as one string
    @staticmethod
    def generatePorts(prefix, count):
        return [f"{prefix}{i}" for i in range (1, count + 1)]
    
    def getPortStatistics(self):
        totalPorts = len(self.ports)
        usedPorts = sum(
            1 for port in self.ports.values()
            if port["connection"] is not None
        )
        unusedPorts = totalPorts - usedPorts
        return totalPorts, usedPorts, unusedPorts
    
    @staticmethod
    def getNextGlobalPoNumber(devices):
        numbers = []

        for dev in devices.values():
            for po in dev.etherchannels.keys():
                if po.startswith("Po"):
                    try:
                        numbers.append(int(po[2:]))
                    except:
                        pass

        return f"Po{max(numbers, default=0) + 1}"
    
 
class EndDevice(Device):
    canHaveIP = True
    canHaveGateway = True
    canHaveVLAN = False

    def __init__(self, name, ports):
        super().__init__(name, self.__class__.__name__, ports)
        self.vlan = 1
        self.default_gateway = None

        for port_data in self.ports.values():
            port_data["vlan"] = self.vlan
    
class PC(EndDevice):
    def __init__(self, name):
        super().__init__(name, Device.generatePorts("f0/", 1))

class Server(EndDevice):
    def __init__(self, name):
        super().__init__(name, Device.generatePorts("g0/", 2))

class Router(Device):
    canHaveIP = True
    canHaveGateway = False
    canHaveVLAN = False
    models = {
        "4331": {"gigabitethernet": 4},
        "1941": {"gigabitethernet": 2},
        "2911": {"gigabitethernet": 3},
    }

    def __init__(self, name, model="4331"):
        if model not in self.models:
            raise ValueError(f"Invalid Router model '{model}'")
        ports = Device.generatePorts("g0/", self.models[model]["gigabitethernet"])
        super().__init__(name, "Router", ports, state="off", model=model)
        
class L2Switch(Device):
    canHaveIP = False
    canHaveGateway = False
    canHaveVLAN = True
    models = {
        "2960": {"fastethernet": 24, "gigabitethernet": 2},
        "2960S": {"fastethernet": 48, "gigabitethernet": 4},
    }

    def __init__(self, name, model="2960"):
        if model not in self.models:
            raise ValueError(f"Invalid L2Switch model '{model}'")
        ports = (
            Device.generatePorts("f0/", self.models[model]["fastethernet"]) +
            Device.generatePorts("g0/", self.models[model]["gigabitethernet"])
        )
        super().__init__(name, "L2Switch", ports, state="off", model=model)
        
        # Default all ports to VLAN 1
        for port in self.ports:
            self.ports[port]["vlan"] = 1

        # Initialize VLAN 1 in vlans dict
        self.vlans = {1: {"name": "default", "ports": list(self.ports.keys()), "ip": None}}


class L3Switch(Device):
    canHaveIP = True
    canHaveGateway = False
    canHaveVLAN = True
    models = {
        "3650": {"fastethernet": 24, "gigabitethernet": 4},
        "9300": {"fastethernet": 48, "gigabitethernet": 8},
    }

    def __init__(self, name, model="3650"):
        if model not in self.models:
            raise ValueError(f"Invalid L3Switch model '{model}'")
        ports = (
            Device.generatePorts("f0/", self.models[model]["fastethernet"]) +
            Device.generatePorts("g0/", self.models[model]["gigabitethernet"])
        )
        super().__init__(name, "L3Switch", ports, state="off", model=model)
        
        # Default all ports to VLAN 1
        for port in self.ports:
            self.ports[port]["vlan"] = 1

        self.vlans = {1: {"name": "default", "ports": list(self.ports.keys()), "ip": None}}

        # --- HSRP support ---
        # Structure: {vlan_id: {"virtual_ip": str, "priority": int, "state": "active"/"standby"}}
        self.hsrp_groups = {}

    def configure_hsrp(self, vlan_id, virtual_ip, priority=100):
        """
        Configures HSRP for a VLAN
        - vlan_id: VLAN number
        - virtual_ip: IP that HSRP group will use
        - priority: determines active/standby (higher = active)
        """
        if vlan_id not in self.vlans:
            raise ValueError(f"VLAN {vlan_id} does not exist on {self.name}")
        self.hsrp_groups[vlan_id] = {
            "virtual_ip": virtual_ip,
            "priority": priority,
            "state": "standby"  # default, you can calculate later
        }
    
    @staticmethod
    def determine_hsrp_for_vlan(devices, vlan_id):
        participants = []

        # Find all L3 switches participating in this VLAN
        for dev in devices.values():
            if isinstance(dev, L3Switch) and vlan_id in dev.hsrp_groups:
                participants.append(dev)

        if not participants:
            return

        # Ensure all virtual IPs match
        virtual_ips = {sw.hsrp_groups[vlan_id]["virtual_ip"] for sw in participants}
        if len(virtual_ips) > 1:
            print(f"Warning: HSRP virtual IP mismatch in VLAN {vlan_id}")
            return

        # Elect active (highest priority)
        active = max(participants, key=lambda sw: sw.hsrp_groups[vlan_id]["priority"])

        # Assign states
        for sw in participants:
            sw.hsrp_groups[vlan_id]["state"] = "active" if sw == active else "standby"
        
class Firewall(Device):
    canHaveIP = True
    canHaveGateway = False
    canHaveVLAN = False
    def __init__(self, name):
        super().__init__(
            name,
            "Firewall",
            Device.generatePorts("g0/", 4)
        )
class Factory: #make classes at runtime
    checkType = {"router","l2switch","l3switch","server","pc", "firewall"}
    
    @staticmethod
    def normalizeType(deviceType):
        deviceType = deviceType.lower()
        matches = [d for d in Factory.checkType if d.startswith(deviceType)]
        if len(matches) == 1:
            return matches[0]
        else:
            return None

    @staticmethod
    def getAvailableModels(deviceType):
        deviceType = Factory.normalizeType(deviceType)
        if deviceType == "router":
            return list(Router.models.keys())
        elif deviceType == "l2switch":
            return list(L2Switch.models.keys())
        elif deviceType == "l3switch":
            return list(L3Switch.models.keys())
        else:
            return None
    
    @staticmethod
    def buildDevice(deviceType, name, model=None):
        deviceType = Factory.normalizeType(deviceType)
        if deviceType == "router":
            return Router(name, model=model if model else "4331")
        if deviceType == "l2switch":
            return L2Switch(name, model=model if model else "2960")
        if deviceType == "l3switch":
            return L3Switch(name, model=model if model else "3650")
        if deviceType == "server":
            return Server(name)
        if deviceType == "pc":
            return PC(name)
        if deviceType == "firewall":
            return Firewall(name)
        else:
            print("Invalid option")
            return None
    
    def validType(deviceType): 
        return Factory.normalizeType(deviceType) is not None
    #used to check is device type is correct before continuing in main code
            
if __name__ == '__main__': #test code
    while True:
        choice = input("What device would you like to create (or 'quit'): ")
        if choice.lower() == "quit":
            break

        name = input("What is the device name: ")

        device = Factory.buildDevice(choice, name)

        if device:
            print(device.name)
            print(device.deviceType)
            print(device.showPorts)
        else:
            print("Invalid option.")
            