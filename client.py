import os
import pathlib
import threading
import time
import socket
import struct
import time
import zlib


header = struct.Struct('H I I H 200s I') 
destination_addr = ("127.0.0.1", 12000)
fragment_size = 1024
request_header = struct.Struct(f'H I I H 2s I')
keepalive_thread = None
keepalive_needed = True



def synchronize_with_server():
    not_sync = True
    packet_id = 0
    print("Waiting for synchronization....")
    while not_sync:
        try:
            header_data = header.pack(*(0, packet_id, 0, 0, b"", 0)) #SYNC
            client_socket.sendto(header_data, destination_addr)
            message, address = client_socket.recvfrom(fragment_size)
            resp = header.unpack(message)

            if resp[0] == 1 and resp[1] == packet_id + 1:
                not_sync = False
                print("Client: Connection established")
                packet_id = resp[1] +1
        except:
            time.sleep(2)

def receive_data(data_type = 0, data_fragment_size = 1024, total_fragments = 1, path = ""):
    data = b""

    #Turn off keepalive
    global keepalive_needed
    global keepalive_thread
    keepalive_needed = False
    if keepalive_thread != None:
        keepalive_thread.join()
    
    print(f"Total frags: {total_fragments}")
    data_header = struct.Struct(f'H I I H {data_fragment_size}s I')

    for frag_num in range(total_fragments):
        received = False
        while not received:
            try:
                message, address = client_socket.recvfrom(fragment_size)
                try:
                    packet = data_header.unpack(message) #DATA
                except struct.error:
                    print("Wrong header received")
                    continue

                data_len = packet[2]
                received_data = packet[4][:int(packet[2])]
                client_crc = zlib.crc32(received_data)
                packet_crc = packet[5]
                packet_id = packet[1]
                #error verification
                if packet[0] == 7:
                    print(f"Data fragment received - {packet_id} CRC passed: {client_crc == packet_crc}")
                    print(f"Packet {packet_id} frag num: {frag_num}")
                    if client_crc == packet_crc and packet_id == frag_num:
                        data += received_data;
                        header_data = request_header.pack(*(2, packet_id, 0, 0, b"", 0)) #OK
                        client_socket.sendto(header_data, destination_addr)
                        received = True
                    elif frag_num > packet_id:
                        print(f"Already received - {packet_id}")
                        header_data = request_header.pack(*(2, packet_id, 0, 0, b"", 0)) #OK
                        client_socket.sendto(header_data, destination_addr)
                    else:
                        print("Sending RESEND REQUEST")
                        header_data = request_header.pack(*(4, packet_id, 0, 0, b"", 0)) #RESEND
                        client_socket.sendto(header_data, destination_addr)
            except TimeoutError:
                pass

    if data_type == 0:
        print("Full data receeived!")
        print(data)
    else:
        print("Full file receeived!")
        ppath = pathlib.Path(path)
        ppath.parent.mkdir(parents=True, exist_ok=True)
        file = open(path, "wb")
        file.write(data)
        file.close()

    print("--------------------------------------------")
    if data_type == 1:
        print(f"Saved file: {os.path.basename(path)}")
        print(f"Path: {os.path.abspath(path)}")

    print(f"Total data size: {len(data)} B")
    print(f"Total number of fragments: {total_fragments}")
    print(f"Data fragment size: {data_fragment_size} B")
    print("--------------------------------------------")

def send_keep_alive():
    global keepalive_needed
    keepalive_needed = True
    timeout_count = 0
    global exit
    exit = False
    keepalive_header = struct.Struct(f'H I I H 2s I')
    packet_num = 0

    while keepalive_needed and not exit:
        try:
            header_data = keepalive_header.pack(*(5, packet_num, 0, 0, b"", 0)) #KEEP_ALIVE
            keepalive_socket.sendto(header_data, keepalive_addr)
            packet_num = packet_num +1
            time.sleep(3)
            message, _ = keepalive_socket.recvfrom(fragment_size)
            packet = keepalive_header.unpack(message)
            ok_id = packet[1]
            if packet[0] == 5 and (packet_num - ok_id <= 4):
                timeout_count = 0

           
        except TimeoutError:
            print("Tiemout")
            timeout_count = timeout_count +1
            if timeout_count > 3:
                print(f"Keepalive timed out - {timeout_count}")
                keepalive_needed = False
                exit = True
                quit()
        
        except ConnectionResetError:
            print("Keepalive: Connection with the server was terminated. Quitting...")
            exit = True
            quit()



def listen_for_requests():
    global keepalive_thread

    keepalive_thread = threading.Thread(target=send_keep_alive)
    keepalive_thread.start()
    global keepalive_needed
    global exit
    exit = False
    while not exit:
        try:
            # Keepalive
            if not keepalive_thread.is_alive():
                print("Restarting keepalive thread")
                keepalive_needed = True
                keepalive_thread = threading.Thread(target=send_keep_alive)
                keepalive_thread.start()
            header = struct.Struct(f'H I I H 200s I')
            message, _ = client_socket.recvfrom(fragment_size)
            try:
                packet = header.unpack(message)
            except:
                continue

            request_type = packet[0]
            data = str(packet[4][:int(packet[2])]).replace('\'','')

            if request_type == 3: #EXIT
                print("Exit received from the server. Quitting...")
                exit = True
                quit()

            if request_type == 6:
                data_type = int(packet[3])
                config = data.split(";")
                header_data = request_header.pack(*(2, packet[1], 0, 0, b"", 0)) #OK
                client_socket.sendto(header_data, destination_addr)
                if data_type == 0:
                    # print(f"nss: {config}")
                    receive_data(data_type,int(config[2]),int(config[1]))
                else:
                    receive_data(data_type,int(config[2]),int(config[1]),config[0][1:])
        except TimeoutError:
            pass
        except ConnectionResetError:
            print("Connection with the server was terminated. Quitting...")
            quit()


def start():
    global destination_addr
    global client_socket
    global keepalive_socket
    global keepalive_addr

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(2.5)

    # Keepalive
    keepalive_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    keepalive_socket.settimeout(3.0)

    #Application start

    print("Destination Ip:")
    ip = input()
    print("Destination port:")
    port = int(input())
    keepalive_addr = (ip, 9999)
    destination_addr = (ip, port)
    synchronize_with_server()
    listen_for_requests()



# message = "Hellow world!Hellow world!Hellow world!Hellow world!Hellow world!Hellow world!6".encode("utf-8")
# values = (3, 1, len(message),2, message, 2545)
# packed_data = header.pack(*values)

# client_socket.sendto(packed_data, destination_addr)
# print(client_socket.recvfrom(fragment_size)[0].decode("utf-8"))
