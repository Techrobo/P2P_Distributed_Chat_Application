import multiprocessing
import socket
import threading
import time
import json
import random
import uuid
import random

# PROJECT Peer-to-Peer Chat-based Distributed Application
# Group 18 :  Ikenna Abara[3644968] and Shubham Gupta[3506475]
# Contact : st173207@stud.uni-stuttgart.de


class PeerDiscoveryProtocol:
    # Define message formats for registration, deregistration, and querying active peers.
    # Implement basic message parsing functions
    @staticmethod
    def encode_register(name, ip, heartbeat_port, message_port):
        return json.dumps({'action': 'register', 'name': name, 'ip': ip, 'heartbeat_port': heartbeat_port, 'message_port':  message_port}).encode()
    
    @staticmethod
    def encode_register_reply(name, ip, heartbeat_port, message_port):
        return json.dumps({'action': 'yes', 'name': name, 'ip': ip, 'heartbeat_port': heartbeat_port, 'message_port':  message_port}).encode()
    
    @staticmethod
    def encode_election(name, id, ip, election_port):
        return json.dumps({'action': 'election', 'name': name, 'id': id, 'ip': ip, 'election_port': election_port}).encode()
  
    @staticmethod
    def encode_voting(name, id, ip, election_port):
        return json.dumps({'action': 'voting', 'name': name, 'id': id, 'ip': ip, 'election_port': election_port}).encode() 
    
    @staticmethod
    def encode_voting_result():
        return json.dumps({'action': 'OK'}).encode()
    
    @staticmethod
    def encode_deregister(name, heartbeat_port, message_port):
        return json.dumps({'action': 'deregister', 'name': name, 'heartbeat_port': heartbeat_port, 'message_port':  message_port}).encode()

    @staticmethod
    def encode_register_confirmation():
        return json.dumps({'action': 'registered'}).encode()

    @staticmethod
    def encode_query():
        return json.dumps({'action': 'query'}).encode()

    @staticmethod
    def encode_heartbeat(name, ip, heartbeat_port):
        return json.dumps({'action': 'heartbeat', 'name': name, 'ip': ip, 'port':  heartbeat_port, }).encode()

    @staticmethod
    def decode_message(data):
        return json.loads(data.decode())


class ServerClientProcess(multiprocessing.Process):
    def __init__(self):
        super(ServerClientProcess, self).__init__()
        self.id = self.generate_unique_id()
        self.ip = socket.gethostbyname(socket.gethostname())
        self.heartbeat_port = self.get_available_port()
        self.message_port = self.get_available_port()
        self.election_port = self.get_available_port()
        self.broadcast_port = 12345
        self.server_ip = None
        self.server_heartbeat_port = None
        self.server_message_port = None
        self.is_client = True
        self.is_first = True
        self.is_leader = False
        self.voting_end_flag = False
        self.client_thread_stop_flag = False
        self.client_registeration_flag = False
        self.timeout = 5  # Timeout for socket operations in seconds
        # "User_".join(self.generate_hash())
        self.name = input("Enter your name: ")

        self.active_peers = []
        self.voting_participants = []

########### START : HELPER METHODS ############
    def generate_unique_id(self):
        # Generate a random delay between 0 and 999 milliseconds
        random_ms = random.randint(0, 999) / 1000
        # Sleep for 1 second plus the random milliseconds
        time.sleep(1 + random_ms)
        # Get current time in milliseconds
        current_time_ms = int(time.time() * 1000)
        # Generate a UUID (unique identifier)
        unique_identifier = str(uuid.uuid4()).replace('-', '')[:8]
        # Combine timestamp and UUID to create a unique and sortable ID
        unique_id = f"{current_time_ms}-{unique_identifier}"
        return unique_id

    def get_available_port(self):
        # Create a socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Bind to an available port
            s.bind(('0.0.0.0', 0))
            # Get the port that was allocated by the operating system
            _, port = s.getsockname()
            print(f"Self Port: {port}")
            return port

    def is_first_(self):
        # Check if the broadcast port is open
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(2)
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                print("Braoadcast Check by Peer")
                sock.bind(('0.0.0.0', self.broadcast_port))
                data, server_address = sock.recvfrom(1024)
                print("Broadcast Found From Server : ", server_address)
                return False
            except OSError:
                print("No Broadcast Port Found")
                return True
########### END : HELPER METHODS ############

########### START : DECISION FOR PEER ROLE METHODS ############
    def run(self):
        # Generate a random delay between 0 and 999 milliseconds
        random_ms = random.randint(0, 999) / 1000
        # Sleep for 1 second plus the random milliseconds
        time.sleep(random_ms)
        
        self.base_processes()
        
        self.peer_process()
        
    def peer_process(self):
        self.is_client = True
        self.is_first = True
        self.is_leader = False
        self.client_thread_stop_flag = False
        self.client_registeration_flag = False
        self.is_client= self.initiate_election()
        
        if (self.is_client):
            print("Election Finished : Peer Act as Client")
            self.run_client()
        else:
            print("Election Finished : Peer Act as Leader")
            self.run_server()
    

########### END :  DECISION FOR PEER ROLE METHODS ############

########### START :VOTING ELECTION METHODS ############
    
    def base_processes(self):
        print("Base Processes Start")
        election_initiation_thread = threading.Thread(
            target=self.send_election_broadcast_messages)

        election_initiation_thread.start()

        #election_initiation_thread.join() //This thread is  never ending


                
    def send_election_broadcast_messages(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as broadcast_sock:
            broadcast_sock.setsockopt(
                socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            message = PeerDiscoveryProtocol.encode_election(
                self.name, self.id, self.ip, self.election_port)

            while True:
                broadcast_sock.sendto(
                    message, ('<broadcast>', self.broadcast_port))
                time.sleep(2)
                #print("Election Process broadcasting on port:", self.broadcast_port)
   
    # Always Satrted when running as a client or server
    def handle_voting_requests(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as registration_sock:
            registration_sock.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            registration_sock.bind((self.ip, self.election_port))

            registration_sock.settimeout(10)
            while True:
                try:
                    data, _ = registration_sock.recvfrom(1024)
                    decoded_msg = PeerDiscoveryProtocol.decode_message(data)
                    if decoded_msg['action'] == 'voting':
                        print(self.name, ": Election Request Received from", decoded_msg['name'])
                        print(self.name, ": Election Confirmation Sent to ", decoded_msg['name'])     
                        registration_sock.sendto(PeerDiscoveryProtocol.encode_voting_result(), (decoded_msg['ip'],  decoded_msg['election_port']))
                        if(not self.is_leader):
                            # Wait for the thread to finish
                            print(self.name, ": Finishing Existing Client Registeration", decoded_msg['name'])
                            self.client_thread_stop_flag = True
                            #Run again 
                            self.peer_process()
                            #Start election
                        else :
                            print(self.name, "Already I am Leader, No Election Needed")   
                            
                except socket.timeout:
                    print("Server timed out waiting for voting requests")        
            

    def initiate_election(self):
        print("Starting Election")

        election_process_thread = threading.Thread(
            target=self.receive_election_broadcast_messages)

        election_process_thread.start()

        election_process_thread.join()
        return self.is_client
                
    def receive_election_broadcast_messages(self):
        start_time = time.time()  # Record the start time
        # Set up a socket for receiving broadcast messages
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as election_sock:
            election_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            #election_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            election_sock.bind(('0.0.0.0', self.broadcast_port))

            print("Listening for broadcast of candidates for election ")
        
            election_sock.settimeout(10)
            while time.time() - start_time < 10:  # Run for 10 seconds
                try:
                    data, _ = election_sock.recvfrom(1024)
                    decoded_msg = PeerDiscoveryProtocol.decode_message(data)
                    if decoded_msg['action'] == 'election' and decoded_msg['name'] != self.name :
                        print("Found Election Participant :",decoded_msg['name'])
                        self.is_first = False
                        if(self.id>decoded_msg['id']):
                            print("Qualified Voting Participant :",decoded_msg['name'])
                            self.voting_participants.append({'name':decoded_msg['name'], 'id':decoded_msg['id'], 'ip':decoded_msg['ip'], 'election_port':decoded_msg['election_port']})   
                except socket.timeout:
                    self.is_first = True    
                    print("Election Participants Listening Call timed out : Process over")
        if(len(self.voting_participants)>0):
            sorted_participants = sorted(self.voting_participants, key=lambda x: x['id'], reverse=False)
            
            for participant in sorted_participants:
                print("Sending Voting Request To ", participant['name'])
                self.send_election_request_thread(participant['ip'],participant['election_port'])
                if(self.voting_end_flag):
                    print("Voting Finished")
                    self.voting_participants.clear()
                    break
                       
        elif (self.is_first):
            self.is_client = False
            self.is_leader = True
            
    
    def send_election_request_thread(self,peer_ip,peer_port):
        registration_thread = threading.Thread(
            target=self.send_election_request, args=(peer_ip,peer_port))
        registration_thread.start()
        registration_thread.join()
            
    def send_election_request(self, peer_ip, peer_port):
        start_time = time.time()  # Record the start time
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as registration_sock_:
            registration_sock_.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            registration_sock_.bind((self.ip, self.election_port))
           
            registration_sock_.settimeout(10)
            while time.time() - start_time < 10:  # Run for 10 seconds
                #time.sleep(2)
                try:
                    registration_sock_.sendto(PeerDiscoveryProtocol.encode_voting(self.name, self.id, self.ip, self.election_port),
                                            (peer_ip, peer_port))
                    data, _ = registration_sock_.recvfrom(1024)
                    decoded_msg = PeerDiscoveryProtocol.decode_message(data)
                    if( decoded_msg['action'] == 'OK'):
                        print("Received voting confirmation from peer")
                        self.is_client = True
                        self.voting_end_flag = True
                        return
                        
                except socket.timeout:
                    print("No Voting Confirmation received confirmation from peer")
                    self.is_client = False   

        
########### END :VOTING ELECTION METHODS ############
            

########### START : SERVER (LEADER) METHODS ############

    def send_discovery_broadcast_messages(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as broadcast_sock:
            broadcast_sock.setsockopt(
                socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            message = PeerDiscoveryProtocol.encode_register(
                self.name, self.ip, self.heartbeat_port, self.message_port)

            while True:
                broadcast_sock.sendto(
                    message, ('<broadcast>', self.broadcast_port))
                time.sleep(2)
                print("Server broadcasting on port:", self.broadcast_port)

    def handle_registration_requests(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as registration_sock:
            registration_sock.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            registration_sock.bind((self.ip, self.heartbeat_port))

            registration_sock.settimeout(10) 
            while True:
                try:
                    data, _ = registration_sock.recvfrom(1024)
                    decoded_msg = PeerDiscoveryProtocol.decode_message(data)
                    if decoded_msg['action'] == 'yes':
                        self.active_peers.append({'name': decoded_msg['name'], 'status': 'registered', 'ip': decoded_msg['ip'],
                                                 'heartbeat_port': decoded_msg['heartbeat_port'], 'message_port': decoded_msg['message_port']})
                        registration_sock.sendto(PeerDiscoveryProtocol.encode_register_confirmation(
                        ), (decoded_msg['ip'],  decoded_msg['heartbeat_port']))
                        print(
                            f"Registered peer: {decoded_msg['name']} : {decoded_msg['ip']} :{decoded_msg['heartbeat_port']}")
                        time.sleep(2)                
                except socket.timeout:
                    print("Server timed out waiting for registration requests")
                except ConnectionResetError as e:
                     print("ConnectionResetError:", e)
                     # Handle the error or perform cleanup actions
                     # # Close the socket to release system resources
                     registration_sock.close()
                     return
                    

    def run_server(self):
        print("Peer is First Node , Acting as a Server(Leader)")
        broadcast_thread = threading.Thread(
            target=self.send_discovery_broadcast_messages)
        registration_thread = threading.Thread(
            target=self.handle_registration_requests)
        election_result_thread= threading.Thread(
            target=self.handle_voting_requests)

        broadcast_thread.start()
        registration_thread.start()
        election_result_thread.start()

        #broadcast_thread.join() //Never ending
        #registration_thread.join()
        #election_result_thread.join()

  ########### END : SERVER (LEADER) METHODS ############

  ########### START : CLIENT METHODS ############

    def send_registration_request(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as registration_sock_:
            registration_sock_.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            registration_sock_.bind((self.ip, self.heartbeat_port))
            registration_sock_.settimeout(5)
            while True :
                try:
                    registration_sock_.sendto(PeerDiscoveryProtocol.encode_register_reply(self.name, self.ip, self.heartbeat_port, self.message_port),
                                              (self.server_ip,  self.server_heartbeat_port))
                    data, _ = registration_sock_.recvfrom(1024)
                    decoded_msg = PeerDiscoveryProtocol.decode_message(data)
                    if( decoded_msg['action']=='registered'):
                        #print(
                        #    f"Received confirmation from server {self.server_ip} : { decoded_msg['action'] }")
                        self.client_registeration_flag = True
                    time.sleep(2)
                        
                except socket.timeout:
                    print("Client timed out waiting for Server Registeration Confirmation, Leader Dead ")
                    # Wait for the thread to finish
                    print(self.name, ": Finishing Existing Client Registeration")
                    self.client_thread_stop_flag = True
                    self.client_registeration_flag = False
                    return
                    #Start election
                except ConnectionResetError as e:
                    print("ConnectionResetError:", e)
                    # Handle the error or perform cleanup actions
                    # # Close the socket to release system resources
                    registration_sock_.close()
                    return
            #registration_sock_.close()

    def send_registration_thread(self):
        registration_thread = threading.Thread(
            target=self.send_registration_request)
        registration_thread.start()
        registration_thread.join() #Regiteration thread finished due to leader dead timeout
        self.peer_process()

    def receive_discovery_broadcast_messages(self):
        # Set up a socket for receiving broadcast messages
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_sock:
            client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            client_sock.bind(('0.0.0.0', self.broadcast_port))

            print("Client listening for server broadcast ")

            while True:
                # client_sock.settimeout(5)
                if(self.client_thread_stop_flag):
                    client_sock.close
                    return
                try:
                    data, _ = client_sock.recvfrom(1024)
                    decoded_msg = PeerDiscoveryProtocol.decode_message(data)

                    if (decoded_msg['action'] == 'register' and decoded_msg['name'] != self.name and not self.client_registeration_flag):
                        print(
                            f"Received registration broadcast message from server { decoded_msg['name'] }")
                        self.server_ip = decoded_msg['ip']
                        self.server_heartbeat_port = decoded_msg['heartbeat_port']
                        # Extract IP and port from server_address
                        self.server_message_port = decoded_msg['message_port']
                        #self.send_registration_request()
                        self.send_registration_thread()

                except socket.timeout:
                    print("Client timed out waiting for broadcast messages")

    def run_client(self):
        print("Peer is Acting as client")
        time.sleep(1)  # Wait for the server to start

        broadcast_thread = threading.Thread(
            target=self.receive_discovery_broadcast_messages)
        election_result_thread= threading.Thread(
            target=self.handle_voting_requests)

        election_result_thread.start()

        broadcast_thread.start()

        broadcast_thread.join()
        election_result_thread.join()

    ########### END : CLIENT METHODS ############


if __name__ == "__main__":
    process = ServerClientProcess()
    process.start()
    process.join()
