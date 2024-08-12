from thread_mesh_read import get_mesh_data 
import serial, time
import json

SERIAL_PORT = '/dev/ttyACM1'
BAUD_RATE = 115200

class Child:
    def __init__(self, rloc16: int, lq: int, mode: str):
        self.rloc16 = rloc16
        self.lq = lq
        self.mode = mode

    def __eq__(self, other):
        rloc16 = self.rloc16 == other.rloc16
        lq = self.lq == other.lq
        mode = self.mode == other.mode

        return rloc16 and lq and mode

    def to_dict(self):
        return {
                'rloc16': self.rloc16,
                'lq': self.lq,
                'mode': self.mode
            }

class Router:
    def __init__(self, rloc16: int, ext_addr: str, identifier: int, ver: int, ip_list: [str], child_list: [Child]):
            self.rloc16 = rloc16,
            self.ext_addr = ext_addr
            self.identifier = identifier
            self.ver = ver
            self.ip_list = ip_list
            self.child_list = child_list
    def __eq__(self, other):
        rloc16 = self.rloc16 == other.rloc16
        ext_addr = self.ext_addr == other.ext_addr
        identifier = self.identifier == other.identifier
        ver = self.ver == other.ver
        ip_list = self.ip_list == other.ip_list
        child_list = self.child_list == other.child_list
        
        return rloc16 and ext_addr and identifier and ver and ip_list and child_list

    def to_dict(self):
        return {
                'rloc16': self.rloc16,
                'ext_addr': self.ext_addr,
                'identifier': self.identifier,
                'ver': self.ver,
                'ip_list': self.ip_list,
                'child_list': [child.to_dict() for child in self.child_list]
                }

def process_router_data(mesh_data_raw):
    # Process the data_string
    data_list = mesh_data_raw[0].split()

    # Extracting the relevant fields from the data_string
    identifier = int(data_list[0].split(":")[1])
    rloc16 = int(data_list[1].split(":")[1], 16)  # converting hex string to integer
    ext_addr = data_list[2].split(":")[1]
    ver = int(data_list[3].split(":")[1])

    ip_list = mesh_data_raw[2:6]

    child_list = []
   
    if "none" in mesh_data_raw[6].split(":")[1]:
        print("There are no children!!")
    else:
        iterator = 7

        while iterator < len(mesh_data_raw) and "id" not in mesh_data_raw[iterator]:
            child_data_list = mesh_data_raw[iterator].split()
            child_rloc16 = int(child_data_list[0].split(":")[1], 16)
            child_lq = int(child_data_list[1].split(":")[1][0])
            child_mode = child_data_list[2].split(":")[1]
            new_child = Child(child_rloc16, child_lq, child_mode)

            child_list.append(new_child)
            iterator += 1
    
    return (rloc16, Router(rloc16, ext_addr, identifier, ver, ip_list, child_list))

if __name__ == "__main__":
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE)

    mesh_data = {}
    
    while True:
        mesh_data_raw = get_mesh_data(ser)
        rloc16, router = process_router_data(mesh_data_raw)
        
        if rloc16 not in mesh_data or mesh_data[rloc16] != router:
            print("Updated info")
            mesh_data[rloc16] = router
            json_object = json.dumps(mesh_data[rloc16].to_dict(), indent = 2)
            
            # send the json object over socket to jacquard

        # check for new data every 5 seconds
        time.sleep(5)
