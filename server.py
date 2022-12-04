import math
import os
import random
import socket
import struct
import threading
import time
import zlib

header = struct.Struct('H I I H 1000s I') 
request_header = struct.Struct(f'H I I H 2s I')

# server_address = ('localhost', 12000)
client_address = None

fragment_size = 1024
packet_id = 0

keepalive_thread = None
keepalive_needed = True
exit = False



# keepalive_addr = ('192.168.0.122', 9999)


def synchronize_with_client():
    not_sync = True
    header = struct.Struct(f'H I I H 200s I')
    while not_sync:
        try:
            message, address = server_socket.recvfrom(fragment_size)
            resp = header.unpack(message) #SYNC
            print("REQUEST: " + str(resp[0]))
            packet_id = resp[1] +1
            if resp[0] == 0:
                header_data = header.pack(*(1, packet_id, 0, 0, b"", 0)) #SYNC ACK
                server_socket.sendto(header_data, address)
                not_sync = False
                global client_address
                client_address = address
        except TimeoutError:
            pass

def send_data(data = None, data_type = 0, data_fragment_size = 1024, path = "/null/", source_path = ""):

    if client_address is None:
        print("No connection established")
        return

    #Turn off keepalive
    global keepalive_needed
    global keepalive_thread
    keepalive_needed = False
    if keepalive_thread != None:
        keepalive_thread.join()

    data_fragments = math.ceil(len(data) / data_fragment_size)
    initialized = False

    print("--------------------------------------------")
    if data_type == 1:
        print(f"Sending file: {os.path.basename(source_path)}")
        print(f"Path: {os.path.abspath(source_path)}")

    print(f"Total data size: {len(data)} B")
    print(f"Total number of fragments: {data_fragments}")
    print(f"Data fragment size: {data_fragment_size} B")
    print("--------------------------------------------")


    

    data_header = struct.Struct(f'H I I H {data_fragment_size}s I')
    header = struct.Struct(f'H I I H 200s I')
    while not initialized:
        try:
            initialization_data = f"{path};{data_fragments};{data_fragment_size}".encode("utf-8")
            header_data = header.pack(*(6, 0, len(initialization_data), data_type, initialization_data, 0)) #Initialization
            server_socket.sendto(header_data, client_address)
            print("Init sent")
            message, _ = server_socket.recvfrom(fragment_size)
            resp = request_header.unpack(message) #OK
            if resp[0] == 2 and resp[1] == 0:
                print("Data transfer initialized")
                initialized = True
        except TimeoutError:
            time.sleep(1)
        except ConnectionResetError:
                print("The connection has been reset!")
                return

    for frag_num in range(data_fragments):
        sent = False
        while not sent:
            data_to_send = data[frag_num*data_fragment_size:((frag_num+1)*data_fragment_size)]
            data_len = len(data_to_send)
            server_crc = zlib.crc32(data_to_send)
            error_inserted = False

            #simulated_error
            if random.randrange(200) > 190 and not error_inserted:
                server_crc += 1
                error_inserted = True
            header_data = data_header.pack(*(7, frag_num, data_len, data_type, data_to_send, server_crc)) #Data

            try:
                server_socket.sendto(header_data, client_address)
                message, address = server_socket.recvfrom(fragment_size)
                resp = request_header.unpack(message) #OK or RESEND

                if resp[0] == 2 and client_address[1] == address[1] and resp[1] == frag_num:
                    # print("Packet trannsmitted")
                    sent = True
                elif resp[0] == 4 and resp[1] == frag_num:
                    print("Resend")
                elif resp[0] == 4:
                    print(f"Resend previous - {resp[1]} - {frag_num}")
                    frag_num = resp[1]
                    continue
                else:
                    pass
            except TimeoutError:
                pass
            except ConnectionResetError:
                print("The connection has been reset!")
                return

    print("All data has been sent!")
            

def send_text():
    print("----------------")
    print("What do you want to send: ")
    message = input()
    print("Fragment size: ")
    fragment_size = int(input())
    if fragment_size > 1004:
        print("Too big fragment size")
        fragment_size = 1004
    
    if fragment_size < 1:
        print("Fragment size cannot be smaller than 1, resetting to 2B")
        fragment_size = 2

    print(f"Destination will be ${client_address}")

    data = message.encode("utf-8")

    send_data(data, 0, fragment_size)


def send_file():
    print("----------------")
    print("Path to the file: ")
    path = input()
    print("Save file path: ")
    dest_path = input()
    print("Fragment size: ")
    fragment_size = int(input())
    if fragment_size > 1004:
        print("Too big fragment size")
        fragment_size = 1004
    
    if fragment_size < 1:
        print("Fragment size cannot be smaller than 1, resetting to 2B")
        fragment_size = 2

    print(f"Destination will be ${client_address}")

    file = open(path, "rb")
    file_size = os.path.getsize(path)
    data = file.read()
    send_data(data, 1, fragment_size, dest_path, path)

def process_keep_alive():
    global exit
    global keepalive_needed
    keepalive_header = struct.Struct(f'H I I H 2s I')
    exit = False
    timeout_count = 0
    while keepalive_needed and not exit:
        try:
            message, address = keepalive_socket.recvfrom(fragment_size)
            packet = keepalive_header.unpack(message)
            request_type = packet[0]
            packet_id = packet[1]
            if request_type == 5:
                header_data = keepalive_header.pack(*(5, packet_id, 0, 0, b"", 0)) #OK
                keepalive_socket.sendto(header_data, address)
                timeout_count = 0

        except TimeoutError:
            timeout_count = timeout_count +1
            if timeout_count > 3:
                print(f"Keepalive timed out - {timeout_count}")
                exit = True
                quit()

        except ConnectionResetError:
            print("connection has been reset! - Keepalive")
            exit = True
            quit()
        
def listen_for_commands():
    global keepalive_thread
    keepalive_thread = threading.Thread(target=process_keep_alive)
    keepalive_thread.start()
    global exit
    global keepalive_needed
    exit = False
    while not exit:

        # Keepalive
        if not keepalive_thread.is_alive():
            print("Restarting keepalive thread")
            keepalive_needed = True
            keepalive_thread = threading.Thread(target=process_keep_alive)
            keepalive_thread.start()

        print("What do you want to do?")
        print("1 - send text")
        print("2 - send file")
        print("3 - exit")
        response  = input()

        if response == "1":
            send_text()
        elif response == "2":
            send_file()
        elif response == "3":
            keepalive_needed = False
            keepalive_thread.join()
            header = struct.Struct(f'H I I H 200s I')
            header_data = header.pack(*(3, 0, 0, 0, b"", 0)) #EXIT
            server_socket.sendto(header_data, client_address)

            exit = True
            # keepalive_thread.join()
        else:
            print("Unknown command")
    
def start():
    global server_address
    global server_socket
    global keepalive_socket
    print("Listening Ip:")
    ip = str(input())
    print("Listening port:")
    port = int(input())

    server_address = (ip, port)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(server_address)
    server_socket.settimeout(2.0)


    keepalive_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    keepalive_socket.settimeout(5.0)
    keepalive_socket.bind((ip,9999))
    synchronize_with_client()
    listen_for_commands()



# message, address = server_socket.recvfrom(fragment_size)
# unpacked_data = header.unpack(message)
# data = unpacked_data[4][:int(unpacked_data[2])]
# print(unpacked_data)
# print(data)

    