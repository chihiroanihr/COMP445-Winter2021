import socket
from urllib.parse import urlparse
import json
from packet import Packet
import ipaddress

# 1. HTTP client initiates TCP connection to HTTP server (process) at {link} on port {num}
# 1s. HTTP server at host {link} waiting for TCP connection at port {num}
#   --> Accepts connection, notifying client

# 2. HTTP client sends HTTP request message containing URL into TCP connection socket
#   (Up to here is TCP handshake)
# 2s. HTTP server receives request message, forms response message containing requested object,
#   and sends message into its socket
# 3s. HTTP server closes TCP connection
# 3. HTTP client receives response message containing html file, displays html.
#   --> Parses html file, finds more objects --> REQUEST AGAIN

OUTPUTS_DIR = './outputs/'
DEFAULT_USER_AGENT = 'Concordia-HTTP/1.0'

DEFAULT_ROUTER_HOST = 'localhost'
DEFAULT_ROUTER_PORT = 3010
DEFAULT_SERVER_HOST = 'localhost'
DEFAULT_SERVER_PORT = 8010

TIMEOUT = 5

class HttpcRequests:

    def __init__(self,
                 url,
                 headers='',
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
        self.request_message = ''   # To send full request lines to the host
        self.parsed_url = urlparse(url)  # Parse URL
        self.hostname = self.parsed_url.hostname
        self.path = self.parsed_url.path if self.parsed_url.path else '/'
        self.query = self.parsed_url.query  # in string
        self.headers = headers  # in dict {'key':'val'}
        self.verbose = verbose
        self.post_inline_data = post_inline_data  # in json
        self.post_input_file = post_input_file  # in json
        self.body = ''
        self.output_file = output_file
        # router and server host/port config
        self.router_host = router_host
        self.router_port = router_port
        self.server_host = server_host
        self.server_port = server_port

        #self.scheme = self.parsed_url.scheme
        #self.netloc = self.parsed_url.netloc
        #self.params = self.parsed_url.params
        #self.fragment = self.parsed_url.fragment

    def create_request_headers(self):
        # add host entry to the headers dict
        if not self.headers:
            self.headers = dict()
        self.headers['Host'] = self.hostname

        # if User-Agent header does not exist (user did not specified in httpc command line with -h)
        if 'User-Agent' not in self.headers:
            # then append default user-agent
            self.headers['User-Agent'] = DEFAULT_USER_AGENT

        ''' self.headers['Connection'] = 'closed' '''

        request_header_str = ''
        for key, val in self.headers.items():
            request_header_str += '{}:{}\r\n'.format(key, val)
        return request_header_str

    def create_request_body(self):
        if self.post_input_file:
            with open(self.post_input_file, encoding='utf-8') as json_file:
                json_data = json.load(json_file)
                self.body = json.dumps(json_data)
        if self.post_inline_data:
            self.body = str(self.post_inline_data)
        if 'Content-Length' in self.headers:
            index = int(self.headers['Content-Length'])
            self.body = self.body[:index]
        return self.body

    def output_to_file(self, response):
        self.output_file = OUTPUTS_DIR + self.output_file
        try:
            f = open(self.output_file, "w")
            f.write(response)
        except:
            print("!!! The error occured while outputting to file.")
            print(response)
        finally:
            f.close()

    def run_client(self):
        # peer address = receiver's address (server) for sending packet
        peer_ip_addr = ipaddress.ip_address(socket.gethostbyname(self.server_host))
        # open and set up client socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        try:
            #TODO: Three-way-handshake
            '''three_way_handshake(peer_ip, server_port, router_addr, router_port, conn)'''
            
            # construct packet
            print(">>> Constructing packet") if self.verbose else ''
            packet = Packet(
                packet_type = 0,
                seq_num = 1,
                peer_ip_addr = peer_ip_addr,
                peer_port = self.server_port,
                payload = self.request_message.encode("utf-8")
            )
            print(">>> Packet created.") if self.verbose else ''
            
            # convert from host-byte (big-endian order) to network-byte when sending packet
            packet = packet.to_bytes()
            
            # send request message to router
            print(">>> Send packet to server via router")
            print(">>> Packet payload: ", self.request_message) if self.verbose else ''
            client_socket.sendto(packet, (self.router_host, self.router_port))
            print(">>> Successfully sent.") if self.verbose else ''
            
            # try to receive a response within timeout
            client_socket.settimeout(TIMEOUT)
            print(">>> ...waiting for a response...")
            
            # receive response data from router
            response, sender_addr = client_socket.recvfrom(1024)
            print(">>> Successfully received a response from server via router.") if self.verbose else ''
            
            # Convert from network-byte (big-endian order) to host-byte when receiving packet
            packet = Packet.from_bytes(response)
            
            # Extracts response message payload
            payload = packet.payload.decode("utf-8")
            
            # Divide response message into header (if verbose) and body
            payload_header = payload[:payload.find('\r\n\r\n')].replace('\r\n\r\n', '')
            payload_body = payload[payload.find('\r\n\r\n'):].replace('\r\n\r\n', '')
            
            # Output response
            print('---> Router: ', sender_addr)
            print('---> Packet: ', packet)
            print('---> Payload: ')
            if self.verbose:
                print(payload_header)
                print()
            if self.output_file:
                self.output_to_file(payload_body)
                print("\t The response message payload from server is recorded in {}".format(self.output_file))
            else:
                print(payload_body)
                
        except socket.timeout:
            print('>>> No response after {}s'.format(TIMEOUT))
            
        finally:
            # close the connection
            client_socket.close()

    def GET(self):
        self.request_method = 'GET'

        # Request-URI = [ path ][ "?" query ]
        request_uri = "{}?{}".format(
            self.path, self.query) if self.query else self.path
        # Request-Line = Method SP Request-URI SP HTTP-Version CRLF
        request_line = "GET {} HTTP/1.0\r\n".format(request_uri)
        # Request-Heaer = Headers CRLF User-Agent CRLF
        request_headers = self.create_request_headers()
        self.request_message = "{}{}\r\n".format(request_line, request_headers)

        print("[Sent]")
        print(self.request_message)

        self.run_client()
        # return self.request_message

    def POST(self):
        self.request_method = 'POST'

        # Request-URI = [ path ][ "?" query ]
        request_uri = "{}?{}".format(
            self.path, self.query) if self.query else self.path
        # Request-Line = Method SP Request-URI SP HTTP-Version CRLF
        request_line = "POST {} HTTP/1.0\r\n".format(request_uri)
        # Request-Heaer = Headers CRLF User-Agent CRLF
        request_headers = self.create_request_headers()
        # Request-Body
        request_body = self.create_request_body()

        self.request_message = "{}{}\r\n{}\r\n".format(
            request_line, request_headers, request_body)

        print("[Sent]")
        print(self.request_message)

        self.run_client()
        # return self.request_message


if __name__ == "__main__":
    print("========= 1st Request =========")
    url = 'http://httpbin.org/status/418'
    request = HttpcRequests(url)
    request.GET()

    print("========= 2nd Request =========")
    url = 'http://httpbin.org/status/418'
    headers = {'key': 'value'}
    request = HttpcRequests(url, headers=headers)
    request.GET()

    print("========= 3rd Request =========")
    request = HttpcRequests(url, headers=headers, verbose=True)
    request.GET()

    print("========= 4th Request =========")
    url = 'http://httpbin.org/get?course=networking&assignment=1'
    headers = {'key1': 'value1'}
    request = HttpcRequests(url, headers=headers)
    request.GET()

    print("========= 5th Request =========")
    url = 'http://httpbin.org/post'
    data = {'Assignment': 1}
    headers = {"Content-Type": "application/json"}
    request = HttpcRequests(url, headers=headers, post_inline_data=data)
    request.POST()

    print("========= 6th Request =========")
    url = 'http://httpbin.org/post'
    headers = {"Content-Type": "application/json"}
    request = HttpcRequests(url=url, headers=headers,
                            post_input_file='file1.json')
    request.POST()

    print("========= 7th Request =========")
    url = 'http://httpbin.org/post'
    headers = {"Content-Type": "application/json"}
    request = HttpcRequests(url=url, headers=headers,
                            post_input_file='file1.json', output_file='result.txt')
    request.POST()
