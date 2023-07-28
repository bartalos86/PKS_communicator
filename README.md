# UDP communication server and client
A program written in python that enables sending and receiving files and messages through the network from anywhere in the world. (Peer-to-peer) It features a custom protocol built over UDP, which has features such as connection re-estanblishment and packet re-sending in case of packets loss. The program has two modes, it can act as a client or a server.

During the run of the program after synchronization it is possible to switch the roles, this enables back-and-forth communication and file transfer. During file and message transfer it is possible to set the packet size for each operation. Every received packet is checked before deemed valid with CRC. If a packet is missing or lost during the transfer it is asked again by the client and retransmitted, same with the packets which has been corrupted.

## Features
- CRC error check
- Lost packet retransmission
- Custom packet size
- Keep-alive
- Ability to swicth client-server role automatically
- File and text transfer
- Handling of network interruptions

## Documentation
More in-depth documentation of the protocol and program can be found in the `Documentation` folder.

### Client
 <img src="/Showcase/client.png">

 ### Server
 <img src="/Showcase/server.png">

