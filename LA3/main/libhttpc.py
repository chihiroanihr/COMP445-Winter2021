import json
import socket
import ipaddress
from urllib.parse import urlparse
from packet import Packet
from utils.shell_output import shell_boxing
from utils.global_config import (
    CONN_TIMEOUT,
    OUTPUTS_DIR,
    DEFAULT_USER_AGENT,
    DEFAULT_ROUTER_HOST,
    DEFAULT_ROUTER_PORT,
    DEFAULT_SERVER_HOST,
    DEFAULT_SERVER_PORT,
    RequestMethod,
    PacketType,
    PacketStatus
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
                 request_url,
                 request_header='',
                 post_inline_data='',
                 post_input_file='',
                 verbose=False,
                 output_file='',
                 router_host=DEFAULT_ROUTER_HOST,
                 router_port=DEFAULT_ROUTER_PORT,
                 server_host=DEFAULT_SERVER_HOST,
                 server_port=DEFAULT_SERVER_PORT
                 ):
        self.request_method = None  # To initialize request method: GET / POST
        self.parsed_url = urlparse(request_url)  # Parse URL
        self.hostname = self.parsed_url.hostname
        self.path = self.parsed_url.path if self.parsed_url.path else '/'
        self.query = self.parsed_url.query  # in string
        self.request_header = request_header  # in dict {'key':'val'}
        self.verbose = verbose
        self.post_inline_data = post_inline_data  # in json
        self.post_input_file = post_input_file  # in json
        self.output_file = output_file
        # router and server host/port config
        self.router_host = router_host
        self.router_port = router_port
        self.server_host = server_host
        self.server_port = server_port
        # peer address = receiver's address (server) for sending packet
        self.peer_ip_addr = ipaddress.ip_address(
            socket.gethostbyname(self.server_host))
        self.packet_status = None

        #self.scheme = self.parsed_url.scheme
        #self.netloc = self.parsed_url.netloc
        #self.params = self.parsed_url.params
        #self.fragment = self.parsed_url.fragment


    def request(self, request_method):
        # Request-URI = [ path ][ "?" query ]
        request_uri = f"{self.path}?{self.query}" if self.query else self.path
        # Request-Line = Method SP Request-URI SP HTTP-Version CRLF
        request_line = f"GET {request_uri} HTTP/1.0\r\n"
        # Request-Heaer = Headers CRLF User-Agent CRLF
        request_headers = self.create_request_headers()

        # if get method, then send only header message
        if request_method == RequestMethod.GET:
            send_payload = f"{request_line}{request_headers}\r\n"

        # if post method, then send both header and body
        if request_method == RequestMethod.POST:
            # Request-Body
            request_body = self.create_request_body()
            send_payload = f"{request_line}{request_headers}\r\n{request_body}\r\n"

        self.run_client(send_payload)


    def run_client(self, send_payload):
        # open and set up client socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # try to receive a response within timeout
        client_socket.settimeout(CONN_TIMEOUT)

        #TODO: Three-way-handshake
        '''three_way_handshake(peer_ip, server_port, router_addr, router_port, conn)'''
        handshake = True

        try:
            # construct packet
            print(">>> Constructing packet" if self.verbose else '')
            send_packet = Packet(
                packet_type=PacketType.DATA,
                seq_num=1,
                peer_ip_addr=self.peer_ip_addr,
                peer_port=self.server_port,
                # convert request message payload to byte code
                payload=send_payload.encode("utf-8")
            )
            self.packet_status = PacketStatus.CREATED
            print(">>> Packet created." if self.verbose else '')

            # convert from host-byte to network-byte(big-endian order) before sending packet
            send_byte_packet = send_packet.to_bytes()

            # output packet to be sent
            self.output_packet(send_packet, send_byte_packet, send_payload)

            # send packet to router
            print(">>> Send packet to server via router")
            client_socket.sendto(
                send_byte_packet, (self.router_host, self.router_port)
            )
            print(">>> Successfully sent." if self.verbose else '')

            # receive response packet from router
            print("\n.....waiting for a response.....\n")
            receive_byte_packet, sender_addr = client_socket.recvfrom(1024)
            self.packet_status = PacketStatus.RECEIVED
            print(
                ">>> Successfully received a response from server via router."
                if self.verbose else ''
                )

            # Convert from network-byte(big-endian order) to host-byte after receiving packet
            receive_packet = Packet.from_bytes(receive_byte_packet)

            # Extracts/decode response message payload
            receive_payload = receive_packet.payload.decode("utf-8")

            # output packet received
            self.output_packet(
                receive_packet, receive_byte_packet, receive_payload, sender_addr
            )

        except socket.timeout:
            print(f">>> No response after {CONN_TIMEOUT}s")

        finally:
            # close the connection
            client_socket.close()


    def output_packet(self, packet, byte_packet, payload, sender_addr=''):
        if self.verbose:
            packet_total_size = len(byte_packet)
            header_size = len(byte_packet)-len(payload)
            body_size = len(payload)

            # console output for sending packet data
            if self.packet_status == PacketStatus.CREATED:
                print(f"Packet: {packet}")
                print(f"Packet total size: {packet_total_size}" + \
                      f"(header size={header_size}, body size={body_size})"
                    )
                print(f"Payload: \n{shell_boxing(payload)}")

            # console output for response packet data
            elif self.packet_status == PacketStatus.RECEIVED:
                # Divide response message into header (if verbose) and body
                payload_header = payload[:payload.find('\r\n\r\n')]
                payload_body = payload[payload.find('\r\n\r\n'):]

                # Output response
                print('Router: ', sender_addr)
                print('Packet: ', packet)
                print(f"Packet total size: {packet_total_size} " + \
                      f"(header size={header_size}, body size={body_size})"
                    )
                print('Payload: ')
                output_str = ''
                if self.verbose:
                    output_str += payload_header
                if self.output_file:
                    self.output_to_file(payload_body)
                    print("The response message payload received was recorded in " + \
                          f"{self.output_file}"
                        )
                else:
                    output_str += '\r\n' + payload_body
                print(shell_boxing(output_str))
        else:
            return


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


    def create_request_headers(self):
        # add host entry to the headers dict
        if not self.request_header:
            self.request_header = dict()
        self.request_header['Host'] = self.hostname

        # if User-Agent header does not exist (user did not specified in httpc command line with -h)
        if 'User-Agent' not in self.request_header:
            # then append default user-agent
            self.request_header['User-Agent'] = DEFAULT_USER_AGENT

        ''' self.headers['Connection'] = 'closed' '''

        request_header_str = ''
        for key, val in self.request_header.items():
            request_header_str += f"{key}:{val}\r\n"
        return request_header_str


    def create_request_body(self):
        body = ''
        if self.post_input_file:
            with open(self.post_input_file, encoding='utf-8') as json_file:
                json_data = json.load(json_file)
                body = json.dumps(json_data)
        if self.post_inline_data:
            body = str(self.post_inline_data)
        if 'Content-Length' in self.request_header:
            index = int(self.request_header['Content-Length'])
            body = body[:index]
        return body



if __name__ == "__main__":
    print("========= 1st Request =========")
    URL = 'http://httpbin.org/status/418'
    request = HttpcRequests(URL)
    request.request(RequestMethod.GET)

    print("========= 2nd Request =========")
    URL = 'http://httpbin.org/status/418'
    headers = {'key': 'value'}
    request = HttpcRequests(URL, request_header=headers)
    request.request(RequestMethod.GET)

    print("========= 3rd Request =========")
    request = HttpcRequests(URL, request_header=headers, verbose=True)
    request.request(RequestMethod.GET)

    print("========= 4th Request =========")
    URL = 'http://httpbin.org/get?course=networking&assignment=1'
    headers = {'key1': 'value1'}
    request = HttpcRequests(URL, request_header=headers)
    request.request(RequestMethod.GET)

    print("========= 5th Request =========")
    URL = 'http://httpbin.org/post'
    data = {'Assignment': 1}
    headers = {"Content-Type": "application/json"}
    request = HttpcRequests(URL, request_header=headers, post_inline_data=data)
    request.request(RequestMethod.POST)

    print("========= 6th Request =========")
    URL = 'http://httpbin.org/post'
    headers = {"Content-Type": "application/json"}
    request = HttpcRequests(
        request_url=URL,
        request_header=headers,
        post_input_file='/inputs/file1.json'
    )
    request.request(RequestMethod.POST)

    print("========= 7th Request =========")
    URL = 'http://httpbin.org/post'
    headers = {"Content-Type": "application/json"}
    request = HttpcRequests(
        request_url=URL,
        request_header=headers,
        post_input_file='file1.json',
        output_file='/outputs/result.txt'
    )
    request.request(RequestMethod.POST)
