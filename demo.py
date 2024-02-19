from multiprocessing  import Process, Lock
import socket
import threading
import time
import json
import random
import uuid
import struct

# PROJECT Peer-to-Peer Chat-based Distributed Application
# Group 18 :  Ikenna Abara[3644968] and Shubham Gupta[3506475]
# Contact : st173207@stud.uni-stuttgart.de


class PeerDiscoveryProtocol:
    # Define message formats for registration, deregistration, and querying active peers.
    # Implement basic message parsing functions
    @staticmethod
    def encode_register(name, id, ip, registeration_port, heartbeat_port, message_port, multicast_address):
        return json.dumps({'action': 'register', 'name': name,'id': id, 'ip': ip, 'registeration_port': registeration_port, 'heartbeat_port': heartbeat_port, 'message_port':  message_port,'multicast_address': multicast_address}).encode()
    
    @staticmethod
    def encode_register_reply(name, id, ip, registeration_port, heartbeat_port, message_port):
        return json.dumps({'action': 'yes', 'name': name,'id': id, 'ip': ip, 'registeration_port': registeration_port,  'heartbeat_port': heartbeat_port, 'message_port':  message_port}).encode()
    
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
    def encode_deregister(name, registeration_port, message_port):
        return json.dumps({'action': 'deregister', 'name': name, 'registeration_port': registeration_port, 'message_port':  message_port}).encode()

    @staticmethod
    def encode_register_confirmation():
        return json.dumps({'action': 'registered'}).encode()

    @staticmethod
    def encode_query():
        return json.dumps({'action': 'query'}).encode()

    @staticmethod
    def encode_heartbeat(name, ip, heartbeat_port):
        return json.dumps({'action': 'heartbeat', 'name': name, 'ip': ip, 'heartbeat_port':  heartbeat_port, }).encode()

    @staticmethod
    def decode_message(data):
        return json.loads(data.decode())


class ServerClientProcess(Process):
    def __init__(self):
        super(ServerClientProcess, self).__init__()
        self.id = self.generate_unique_id()
        self.ip =  self.get_ip_address() #socket.gethostbyname(socket.gethostname())
        self.heartbeat_port = self.get_available_port()
        self.registeration_port = self.get_available_port()
        self.message_port = self.get_available_port()
        self.election_port = self.get_available_port()
        self.broadcast_port = 12345
        self.broadcast_ip = self.get_broadcast_ip()
        self.multicast_address = '224.0.0.1' #self.generate_multicast_group()
        self.multicast_group = None
        self.server_ip = None
        self.server_heartbeat_port = None
        self.server_registeration_port = None
        self.server_message_port = None
        self.is_client = True
        self.is_first = True
        self.is_leader = False
        self.voting_end_flag = False
        self.demand_election = False
        self.timeout = 5  # Timeout for socket operations in seconds
        # "User_".join(self.generate_hash())
        self.name = input("Enter your name: ")

        self.active_peers = []
        self.voting_participants = []
        
        #Multicast Variables
        self.vector_clock = {self.id: 0}
        self.hold_back_queue = []
        self.message_history_buffer = dict({})
        self.displayed_own_message = set()
        self.lock = Lock()
        self.client_registeration_flag = False 

########### START : HELPER METHODS ############
    def get_broadcast_ip(self):
        try:
            # Get the local IP address
            local_ip = self.ip

            # Get the subnet mask
            subnet_mask = self.get_subnet_mask()
            print("Subnet Mask : ",subnet_mask)

            if local_ip and subnet_mask:
                # Calculate the network address
                network_address = '.'.join(str(int(local_ip.split('.')[i]) & int(subnet_mask.split('.')[i])) for i in range(4))

                # Calculate the broadcast address
                broadcast_address = '.'.join(str(int(network_address.split('.')[i]) | (255 - int(subnet_mask.split('.')[i]))) for i in range(4))
                print("Broadcast IP :" , broadcast_address)
                return broadcast_address
            else:
                return None
        except Exception as e:
            print("Error:", e)
            return None
    
    def get_subnet_mask(self):
        return '255.255.255.0'
    
    def get_ip_address(self):
        # Create a socket object
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Connect to any IP address (here, we use Google's public DNS server)
            s.connect(('8.8.8.8', 80))
            # Get the local IP address
            ip_address = s.getsockname()[0]
            print("IP Address : ",ip_address)
        finally:
            # Close the socket
            s.close()
        
        return ip_address

    def generate_multicast_group(self):
        # Only generated by server(Leader)
        # Generate a random multicast group address within the valid range
        # Range for multicast group addresses: 224.0.0.0 to 239.255.255.255
        # But certain ranges are reserved, so we avoid those
        multicast_range_start = struct.unpack('!I', socket.inet_aton('224.0.0.0'))[0]
        multicast_range_end = struct.unpack('!I', socket.inet_aton('239.255.255.255'))[0]
        while True:
            multicast_address = socket.inet_ntoa(struct.pack('!I', random.randint(multicast_range_start, multicast_range_end)))
            if not (224 <= int(multicast_address.split('.')[0]) <= 239):
                continue  # Skip addresses outside the valid range
            if multicast_address.startswith('224.0') or multicast_address.startswith('224.255'):
                continue  # Skip reserved addresses
            print("Multicast Address : ",multicast_address)
            return multicast_address
        
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
        self.demand_election = False
        self.client_registeration_flag = False
        self.voting_end_flag= False
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
                    message, (self.broadcast_ip, self.broadcast_port))
                time.sleep(2)
                #print("Election Process broadcasting on port:", self.broadcast_port)
   
    # Always Started when running as a client or server
    def handle_voting_requests(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as registration_sock:
            registration_sock.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            registration_sock.bind((self.ip, self.election_port))

            registration_sock.settimeout(10)
            while True:
                # client_sock.settimeout(5)
                if(self.demand_election):
                    registration_sock.close()
                    time.sleep(2)  # Wait for the socket to close
                    return
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
                            self.demand_election = True
                            registration_sock.close()
                            time.sleep(2)  # Wait for the socket to close
                            return
                        else :
                            print(self.name, "Already I am Leader, No Election Needed")   
                            
                except socket.timeout:
                    print("Server timed out waiting for voting requests") 
                except ConnectionResetError as e:
                     print("ConnectionResetError in handle_voting_requests:", e)
                     # Handle the error or perform cleanup actions
                     # # Close the socket to release system resources
                     registration_sock.close()
                     time.sleep(2)  # Wait for the socket to close
                     return       
            

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
                    if decoded_msg['action'] == 'election' and decoded_msg['id'] != self.id :
                        print("Found Election Participant :",decoded_msg['name'])
                        self.is_first = False
                        if(self.id>decoded_msg['id']):
                           
                            # Check if 'id' already exists in the list
                            id_exists = False
                            for participant in self.voting_participants:
                                if participant['id'] == decoded_msg['id']:
                                    # If 'id' already exists, set flag and break out of the loop
                                    id_exists = True
                                    break
                            # If 'id' already exists, skip to next iteration
                            if id_exists:
                                continue
                            print("Qualified Voting Participant :",decoded_msg['name'])
                            self.voting_participants.append({'name':decoded_msg['name'], 'id':decoded_msg['id'], 'ip':decoded_msg['ip'], 'election_port':decoded_msg['election_port']})   
                except socket.timeout:
                    self.is_first = True    
                    print("Election Participants Listening Call timed out : Process over")
                except ConnectionResetError as e:
                     print("ConnectionResetError in receive_election_broadcast_messages:", e)
                     # Handle the error or perform cleanup actions
                     # # Close the socket to release system resources
                     election_sock.close()
                     time.sleep(2)  # Wait for the socket to close
                     return  
                
        if(len(self.voting_participants)>0):
            sorted_participants = sorted(self.voting_participants, key=lambda x: x['id'], reverse=False)
            
            for participant in sorted_participants:
                print("Sending Voting Request To ", participant['name'])
                self.send_election_request_thread(participant['ip'],participant['election_port'])
                if(self.voting_end_flag):
                    print("Voting Finished")
                    self.voting_participants.clear()
                    return
            if(not self.voting_end_flag):
                print("No Qualified Voting Participant Replied, Repeating Election")
                self.voting_participants.clear()
                self.is_client = True
                self.is_first = True
                self.is_leader = False
                self.demand_election = False
                self.client_registeration_flag = False
                self.receive_election_broadcast_messages()
                       
        else:
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
                        registration_sock_.close()
                        time.sleep(2)  # Wait for the socket to close
                        return
                        
                except socket.timeout:
                    print("No Voting Confirmation received confirmation from peer")
                    self.is_client = False
               
                except ConnectionResetError as e:
                     print("ConnectionResetError in send_election_request:", e)
                     # Handle the error or perform cleanup actions
                     # # Close the socket to release system resources
                     registration_sock_.close()
                     time.sleep(2)  # Wait for the socket to close
                     return     
                

        
########### END :VOTING ELECTION METHODS ############

  ########### START : MULTICAST METHODS ############
  
  #Sending Multicast#
  
    def test_multicast(self):
        count = 0
        num_list = [15, 20, 25, 30]
        while True:
            if(not self.client_registeration_flag) :
                continue
            if(self.demand_election):
                #listen_sock.close()
                time.sleep(2)  # Wait for the socket to close
                return
            time.sleep(random.choice(num_list))
            count += 1
            message = f"{count}: Hello from {self.name} with ID: {self.id}"
            print (message)
            #self.send_multicast(message, "normal", "224.0.0.2", 7000)
            self.send_multicast(message, "normal", self.multicast_group, self.server_heartbeat_port)
            
    def send_multicast(self, message, message_type, multicast_group, port):
        multicast_send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        #set the time-to-live to binary format, and restrict the hops to the LAN
        ttl = struct.pack('b', 1)
        multicast_send_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        
        #serialize message & increment vector clock before send event
        json_msg = self.send_event_vector(message, message_type)
        try:
            multicast_send_socket.sendto(str.encode(json_msg), (multicast_group, port))
        except Exception as e:
            print(e)
   
    def send_event_vector(self, message, message_type):
        
        if message_type == "NACK":
            #serialize message before sending
            print("sending nack message...")
            serialized_message = json.dumps({
                'content': message,
                'vector_clock': self.vector_clock,
                'sender_id': self.id,
                'type': message_type
            })

        elif message_type == "normal":
            #increament vector clock before send event
            print("sending normal message...")
            self.lock.acquire()
            self.vector_clock[self.id] += 1
            self.lock.release()

            #serialize message before sending
            serialized_message = json.dumps({
                'content': message,
                'vector_clock': self.vector_clock,
                'sender_id': self.id,
                'type': message_type
            })

            #add outgoing message to peer's history buffer
            self.message_history_buffer[self.vector_clock[self.id]] = serialized_message
            
            #print("current history buffer: ", self.message_history_buffer)

        return serialized_message
    
    #Receiving Multicast#
    
    def listen_for_multicast(self, ip, port, multicast_group):
        listen_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        listen_sock.bind((ip, port))

        #configure the socket to join a multicast group, listens on any available interface
        group = socket.inet_aton(multicast_group)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        listen_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        print("listening for multicast... at :",multicast_group)

        while True:
            if(not self.client_registeration_flag) :
                continue
            if(self.demand_election):
                listen_sock.close()
                time.sleep(2)  # Wait for the socket to close
                return
            msg, addr = listen_sock.recvfrom(1024)

            if msg:
                data = json.loads(msg.decode())
                #print(f"'{data['content']}' received from {data['sender_id']} with timestamp: {data['vector_clock']}")
                self.rec_event_vector(data['content'], data['vector_clock'], data['sender_id'], data['type'])
                #print(f"My new timestamp is: {self.vector_clock}")
                
    def rec_event_vector(self, received_message, received_vector_clock, sender_id, received_message_type):
        #print(message_rejection_test)
        if sender_id not in self.vector_clock:
                        # When a message is recieved from a peer for the first time, initialise its timestamp.
                        for peer, timestamp in received_vector_clock.items():
                            if peer == sender_id:
                                self.vector_clock[peer] = timestamp - 1 #self.vector_clock[sender_id] = received_vector_clock[sender_id] - 1
                            else:
                                if peer not in self.vector_clock:
                                    self.vector_clock[peer] = timestamp
                        self.deliver(received_message, received_vector_clock, sender_id)
       
        #check if incoming multicast is a negative acknowledgement
        if received_message_type == "NACK":
            if sender_id != self.id:
                print("received nack message")
                try:
                    self.lock.acquire()
                    if received_vector_clock[self.id] < self.vector_clock[self.id]:
                        #the requester is missing a message that has been sent
                        next_sequence_number = received_vector_clock[self.id] + 1
                        if next_sequence_number in self.message_history_buffer: 
                            print(f"Resending message with sequence number: {next_sequence_number}")
                            #resend next unreceived message
                            missed_message = self.message_history_buffer[next_sequence_number]
                            self.resend_missed_message(missed_message, "224.0.0.2", 7000)
                        else:
                            print(f"No message found with sequence number: {next_sequence_number}")
                except Exception as e:
                    print(f"Error while handling NACK: {e}")
                finally:
                    self.lock.release()
                    
        elif received_message_type == "normal":
            if sender_id == self.id:
                if received_vector_clock[self.id] not in self.displayed_own_message:
                    #Display message to the standard output
                    print(f"Delivered message: '{received_message}' with vector clock: {received_vector_clock} from {sender_id}")
                    self.displayed_own_message.add(received_vector_clock[self.id])
                    print(f"displaed my message list: {self.displayed_own_message}")
                else:
                    print(f"Already displayed my own message with identifier: {received_vector_clock[self.id]}")
            
            else:
    
                self.lock.acquire()
                if self.can_deliver(received_vector_clock, sender_id):
                    self.deliver(received_message, received_vector_clock, sender_id)
                    # Check the hold-back queue for any message that can now be delivered
                    self.check_hold_back_queue()
                else:
                    #first check hold back queue for potentially deliverable messages
                    self.check_hold_back_queue()
                    #add it to the hold-back queue
                    self.hold_back_queue.append({
                        'content': received_message,
                        'vector_clock': received_vector_clock,
                        'sender_id': sender_id,
                        'type': received_message_type
                    }) 
                self.lock.release()

    def deliver(self, message, received_vector_clock, sender_id):
        #Increament the appropriate element of the vector clock
        self.vector_clock[sender_id] += 1
        #Display message to the standard output
        print(f"Delivered message: '{message}' with vector clock: {received_vector_clock} from {sender_id}")   
        
    def resend_missed_message(self, message, multicast_group, port):
        #Function to resend a missed messsage
        try:
            multicast_send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            ttl = struct.pack('b', 1)
            multicast_send_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
            multicast_send_socket.sendto(str.encode(message), (multicast_group, port))
            print("Missed message resent.")
        except Exception as e:
            print(e)
        finally:
            multicast_send_socket.close()
            
    def can_deliver(self, received_vector_clock, sender_id):
        # Check the condition for delivery
        #self.lock.acquire()  # Ensure mutual exclusion when accessing shared state
        try:
            # Check if the message is from the sender and is the next expected message
            if received_vector_clock[sender_id] == self.vector_clock[sender_id] + 1:
                # It's the next expected message, we can potentially deliver this
                for peer, timestamp in received_vector_clock.items():
                    if peer != sender_id:
                        if timestamp > self.vector_clock[peer]:
                            # There is a message from some other peer that we have not processed yet
                            return False
                # If we reach here, the message satisfies causal delivery conditions
                return True
            elif received_vector_clock[sender_id] <= self.vector_clock[sender_id]:
                # It's an old or duplicate message, discard
                return False
            else:
                # There's a gap, so we're missing some messages from this sender
                if sender_id != self.id:  # Don't NACK our own messages
                    self.send_multicast('', "NACK", "224.0.0.2", 7000)
                return False
        except:
            pass
        
    def check_hold_back_queue(self):
        #check for message in the hold-back queue that can now be delivered
        for message in self.hold_back_queue:
            if self.can_deliver(message['vector_clock'], message['sender_id']):
                self.deliver(message['content'], message['vector_clock'], message['sender_id'])
                self.hold_back_queue.remove(message)
   
                
 ########### END : MULTICAST METHODS ############
            

########### START : SERVER (LEADER) METHODS ############

    def send_discovery_broadcast_messages(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as broadcast_sock:
            broadcast_sock.setsockopt(
                socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            message = PeerDiscoveryProtocol.encode_register(
                self.name, self.id, self.ip, self.registeration_port,self.heartbeat_port, self.message_port, self.multicast_address)

            while True:
                if(self.demand_election):
                    broadcast_sock.close()
                    time.sleep(2)  # Wait for the socket to close
                    return
                broadcast_sock.sendto(
                    message, (self.broadcast_ip, self.broadcast_port))
                time.sleep(2)
                print("Server broadcasting on port:", self.broadcast_port)
                
    def check_alive_leader(self):
        # Set up a socket for receiving broadcast messages
        start_time = time.time()  # Record the start time
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_sock:
            client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            client_sock.bind(('0.0.0.0', self.broadcast_port))
            client_sock.settimeout(10)
            while time.time() - start_time < 10:  # Run for 5 seconds
                if(self.demand_election):
                    client_sock.close()
                    time.sleep(2)  # Wait for the socket to close
                    return
                try:
                    data, _ = client_sock.recvfrom(1024)
                    decoded_msg = PeerDiscoveryProtocol.decode_message(data)
                    if (decoded_msg['action'] == 'register' and decoded_msg['id'] != self.id):
                        print(
                            f"Existing Alive Leader: { decoded_msg['name'] }")
                        self.demand_election = True
                        client_sock.close()
                        time.sleep(2)  # Wait for the socket to close
                        return

                except socket.timeout:
                    print("Socket Timeout check_existing_leader")
                    print("I am the Leader")
                    #Multicast Send Thread Start
                    multicast_send_thread = threading.Thread(target=self.test_multicast)
                    #Multicast Receive Thread Start
                    multicast_receive_thread = threading.Thread(target=self.listen_for_multicast, args = ("0.0.0.0",self.server_heartbeat_port, self.multicast_group))
                    multicast_send_thread.start()
                    multicast_receive_thread.start()
                    client_sock.close()
                    time.sleep(2)  # Wait for the socket to close
                    return
                
                except ConnectionResetError as e:
                    print("I am the Leader")
                    client_sock.close()
                    #Multicast Send Thread Start
                    multicast_send_thread = threading.Thread(target=self.test_multicast)
                    #Multicast Receive Thread Start
                    multicast_receive_thread = threading.Thread(target=self.listen_for_multicast, args = ("0.0.0.0",self.server_heartbeat_port, self.multicast_group))
        
                    multicast_send_thread.start()
                    multicast_receive_thread.start()
                    time.sleep(2)  # Wait for the socket to close
                    return
            print("I am the Leader")
            #Multicast Send Thread Start
            multicast_send_thread = threading.Thread(target=self.test_multicast)
            #Multicast Receive Thread Start
            multicast_receive_thread = threading.Thread(target=self.listen_for_multicast, args = ("0.0.0.0",self.server_heartbeat_port, self.multicast_group))
            multicast_send_thread.start()
            multicast_receive_thread.start()
            client_sock.close()
            time.sleep(2)  # Wait for the socket to close

    def handle_registration_requests(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as registration_sock:
            registration_sock.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            registration_sock.bind((self.ip, self.registeration_port))

            registration_sock.settimeout(10) 
            while True:
                if(self.demand_election):
                    registration_sock.close()
                    time.sleep(2)  # Wait for the socket to close
                    return
                try:
                    data, _ = registration_sock.recvfrom(1024)
                    decoded_msg = PeerDiscoveryProtocol.decode_message(data)
                    if decoded_msg['action'] == 'yes':
                        # Check if 'id' already exists in the list
                        id_exists = False
                        for participant in self.active_peers:
                            if participant['id'] == decoded_msg['id']:
                                # If 'id' already exists, set flag and break out of the loop
                                id_exists = True
                                participant['status'] = 'alive'
                                break
                        # If 'id' already exists, skip to next iteration
                        if not id_exists:
                            self.active_peers.append({'name': decoded_msg['name'], 'status': 'registered', 'ip': decoded_msg['ip'],'id': decoded_msg['id'],
                                                 'registeration_port': decoded_msg['registeration_port'],'heartbeat_port': decoded_msg['heartbeat_port'], 'message_port': decoded_msg['message_port']})
                        registration_sock.sendto(PeerDiscoveryProtocol.encode_register_confirmation(
                        ), (decoded_msg['ip'],  decoded_msg['registeration_port']))
                        print(
                            f"Registered peer: {decoded_msg['name']} : {decoded_msg['ip']} :{decoded_msg['registeration_port']}")
                        time.sleep(2)              
                except socket.timeout:
                    print("Server timed out waiting for registration requests")
                except ConnectionResetError as e:
                     print("ConnectionResetError in handle_registeration_requests:", e)
                     # Handle the error or perform cleanup actions
                     # # Close the socket to release system resources
                     registration_sock.close()
                     time.sleep(2)  # Wait for the socket to close
                     return
                    

    def run_server(self):
        print("Peer is First Node , Acting as a Server(Leader)")
        self.client_registeration_flag=True
        self.server_heartbeat_port = self.heartbeat_port
        self.multicast_group =self.multicast_address
        broadcast_thread = threading.Thread(
            target=self.send_discovery_broadcast_messages)
        registration_thread = threading.Thread(
            target=self.handle_registration_requests)
        election_result_thread= threading.Thread(
            target=self.handle_voting_requests)
        leader_check_thread = threading.Thread(
            target=self.check_alive_leader)    #sets self.demand_election if existing leader is found
        
        
        leader_check_thread.start()
        broadcast_thread.start()
        registration_thread.start()
        election_result_thread.start()

        #Mulicast Send Thread End
        #multicast_send_thread.join()
        #Multicast Receive Thread End
        #multicast_receive_thread.join()
        broadcast_thread.join() #Never ending
        leader_check_thread.join()
        registration_thread.join()
        if(self.demand_election):
            self.peer_process()

        #election_result_thread.join()

  ########### END : SERVER (LEADER) METHODS ############

 
 ########### START : CLIENT METHODS ############

    def send_registration_request(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as registration_sock_:
            registration_sock_.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            registration_sock_.bind((self.ip, self.registeration_port))
            registration_sock_.settimeout(5)
            while True :
                # client_sock.settimeout(5)
                if(self.demand_election):
                    registration_sock_.close()
                    time.sleep(2)  # Wait for the socket to close
                    return
                try:
                    registration_sock_.sendto(PeerDiscoveryProtocol.encode_register_reply(self.name,self.id, self.ip, self.registeration_port,self.heartbeat_port, self.message_port),
                                              (self.server_ip,  self.server_registeration_port))
                    data, _ = registration_sock_.recvfrom(1024)
                    decoded_msg = PeerDiscoveryProtocol.decode_message(data)
                    if( decoded_msg['action']=='registered'):
                        print(
                            f"Received confirmation from server {self.server_ip} : { decoded_msg['action'] }")
                        if(not self.client_registeration_flag):
                            #Multicast Send Thread Start
                            multicast_send_thread = threading.Thread(target=self.test_multicast)
                            #Multicast Receive Thread Start
                            #multicast_receive_thread = threading.Thread(target=self.listen_for_multicast, args = ("0.0.0.0", 7000, "224.0.0.2"))
                            multicast_receive_thread = threading.Thread(target=self.listen_for_multicast, args = ("0.0.0.0", self.server_heartbeat_port, self.multicast_group))
                                    
                            multicast_send_thread.start()
                            multicast_receive_thread.start()
                            #Mulicast Send Thread End
                            #multicast_send_thread.join()
                            #Multicast Receive Thread End
                            #multicast_receive_thread.join()
                        self.client_registeration_flag = True
                        
                    time.sleep(2)
                        
                except socket.timeout:
                    print("Client timed out waiting for Server Registeration Confirmation, Leader Dead ")
                    # Wait for the thread to finish
                    print(self.name, ": Finishing Existing Client Registeration")
                    self.demand_election = True
                    registration_sock_.close()
                    time.sleep(2)  # Wait for the socket to close
                    return
                    #Start election
                except ConnectionResetError as e:
                    print("ConnectionResetError in send_registeration_requests:", e)
                    # Handle the error or perform cleanup actions
                    # # Close the socket to release system resources
                    print("Leader Dead")
                    # Wait for the thread to finish
                    print(self.name, ": Finishing Existing Client Registeration")
                    self.demand_election = True
                    registration_sock_.close()
                    time.sleep(2)  # Wait for the socket to close
                    return
            #registration_sock_.close()

    def send_registration_thread(self):
        registration_thread = threading.Thread(
            target=self.send_registration_request)
        registration_thread.start()
        registration_thread.join() #Regiteration thread finished due to leader dead timeout

    def receive_discovery_broadcast_messages(self):
        # Set up a socket for receiving broadcast messages
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_sock:
            client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            client_sock.bind(('0.0.0.0', self.broadcast_port))

            print("Client listening for server broadcast ")          
            client_sock.settimeout(5)
            while True:
 
                if(self.demand_election):
                    client_sock.close()
                    time.sleep(2)  # Wait for the socket to close
                    return
                try:
                    data, _ = client_sock.recvfrom(1024)
                    decoded_msg = PeerDiscoveryProtocol.decode_message(data)

                    if (decoded_msg['action'] == 'register' and decoded_msg['id'] != self.id):
                        print(
                            f"Received registration broadcast message from server { decoded_msg['name'] }")
                        self.server_ip = decoded_msg['ip']
                        self.server_registeration_port = decoded_msg['registeration_port']
                        self.server_heartbeat_port = decoded_msg['heartbeat_port']
                        self.multicast_group = decoded_msg['multicast_address']
                        # Extract IP and port from server_address
                        self.server_message_port = decoded_msg['message_port']
                        #self.send_registration_request()
                        self.send_registration_thread()

                except socket.timeout:
                    print("Client timed out waiting for Leader broadcast messages")
                    print("Leader Dead ")
                    # Wait for the thread to finish
                    print(self.name, ": Finishing Existing Client Registeration")
                    self.demand_election = True
                    client_sock.close()
                    time.sleep(2)  # Wait for the socket to close
                    return
                
                except ConnectionResetError as e:
                    print("ConnectionResetError in  receive_discovery_broadcast_messages:", e)
                    print("Leader Dead ")
                    # Wait for the thread to finish
                    print(self.name, ": Finishing Existing Client Registeration")
                    self.demand_election = True
                    client_sock.close()
                    time.sleep(2)  # Wait for the socket to close
                    return

    def run_client(self):
        print("Peer is Acting as client")
        time.sleep(1)  # Wait for the server to start

        broadcast_thread = threading.Thread(
            target=self.receive_discovery_broadcast_messages)
        election_result_thread= threading.Thread(
            target=self.handle_voting_requests)
        
        #Multicast Send Thread Start
        #multicast_send_thread = threading.Thread(target=self.test_multicast)
        #Multicast Receive Thread Start
        #multicast_receive_thread = threading.Thread(target=self.listen_for_multicast, args = ("0.0.0.0", 7000, "224.0.0.2"))
        #multicast_receive_thread = threading.Thread(target=self.listen_for_multicast, args = ("0.0.0.0", self.server_heartbeat_port, self.multicast_group))

        election_result_thread.start()

        broadcast_thread.start()
        
        #multicast_send_thread.start()
        #multicast_receive_thread.start()

        broadcast_thread.join()
        election_result_thread.join()
        #Mulicast Send Thread End
        #multicast_send_thread.join()
        #Multicast Receive Thread End
        #multicast_receive_thread.join()
       
        if(self.demand_election):
             self.peer_process()
            

    ########### END : CLIENT METHODS ############


if __name__ == "__main__":
    process = ServerClientProcess()
    process.start()
    process.join()
