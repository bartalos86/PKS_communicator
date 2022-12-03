import os
import pathlib
import time
import socket
import struct
import time
import zlib


header = struct.Struct('H I I H 200s I') 
destination_addr = ("127.0.0.1", 12000)
fragment_size = 1024
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.settimeout(1.0)

#Application start

print("Destination Ip:")
ip = input()
print("Destination port:")
port = int(input())

destination_addr = (ip, port)


def synchronize_with_server():
    not_sync = True
    packet_id = 0

    while not_sync:
        try:
            print("Sending sync")
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
    global header
    header = struct.Struct(f'H I I H {data_fragment_size}s I')
    print(f"Total frags: {total_fragments}")
    for frag_num in range(total_fragments):
        received = False
        while not received:
            message, _ = client_socket.recvfrom(fragment_size)
            packet = header.unpack(message)
            data_len = packet[2]
            received_data = packet[4][:int(packet[2])]
            client_crc = zlib.crc32(received_data)
            packet_crc = packet[5]
            packet_id = packet[1]
            #error verification
            if packet[0] == 7:
                print(f"Data fragment received - {packet_id} CRC passed: {client_crc == packet_crc}")
                if client_crc == packet_crc:
                    data += received_data;
                    header_data = header.pack(*(2, packet_id, 0, 0, b"", 0)) #OK
                    client_socket.sendto(header_data, destination_addr)
                    received = True
                else:
                    print("Sending RESEND REQUEST")
                    header_data = header.pack(*(4, packet_id, 0, 0, b"", 0)) #RESEND
                    client_socket.sendto(header_data, destination_addr)

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
    


def listen_for_requests():
    while True:
        try:
            header = struct.Struct(f'H I I H 200s I')
            message, _ = client_socket.recvfrom(fragment_size)
            packet = header.unpack(message)
            request_type = packet[0]
            data = str(packet[4][:int(packet[2])]).replace('\'','')
            print(data)
            if request_type == 6:
                data_type = int(packet[3])
                config = data.split(";")
                header_data = header.pack(*(2, packet[1], 0, 0, b"", 0)) #OK
                client_socket.sendto(header_data, destination_addr)
                if data_type == 0:
                    print(f"nss: {config}")
                    receive_data(data_type,int(config[2]),int(config[1]))
                else:
                    receive_data(data_type,int(config[2]),int(config[1]),config[0][1:])
        except TimeoutError:
            pass






synchronize_with_server()
listen_for_requests()
# message = "Hellow world!Hellow world!Hellow world!Hellow world!Hellow world!Hellow world!6".encode("utf-8")
# values = (3, 1, len(message),2, message, 2545)
# packed_data = header.pack(*values)

# client_socket.sendto(packed_data, destination_addr)
# print(client_socket.recvfrom(fragment_size)[0].decode("utf-8"))
