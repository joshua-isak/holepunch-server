from audioop import add
import socket
import json
from threading import Thread
import time
import traceback


PORT = 420              # port this server will run on
SERVER_LIMIT = 0        # limit of broadcasting servers, 0 for no limit
KEEPALIVE_FREQ = 15     # how often to check for a server's last broadcast


broadcasting_servers = {}


class Server:
    def __init__(self, data):
        self.ip = data["ip"]
        self.port = data["port"]
        self.name = data["name"]
        self.version = ""
        self.description = ""
        self.player_count = 0
        self.player_limit = ""
        self.last_update = 0

    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__)



# Thread to periodically check if a server is still broadcasting
def keepalive_broadcast(running):

    while running:

        time.sleep(KEEPALIVE_FREQ)
        to_remove = []

        # Flag a server for removal if it hasn't updated in KEEPALIVE_FREQ seconds
        for x in broadcasting_servers.values():
            if (time.time() - x["last_update"] > KEEPALIVE_FREQ):
                to_remove.append(x["ip"] + str(x["port"]))
                print("{} has timed out".format(x["name"]))

        # Remove servers from broadcast dict (done here to prevent dict changed size during iteration error)
        for y in to_remove:
            broadcasting_servers.pop(y)



# Add a new server to the list of broadcasting servers
def handle_server_new_broadcast(data):

    # Check if we are over the server broadcasting limit
    if (SERVER_LIMIT == 0):
        pass
    elif (len(broadcasting_servers) >= SERVER_LIMIT):
        raise Exception("Exception: Unable to add broadcasting server, limit reached")

    # Create the new server object
    new_server = data #Server(data)
    new_server["last_update"] = time.time()  #.last_update = time.time()
    new_server.pop("message_type")

    # Add the server to the list of currently broadcasting servers
    broadcasting_servers[new_server["ip"] + str(new_server["port"])] = new_server
    print("Broadcasting new server '{}' from {}:{}".format(new_server["name"], new_server["ip"], new_server["port"]))



# Update an existing server's data in the list of broadcasting servers
def handle_server_update_broadcast(data):

    server = broadcasting_servers[data["ip"] + str(data["port"])]

    server["last_update"] = time.time()




# Send a client information about all servers currently broadcasting
def handle_client_list_request(data, sock):

    print("received new client list request from {}".format(data["ip"]+":"+data["port"]))

    # Prepare encoded json object containing all broadcasting server information
    response = {}
    response["servers"] = broadcasting_servers
    # for x in broadcasting_servers:
    #     response[x] = broadcasting_servers[x].toJson()

    response["message_type"] = "client_list_response"
    response = json.dumps(response).encode('utf-8')  #.replace("\\", "").encode('utf-8')

    # TODO add a max size check?? split into multiple packets?? TCP??

    # Send the response to the client
    address = (data["ip"], str(data["port"]))
    sock.sendto(response, address)



# Facilitate a UDP hole punch!
def handle_client_join_request():
    pass



def main():

    running = True      # TODO this needs to be a global variable or something, the keepalive thread doesn't shut down properly

    # Set up UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", PORT))
    print("Listening for incoming connections on port {}".format(PORT))

    # Start the keepalive thread
    k = Thread(target=keepalive_broadcast, args=(running,))
    k.start()

    # Packet handling loop
    while running:

        try:
            # Read in data from an incoming packet
            raw_data, address = sock.recvfrom(2048)         # read bytes from the socket
            data = json.loads(raw_data.decode('utf-8'))      # decode packet data as dictionary
            packet_type = data["message_type"]

            # Add socket connection information to data dictionary
            data["ip"] = address[0]
            data["port"] = address[1]

            # Set up a thread to handle packet type
            if (packet_type == "server_new_broadcast"):
                t = Thread(target=handle_server_new_broadcast, args=(data,))

            elif (packet_type == "server_update_broadcast"):
                t = Thread(target=handle_server_update_broadcast, args=(data,))

            elif (packet_type == "client_list_request"):
                t = Thread(target=handle_client_list_request, args=(data, sock))

            elif(packet_type == "client_join_request"):
                t = Thread(target=handle_client_join_request, args=(data,))

            else:
                raise Exception("Exception: packet_type not recognized")

            # Start the packet handling thread
            t.start()


        except KeyboardInterrupt:
            print("\nshutting down server...")
            running = False
            break

        except Exception as e:
            print("Error handling incoming connection!\n{}".format(e))
            traceback.print_exc()
            continue



# You already know who it is
main()