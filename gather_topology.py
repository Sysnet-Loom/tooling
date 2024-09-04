import sys, os, re
import yaml
from thread_mesh_read import get_mesh_data 
import serial, time, json, socket

SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 115200

class Child:
    def __init__(self, rloc16: str, lq: int, mode: str):
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
    def __init__(self, loom_id: str, x_offset: int, y_offset: int, one_link: [str], two_link: [str], \
            three_link: [str], rloc16: str, ext_addr: str, identifier: str, ver: int, ip_list: [str], \
            child_list: [Child]):
            
        self.loom_id = loom_id
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.one_link = one_link
        self.two_link = two_link
        self.three_link = three_link
        self.rloc16 = rloc16
        self.ext_addr = ext_addr
        self.identifier = identifier
        self.ver = ver
        self.ip_list = ip_list
        self.child_list = child_list

    def __eq__(self, other):
        loom_id = self.loom_id == other.loom_id
        one_link = self.one_link == other.one_link
        two_link = self.two_link == other.two_link
        three_link = self.three_link == other.three_link
        x_offset = self.x_offset == other.x_offset
        y_offset = self.y_offset == other.y_offset
        rloc16 = self.rloc16 == other.rloc16
        ext_addr = self.ext_addr == other.ext_addr
        identifier = self.identifier == other.identifier
        ver = self.ver == other.ver
        ip_list = self.ip_list == other.ip_list
        child_list = self.child_list == other.child_list
        
        return one_link and two_link and three_link and rloc16 and ext_addr and identifier and \
                ver and ip_list and child_list and loom_id and x_offset and y_offset

    def to_dict(self):
        return {
                self.ext_addr: {
                'network_id_no': self.loom_id,    
                'x_offset': self.x_offset,
                'y_offset': self.y_offset,
                'one_link': self.one_link,
                'two_link': self.two_link,
                'three_link': self.three_link,
                'ext_addr': self.ext_addr,
                'rloc16': self.rloc16,
                'identifier': self.identifier,
                'ver': self.ver,
                'ip_list': self.ip_list,
                'child_list': [child.to_dict() for child in self.child_list]
                }}

def process_router_data(mesh_data_raw, loom_id, x_offset, y_offset):
    
    # The mesh data is of the following form:
    #
    #   id:02 rloc16:0x0800 ext-addr:b29184ab74e677a5 ver:4 - me - leader
    #   3-links:{ 25 }
    #   ip6-addrs:
    #       fdf5:991e:df88:2ada:0:ff:fe00:fc00
    #       fdf5:991e:df88:2ada:0:ff:fe00:800
    #       fdf5:991e:df88:2ada:1342:611f:5647:9e14
    #       fe80:0:0:0:b091:84ab:74e6:77a5
    #   children: none
    #   id:25 rloc16:0x6400 ext-addr:c638d2f97462f0b2 ver:4
    #   3-links:{ 02 }
    #   ip6-addrs:
    #       fdf5:991e:df88:2ada:0:ff:fe00:6400
    #       fdf5:991e:df88:2ada:47ea:4ff4:3f7b:f654
    #       fe80:0:0:0:c438:d2f9:7462:f0b2
    #   children: none
    #   Done

    # output of data parsed into router objects
    router_list = []

    iterator = 0
    while iterator < len(mesh_data_raw) and "Done" not in mesh_data_raw[iterator]:
        # Process the meta data string 
        data_list = mesh_data_raw[iterator].split()
        
        if "me" not in data_list:
            x_offset = None
            y_offset = None 
        # Extracting the relevant fields from the meta data string
        identifier = data_list[0].split(":")[1]
        rloc16 = data_list[1].split(":")[1]
        ext_addr = data_list[2].split(":")[1]
        ver = int(data_list[3].split(":")[1])
    
        # The "links fields may or may not appear depending on if 
        # there are other routers connected. Increment the iterator
        # and check if these exist using the while loop.
        iterator += 1 
        three_link = []
        two_link = []
        one_link = []

        while "ip6-addrs" not in mesh_data_raw[iterator]:
            # remove *-links
            link_no = mesh_data_raw[iterator][0]
            
            # We do not want the link number to be included 
            # in our regex.
            line = mesh_data_raw[iterator][1:]
            routers = re.findall(r'\d+', line)

            if link_no == 3:
                three_link = routers 
            if link_no == 2:
                two_link = routers
            if link_no == 1:
                one_link = routers

            iterator += 1

        ip_list = []

        # increment past the ip6-addrs label
        iterator += 1

        # ip addr list continues until children list
        while "children" not in mesh_data_raw[iterator]:
            ip_list.append(mesh_data_raw[iterator])
            iterator += 1

        child_list = []
       
        # confirm that there are children
        if not "none" in mesh_data_raw[iterator]:
            # increment past the children label
            iterator += 1

            # the next router contains the phrase "id", all entries until then are children
            while iterator < len(mesh_data_raw) and "id" not in mesh_data_raw[iterator] and \
                    "Done" not in mesh_data_raw[iterator]:
                child_data_list = mesh_data_raw[iterator].split()
                child_rloc16 = child_data_list[0].split(":")[1]
                child_lq = int(child_data_list[1].split(":")[1][0])
                child_mode = child_data_list[2].split(":")[1]
                new_child = Child(child_rloc16, child_lq, child_mode)

                child_list.append(new_child)
                iterator += 1

        # increment past last item
        iterator += 1

        # add router to the router list
        router_list.append(Router(loom_id, x_offset, y_offset, one_link, two_link, three_link, \
                rloc16, ext_addr, identifier, ver, ip_list, child_list))

    return router_list

def init_client_socket():
    host = "jacquard"
    port = 5005
    client_socket = socket.socket()
    client_socket.connect((host, port))
    print("Connected to jacquard socket.")
    return client_socket

def update_links(id_list, mesh_data):
    output = []
    for item in id_list:
        output.append(mesh_data[item].ext_addr)
    return output

if __name__ == "__main__":
    print("Beginning OpenThread topology gathering.")
   
    node_id = sys.argv[1]
    with open('nodes.yml', 'r') as f:
        active_nodes = (yaml.load(f, Loader=yaml.SafeLoader))
    
    node_x_pos = active_nodes[node_id]['left-offset']
    node_y_pos = active_nodes[node_id]['top-offset']

    ser = serial.Serial(SERIAL_PORT, BAUD_RATE)
    client_socket = init_client_socket()
    mesh_data = {}
    
    while True:
        mesh_data_raw = get_mesh_data(ser)
        
        try: 
           router_list = process_router_data(mesh_data_raw, node_id, node_x_pos, node_y_pos)
        except KeyboardInterrupt:
            ser.close()
            client_socket.close()
        
        for router in router_list:
            identifier = router.identifier
            if identifier not in mesh_data or mesh_data[identifier] != router:
                router.one_link = update_links(router.one_link, mesh_data)
                router.two_link = update_links(router.two_link, mesh_data)
                router.three_link = update_links(router.three_link, mesh_data)

                mesh_data[identifier] = router
                json_object = json.dumps(mesh_data[identifier].to_dict(), indent = 2)
                json_object = json_object.replace("\n", "").replace("\r", "")
                client_socket.send(json_object.encode())
        
        # check for new data every 5 seconds
        time.sleep(5)


def test():
    # Test data 
    sample_input = ["id:02 rloc16:0x0800 ext-addr:b29184ab74e677a5 ver:4 - me - leader",
                    "3-links:{ 25 }",
                    "ip6-addrs:",
                    "fdf5:991e:df88:2ada:0:ff:fe00:fc00",
                    "fdf5:991e:df88:2ada:0:ff:fe00:800",
                    "fdf5:991e:df88:2ada:1342:611f:5647:9e14",
                    "fe80:0:0:0:b091:84ab:74e6:77a5",
                    "children: none",
                    "id:25 rloc16:0x6400 ext-addr:c638d2f97462f0b2 ver:4",
                    "3-links:{ 02 }",
                    "ip6-addrs:",
                    "fdf5:991e:df88:2ada:0:ff:fe00:6400",
                    "fdf5:991e:df88:2ada:47ea:4ff4:3f7b:f654",
                    "fe80:0:0:0:c438:d2f9:7462:f0b2",
                    "children: none",
                    "Done"]

    sample_input2 = ["id:02 rloc16:0x0800 ext-addr:b29184ab74e677a5 ver:4 - me - leader",
                     "ip6-addrs:",
                     "fdf5:991e:df88:2ada:0:ff:fe00:fc00",
                     "fdf5:991e:df88:2ada:0:ff:fe00:800",
                     "fdf5:991e:df88:2ada:1342:611f:5647:9e14",
                     "fe80:0:0:0:b091:84ab:74e6:77a5",
                     "children:",
                     "rloc16:0x0802 lq:3, mode:rdn"]

    process_router_data(sample_input, 1, 1, 1)
    process_router_data(sample_input2, 1, 1, 1)

