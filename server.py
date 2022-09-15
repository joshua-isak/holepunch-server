from audioop import add
import socket
import json
import threading
from threading import Thread
import time


PORT = 420              # port this server will run on
SERVER_LIMIT = 0        # limit of broadcasting servers, 0 for no limit
KEEPALIVE_FREQ = 10     # how often to check for a server's last broadcast


broadcasting_servers = {}


class Server:
    def __init__(self, data):
        self.ip = data["ip"]
        self.port = data["port"]
        self.name = ""
        self.version = ""
        self.description = ""
        self.player_count = 0
        self.player_limit = ""
        self.last_update = 0



# Thread to periodically check if a server is still broadcasting
def keepalive_broadcast():

    time.sleep(KEEPALIVE_FREQ)

    # Remove server from broadcasting list if it hasn't updated in KEEPALIVE_FREQ seconds
    for x in broadcasting_servers:
        if (time.time() - x.last_update > KEEPALIVE_FREQ):
            broadcasting_servers.pop(x.ip + str(x.port))



# Add a new server to the list of broadcasting servers
def handle_server_new_broadcast(data):

    # Check if we are over the server broadcasting limit
    if (SERVER_LIMIT == 0):
        pass
    elif (len(broadcasting_servers) >= SERVER_LIMIT):
        raise Exception("Exception: Unable to add broadcasting server, limit reached")

    # Create the new server object
    new_server = Server(data)
    new_server.last_update = time.time()

    # Add the server to the list of currently broadcasting servers
    broadcasting_servers[new_server.ip + str(new_server.port)] = new_server
    print("Broadcasting new server from {}:{}".format(new_server.ip, new_server.port))



# Update an existing server's data in the list of broadcasting servers
def handle_server_update_broadcast():
    pass



# Send a client information about all servers currently broadcasting
def handle_client_list_request():
    pass



# Facilitate a UDP hole punch!
def handle_client_join_request():
    pass



def main():

    running = True

    # Set up UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", PORT))
    print("Listening for incoming connections on port {}".format(PORT))

    # Start the keepalive thread
    k = Thread(target=keepalive_broadcast, args=())
    k.start()

    # Packet handling loop
    while running:

        try:
            # Read in data from an incoming packet
            raw_data, address = sock.recvfrom(2048)         # read bytes from the socket
            data = json.load(raw_data.decode('utf-8'))      # decode packet data as dictionary
            packet_type = data["message_type"]

            # Add socket connection information to data dictionary
            data["ip"] = address[0]
            data["port"] = address[1]

            # Set up a thread to handle packet type
            if (packet_type == "server_new_broadcast"):
                t = Thread(target=handle_server_new_broadcast, args=(data))

            elif (packet_type == "server_update_broadcast"):
                t = Thread(target=handle_server_update_broadcast, args=(data))

            elif (packet_type == "client_list_request"):
                t = Thread(target=handle_client_list_request, args=(data))

            elif(packet_type == "client_join_request"):
                t = Thread(target=handle_client_join_request, args=(data))

            else:
                raise Exception("Exception: packet_type not recognized")

            # Start the packet handling thread
            t.start()

        except Exception as e:
            print("Error handling incoming connection!\n{}".format(e))
            continue



# You already know who it is
main()