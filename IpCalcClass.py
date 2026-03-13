class IpCalc:
    def __init__(self, ipAddress):
        self.ipAddress = ipAddress
        if not self.ipChecker():
            raise ValueError("Invalid IP Address")
#ensure if ip address is wrong, class wont be created
    
    def ipChecker(self): #check if ip address is correct format
        ipAddress = self.ipAddress.split(".")

        if len(ipAddress) != 4:
            return False
        else:
            for ipAdd in ipAddress:
                if not ipAdd.isdigit():
                    return False
                
                if len(ipAdd) > 1 and ipAdd.startswith("0"): #ensure ip address doesnt havce following 0s
                    return False
                
                num = int(ipAdd)
                if num < 0 or num > 255:
                    return False

        return True

    def ipToBinary(self):
        ipL = self.ipAddress.split(".")
        OctF = ""
        i = 0

        for ip in ipL:
            ip = int(ip)
            octe = 256
            OctS = ""
            while octe > 1:
                octe //= 2
                if ip-octe >= 0:
                    n = "1"
                    ip = ip - octe
                    OctS = OctS + n
                else:
                    n = "0"
                    OctS = OctS + n
            
            OctD = int(OctS, 2) #converts binary to number
            i+=1
            if i<4:
                OctF = OctF + OctS + "."
            else:
                OctF = OctF + OctS
        return OctF

    def subnetChecker(self):
        binary = self.ipToBinary()
        bits = binary.replace(".", "")
        
        if "01" not in bits:
            return True
        else:
            return False
        
    @staticmethod
    def subnetToPrefix(subnet):
        if subnet is None:
            return ""
        try:
            return f"/{sum(bin(int(octet)).count('1') for octet in subnet.split('.'))}"
        except Exception:
            return ""
        
    def ipToInt(self):
        octets = list(map(int, self.ipAddress.split(".")))
        return (
            (octets[0] << 24) |
            (octets[1] << 16) |
            (octets[2] << 8)  |
            octets[3]
        )
    
    @staticmethod
    def intToIp(value):
        return ".".join([
            str((value >> 24) & 255),
            str((value >> 16) & 255),
            str((value >> 8) & 255),
            str(value & 255)
        ])
    @staticmethod
    def calculateNetwork(ip, subnet):
        ipInt = IpCalc(ip).ipToInt()
        subnetInt = IpCalc(subnet).ipToInt()
        
        networkInt = ipInt & subnetInt
        broadcastInt = networkInt | (~subnetInt & 0xFFFFFFFF)
        
        return {
            "Network": IpCalc.intToIp(networkInt),
            "Broadcast": IpCalc.intToIp(broadcastInt),
            "First Host": IpCalc.intToIp(networkInt + 1),
            "Last Host": IpCalc.intToIp(broadcastInt - 1),
            "Network Int": networkInt,
            "Broadcast Int": broadcastInt,
            "IP Int": ipInt
        }
    @staticmethod
    def wildcardMask(subnet):
        try:
            octets = subnet.split(".")
            wildcard = [str(255-int(o))for o in octets]
            return ".".join(wildcard)
        except:
            return None
    def ipClass(self):
        first = int(self.ipAddress.split(".")[0])
        
        if first == 127:
            return "Loopback (127.x.x.x)"
        elif 1<= first <= 126:
            return "A"
        elif 128 <= first <= 191:
            return "B"
        elif 192 <= first <= 223:
            return "C"
        elif 224 <= first <= 239:
            return "D (Multicast)"
        elif 240 <= first <= 255:
            return "E (Experimental)"
        else:
            return "Unknown"
        
    def ipType(self):
        o1, o2, _, _= map(int, self.ipAddress.split("."))
        
        if o1 == 10:
            return "Private"
        elif o1 == 172 and 16 <= o2 <= 31:
            return "Private"
        elif o1 == 192 and o2 == 168:
            return "Private"
        else:
            return "Public"
        
    @staticmethod
    def defaultGateway(ip, subnet):
        net = IpCalc.calculateNetwork(ip, subnet)
        return net["First Host"]
    
class prefixes: #seperate class for prefixes due to ipAddress check at the start of other class
    def __init__(self, prefix):
        self.prefix = prefix
    def preToSub(self):
        prefix = self.prefix
        #prefix = prefix[1:] #remove / from prefix
        #if not prefix.isdigit():
            #return False
        prefix = int(prefix)
        if prefix < 0  or prefix > 32:
            return False
        else:
            prefix = int(prefix)
            bits = "1" * prefix + "0" * (32 - prefix) #converts prefix to binary
            octets = [str(int(bits[i:i+8], 2)) for i in range(0, 32, 8)] #converts binary into octets after every 8 numbers
            return ".".join(octets)

if __name__ == "__main__": #test code
    ip1 = IpCalc("255.233.244.242")
    print(ip1.ipChecker())
    print(ip1.ipToBinary())
    print(ip1.subnetChecker())
    t1 = prefixes("/12")
    print(t1.preToSub())
