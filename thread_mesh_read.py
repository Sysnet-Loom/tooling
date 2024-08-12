import serial
import time

def encode_and_send(input_str, ser):
    input_str += "\r\n"
    input_str = input_str.replace('\\r','\r').replace('\\n','\n')
    encoded_data = input_str.encode('ascii')
    ser.write(encoded_data)

# todo make this more generic (for now we assume that the device is 
# /dev/ttyACM0 

def init_thread_device(ser):
    # Init dataset
    send_str = "dataset init new"
    print("Init dataset cmd: ", send_str)
    encode_and_send(send_str, ser)

    # Set channel
    send_str = "dataset channel 26"
    print("Set channel cmd: ", send_str)
    encode_and_send(send_str, ser)
    
    # Set panid
    send_str = "dataset panid 0xabcd"
    print("Set panid cmd: ", send_str)
    encode_and_send(send_str, ser)
    
    # Set networkkey
    send_str = "dataset networkkey 00112233445566778899aabbccddeeff"
    print("Set networkkey cmd: ", send_str)
    encode_and_send(send_str, ser)
    
    # Commit dataset
    send_str = "dataset commit active"
    print("Commit active dataset cmd: ", send_str)
    encode_and_send(send_str, ser)

    # Init ipv6 interface
    send_str = "ifconfig up"
    print("Initialize IPv6 interface cmd: ", send_str)
    encode_and_send(send_str, ser)
    
    # Start Thread network
    send_str = "thread start"
    print("Thread start cmd: ", send_str)
    encode_and_send(send_str, ser)

def read_mesh(ser):
    # check if joined network
    send_str = "state"
    encode_and_send(send_str, ser)
    state_data = read_timeout_serial(ser,0.25)
    
    while not "leader" in state_data:
        time.sleep(2)
        
        send_str = "state"
        encode_and_send(send_str, ser)
        state_data = read_timeout_serial(ser,0.25)

    # process 1 - send meshdiag topology request
    send_str = "meshdiag topology ip6-addrs children"
    print("Get mesh info cmd: ", send_str)
    encode_and_send(send_str, ser)

    # process2 - listen
    return read_timeout_serial(ser, 0.25)

def read_timeout_serial(ser, timeout):
    ser.timeout = timeout
    data = []

    while (True):
        new_data = ser.read_until().strip().decode("utf-8")
        if len(new_data) == 0:
            break
        # read from serial until timout is reached
        data.append(new_data)

    return data
                                                          

def get_mesh_data(ser):
    mesh_data = read_mesh(ser)
    output_data = []

    meshdiag_start_index = 0
    for iterator,item in enumerate(mesh_data):
        if 'meshdiag topology ip6-addrs children' in item:
            meshdiag_start_index = iterator + 1
            break
    
    meshdiag_iter = meshdiag_start_index
    while mesh_data[meshdiag_iter] != 'Done':
        # do something to process data here
        output_data.append(mesh_data[meshdiag_iter])
        meshdiag_iter += 1

    return output_data
