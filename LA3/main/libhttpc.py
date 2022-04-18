import json
import socket
import ipaddress
from urllib.parse import urlparse
from packet import Packet
from utils.shell_output import shell_boxing
from utils.global_config import (
    CONN_TIMEOUT,
    INPUTS_DIR,
    OUTPUTS_DIR,
    DEFAULT_USER_AGENT,
    DEFAULT_ROUTER_HOST,
    DEFAULT_ROUTER_PORT,
    DEFAULT_SERVER_HOST,
    DEFAULT_SERVER_PORT,
    RequestMethod,
    PacketType,
    PacketStatus,
    MAX_PAYLOAD_SIZE,
    MAX_SEQ_NUM,
    MAX_WINDOW_SIZE
)

# 3. HTTP client receives response message containing html file, displays html.
#   --> Parses html file, finds more objects --> REQUEST AGAIN

'''
IMPORTANT:
in this assignment, we assume that payload includes both header and body,
since it has to follow the message structure provided in LA3 pdf.

1 char = 1 byte
'''


class HttpcRequests:
    def __init__(self,
                 # router and server host/port
                 router_host=DEFAULT_ROUTER_HOST,
                 router_port=DEFAULT_ROUTER_PORT,
                 server_host=DEFAULT_SERVER_HOST,
                 server_port=DEFAULT_SERVER_PORT
                 ):
        # router and server host/port config
        self.router_host = router_host
        self.router_port = router_port
        self.server_host = server_host
        self.server_port = server_port
        # peer address = receiver's address (server) for sending packet
        self.peer_ip_addr = ipaddress.ip_address(
            socket.gethostbyname(self.server_host)
        )
        # additional attributes
        self.packet_status = None
        self.request_method = None
        self.verbose = None
        self.output_file = None
        self.hostName = None
        self.send_payload = None

        self.buffer_is_full = False

    def open_socket(self):
        # open and set up client socket
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # try to receive a response within timeout
        self.client_socket.settimeout(CONN_TIMEOUT)

        if self.verbose:
            print(">>> Client socket set up completed.")

    def create_request(self,
                       request_method,
                       request_url,
                       request_header='',
                       post_inline_data='',
                       post_input_file='',
                       verbose=False,
                       output_file='',):
        self.request_method = request_method  # To initialize request method: GET / POST
        self.verbose = verbose

        self.output_file = output_file
        parsed_url = urlparse(request_url)  # Parse URL
        url_path = parsed_url.path if parsed_url.path else '/'
        url_query = parsed_url.query  # in string
        self.hostname = parsed_url.hostname

        if self.verbose:
            print(">>> Creating request payload message")

        # Request-URI = [ url_path ][ "?" url_query ]
        request_uri = f"{url_path}?{url_query}" if url_query else url_path
        # Request-Heaer = Headers CRLF User-Agent CRLF
        request_header = self.create_request_header(request_header)

        # if get method, then send only header message
        if self.request_method == RequestMethod.GET:
            # Request-Line = Method Request-URI HTTP-Version CRLF
            request_line = f"GET {request_uri} HTTP/1.0\r\n"
            self.send_payload = f"{request_line}{request_header}\r\n"

        # if post method, then send both header and body
        if self.request_method == RequestMethod.POST:
            # Request-Line = Method Request-URI HTTP-Version CRLF
            request_line = f"POST {request_uri} HTTP/1.0\r\n"
            # Request-Body
            request_body = self.create_request_body(
                request_header, post_inline_data, post_input_file
            )  # in json
            self.send_payload = f"{request_line}{request_header}\r\n{request_body}\r\n"

        if self.verbose:
            print(">>> Request payload message Created.")

    # run client

    def send_request(self):
        #TODO: Three-way-handshake
        '''three_way_handshake(peer_ip, server_port, router_addr, router_port, conn)'''
        handshake = True

        # construct packet
        if self.verbose:
            print(">>> Constructing packet(s) to send")
        send_packets = self.generate_packets()
        self.packet_status = PacketStatus.CREATED
        if self.verbose:
            print(">>> Packet(s) created.")
            print()

        # send packets tp router via selective repeat protocol
        seq_start = 0  # sequence number of first frame in window
        num_buffer_acked = 0
        window_buffers = []  # array of max window size
        num_frame_available = MAX_WINDOW_SIZE
        
        if self.verbose:
            print(">>> Send data packet(s) to server via router")
            print(f">>> There are total of {len(send_packets)} packets to be sent")

        while True:
            # if no more packets left then stop sending
            if not send_packets:
                break
            
            window_buffers.extend(send_packets[:num_frame_available])
            send_packets = send_packets[num_frame_available:]
            num_frame_available = 0

            for packet in window_buffers[num_buffer_acked:]:
                try:
                    if packet.packet_type == PacketType.DATA:

                        # output packet to be sent
                        self.output_packet(packet)

                        # convert from host-byte to network-byte(big-endian order) before sending packet
                        byte_packet = packet.to_bytes()

                        # send packet to router
                        self.client_socket.sendto(
                            byte_packet, (self.router_host, self.router_port)
                        )
                        print(">>> Successfully sent.")

                        print("\n.....waiting for a response.....\n")

                        # receive response packet from router
                        receive_byte_packet, sender_addr = self.client_socket.recvfrom(
                            1024)
                        self.packet_status = PacketStatus.RECEIVED
                        print(
                            ">>> Successfully received a response from server via router.")

                        # Convert from network-byte(big-endian order) to host-byte after receiving packet
                        receive_packet = Packet.from_bytes(receive_byte_packet)

                        packet_type = receive_packet.packet_type
                        seq_num = receive_packet.seq_num

                        if packet_type == PacketType.ACK and seq_num == seq_start:
                            print(">>> ACK Received, window moved.")
                            # output packet received
                            self.output_packet(receive_packet, sender_addr)

                            num_buffer_acked += 1
                            num_frame_available += 1
                            if seq_num == MAX_SEQ_NUM:
                                seq_start = 0
                            else:
                                seq_start = seq_num + 1

                        elif packet_type == PacketType.ACK and seq_num != seq_start:
                            print(">>> ACK Received, yet previous packet(s) have pending ACKs.")
                            window_buffers[seq_num] = receive_packet

                    elif packet.packet_type == PacketType.ACK:
                        print(">>> This is an already ACKed packet. window moved.")
                        packet_type = packet.packet_type
                        seq_num = packet.seq_num

                        if seq_num == seq_start:
                            # output packet received
                            self.output_packet(packet, sender_addr)

                            num_buffer_acked += 1
                            num_frame_available += 1
                            if seq_num == MAX_SEQ_NUM:
                                seq_start = 0
                            else:
                                seq_start = seq_num + 1

                except socket.timeout:
                    print(f">>> No response after {CONN_TIMEOUT}s")
                    print()

        # close the connection
        self.client_socket.close()

    def generate_packets(self):
        sequence_num = 0
        send_packets = []
        payload = self.send_payload
        i = 0
        while True:
            # if no more payload then stop creating packets
            if not payload:
                break
            sequence_num = i % MAX_SEQ_NUM
            packet = Packet(
                packet_type=PacketType.DATA,
                seq_num=sequence_num,
                peer_ip_addr=self.peer_ip_addr,
                peer_port=self.server_port,
                # convert request message payload to byte code
                payload=payload[:MAX_PAYLOAD_SIZE].encode("utf-8")
            )

            # append to list of packets
            send_packets.append(packet)

            # if payload has more than maximum payload size, loop again to make another packet
            payload = payload[MAX_PAYLOAD_SIZE:]

            i += 1

        return send_packets

    def output_packet(self, packet, sender_addr=''):
        # Extracts/decode response message payload
        payload = packet.payload.decode("utf-8")

        byte_packet = packet.to_bytes()
        packet_total_size = len(byte_packet)
        header_size = len(byte_packet)-len(payload)
        body_size = len(payload)

        # console output for sending packet data
        if self.packet_status == PacketStatus.CREATED and self.verbose:
            print(f"Packet: {packet}")
            print(f"Packet total size: {packet_total_size}" +
                  f"(header size={header_size}, body size={body_size})"
                  )
            print(f"Payload: \n{shell_boxing(payload)}")

        # console output for response packet data
        elif self.packet_status == PacketStatus.RECEIVED:
            # Divide response message into header (if verbose) and body
            payload_header = payload[:payload.find('\r\n\r\n')]
            payload_body = payload[payload.find('\r\n\r\n'):]

            # Output response
            output_str = ''
            output_str += f"Router: {sender_addr}\n" + \
                f"Packet: {packet}\n" + \
                f"Packet total size: {packet_total_size}\n" + \
                f"(header size={header_size}, body size={body_size})\n" \
                if self.verbose else ''

            if self.request_method == RequestMethod.GET:
                output_str += "Payload: \n"
                if self.output_file:
                    output_str += f"{shell_boxing(payload_header) if self.verbose else ''}" + \
                        f"\nThe response message payload received was recorded in {self.output_file}"
                else:
                    output_str += f"{shell_boxing(payload_header+payload_body)}" if self.verbose \
                        else f"{shell_boxing(payload_body) if payload_body.strip() else ''}"

            if self.request_method == RequestMethod.POST:
                output_str += ">>> Post request message/payload was successfully stored."

            print(output_str)

    def output_to_file(self, body):
        self.output_file = OUTPUTS_DIR + self.output_file
        try:
            file = open(self.output_file, "w", encoding='utf-8')
            file.write(body)
        except OSError:
            print("!!! Could not output the response to file.")
            print(shell_boxing(body))
        finally:
            file.close()

    def create_request_header(self, request_header):
        # add host entry to the headers dict
        if not request_header:
            request_header = dict()
        request_header['Host'] = self.hostname

        # if User-Agent header does not exist (user did not specified in httpc command line with -h)
        if 'User-Agent' not in request_header:
            # then append default user-agent
            request_header['User-Agent'] = DEFAULT_USER_AGENT

        ''' self.headers['Connection'] = 'closed' '''

        request_header_str = ''
        for key, val in request_header.items():
            request_header_str += f"{key}:{val}\r\n"
        return request_header_str

    def create_request_body(self, request_header, post_inline_data, post_input_file):
        body = ''
        if post_input_file:
            post_input_file = INPUTS_DIR + post_input_file
            if post_input_file.endswith('.json'):
                with open(post_input_file, encoding='utf-8') as json_file:
                    json_data = json.load(json_file)
                    body = json.dumps(json_data)
            else:
                file = open(post_input_file, mode='r', encoding='utf-8')
                body = file.read()
                    
        if post_inline_data:
            body = str(post_inline_data)
        if 'Content-Length' in request_header:
            index = int(request_header['Content-Length'])
            body = body[:index]
        return body


if __name__ == "__main__":
    # print("========= 1st Request =========")
    # URL = 'http://httpbin.org/status/418'
    # request = HttpcRequests()
    # request.open_socket()
    # request.create_request(request_method=RequestMethod.GET, request_url=URL)
    # request.send_request()
    # print()

    # print("========= 2nd Request =========")
    # URL = 'http://httpbin.org/status/418'
    # headers = {'key': 'value'}
    # request = HttpcRequests()
    # request.open_socket()
    # request.create_request(request_method=RequestMethod.GET,
    #                        request_url=URL, request_header=headers)
    # request.send_request()
    # print()

    # print("========= 3rd Request =========")
    # request = HttpcRequests()
    # request.open_socket()
    # request.create_request(request_method=RequestMethod.GET,
    #                        request_url=URL, request_header=headers, verbose=True)
    # request.send_request()
    # print()

    # print("========= 4th Request =========")
    # URL = 'http://httpbin.org/get?course=networking&assignment=1'
    # request = HttpcRequests()
    # request.open_socket()
    # request.create_request(request_method=RequestMethod.GET,
    #                        request_url=URL, request_header=headers, verbose=True)
    # request.send_request()
    # print()

    # print("========= 5th Request =========")
    # URL = 'http://httpbin.org/post'
    # data = {'Assignment': 1}
    # headers = {"Content-Type": "application/json"}
    # request = HttpcRequests()
    # request.open_socket()
    # request.create_request(request_method=RequestMethod.POST, request_url=URL,
    #                        request_header=headers, post_inline_data=data, verbose=True)
    # request.send_request()
    # print()

    # print("========= 6th Request =========")
    # URL = 'http://httpbin.org/post'
    # headers = {"Content-Type": "application/json"}
    # request = HttpcRequests()
    # request.open_socket()
    # request.create_request(
    #     request_method=RequestMethod.POST,
    #     request_url=URL,
    #     request_header=headers,
    #     post_input_file='file1.json',
    #     verbose=True
    # )
    # request.send_request()
    # print()

    # print("========= 7th Request =========")
    # URL = 'http://httpbin.org/post'
    # headers = {"Content-Type": "application/json"}
    # request = HttpcRequests()
    # request.open_socket()
    # request.create_request(
    #     request_method=RequestMethod.POST,
    #     request_url=URL,
    #     request_header=headers,
    #     output_file='result.txt',
    #     verbose=True
    # )
    # request.send_request()
    # print()

    print("========= 8th Request =========")
    URL = 'http://httpbin.org/post'
    headers = {"Content-Type": "application/json"}
    request = HttpcRequests()
    request.open_socket()
    request.create_request(
        request_method=RequestMethod.POST,
        request_url=URL,
        request_header=headers,
        post_input_file='simple-html.html',
        verbose=True
    )
    request.send_request()
    print()
