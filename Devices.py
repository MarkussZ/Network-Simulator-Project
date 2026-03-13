class Device:
    def __init__(self, name, deviceType, ports, state = "off", model=None):
        self.name = name
        self.deviceType = deviceType
        self.ports = {port: None for port in ports}
        self.ip = None
        self.subnet = None
        self.state = state
        self.gateway = None
        self.wildcard = None
        self.ipType = None
        self.ipClass = None
        self.model = model
        self.ipv6 = None
        
        
    def showPorts(self):
        lines = []
        for port, connection in self.ports.items():
            if connection is None:
                status = "free"
            else:
                status = "used"
            lines.append(f"{port}: ({status})")
        return ", ".join(lines)
    #takes items and returns them as pairs, then joins them as one string
    @staticmethod
    def generatePorts(prefix, count):
        return [f"{prefix}{i}" for i in range (1, count + 1)]
    
    def getPortStatistics(self):
        totalPorts = len(self.ports)
        usedPorts = sum(1 for connection in self.ports.values() if connection is not None)
        unusedPorts = totalPorts - usedPorts
        return totalPorts, usedPorts, unusedPorts
    
class PC(Device):
    def __init__(self, name):
        super().__init__(
            name,
            "PC",
            Device.generatePorts("f0/", 1)
        )

class Server(Device):
    def __init__(self, name):
        super().__init__(
            name,
            "Server",
            Device.generatePorts("g0/", 2)
        )

class Router(Device):
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
        

class L3Switch(Device):
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
        
class Firewall(Device):
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