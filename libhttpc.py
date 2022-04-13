from re import L
import socket
import sys
from urllib.parse import urlparse
import json

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

class HttpcRequests:

    def __init__(self, url, headers='', post_inline_data='', post_input_file='', verbose=False, output_file='', DEFAULT_PORT=80): # Standard HTTP/TCP port is 80
        self.request_method = None  # To initialize request method: GET / POST
        self.request_message = ''   # To send full request lines to the host
        self.parsed_url = urlparse(url) # Parse URL
        self.hostname = self.parsed_url.hostname
        self.path = self.parsed_url.path if self.parsed_url.path else '/'
        # if port num not specified in url, use default port
        self.port = self.parsed_url.port if self.parsed_url.port else DEFAULT_PORT
        self.query = self.parsed_url.query  # in string
        self.headers = headers  # in dict {'key':'val'}
        self.verbose = verbose
        self.post_inline_data = post_inline_data # in json
        self.post_input_file = post_input_file # in json
        self.body = ''
        self.output_file = output_file

        #self.scheme = self.parsed_url.scheme
        #self.netloc = self.parsed_url.netloc
        #self.params = self.parsed_url.params
        #self.fragment = self.parsed_url.fragment


    def create_request_headers(self):
        DEFAULT_USER_AGENT = 'Concordia-HTTP/1.0'

        # add host entry to the headers dict
        if not self.headers:
            self.headers = dict()
        self.headers['Host'] = self.hostname

        # if User-Agent header does not exist (user did not specified in httpc command line with -h)
        if 'User-Agent' not in self.headers:
            self.headers['User-Agent'] = DEFAULT_USER_AGENT # then append default user-agent
            
        if self.body:
            self.headers['Content-Length'] = str(len(self.body))

        ''' self.headers['Connection'] = 'closed' '''

        request_header_str = ''
        for key, val in self.headers.items():
            request_header_str += '{}:{}\r\n'.format(key, val)
        return request_header_str

    
    def create_request_body(self):
        if self.post_input_file:
            with open(self.post_input_file, encoding='utf-8') as json_file:
                json_data = json.load(json_file)
                self.body=json.dumps(json_data)
        if self.post_inline_data:
            self.body = str(self.post_inline_data)
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
        # open and set up client socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # connect to the server(host) at port num given
            client_socket.connect((self.hostname, self.port))
            # send request message to server
            client_socket.sendall(self.request_message.encode("UTF-8"))
            # receive response data from server
            # MSG_WAITALL waits for full request or error
            response = client_socket.recv(4096, socket.MSG_WAITALL).decode("utf-8")
            # Divide response into header (verbose) and body
            response_header = response[:response.find('\r\n\r\n')].replace('\r\n\r\n', '')
            response_body = response[response.find('\r\n\r\n'):].replace('\r\n\r\n', '')

            # Output response message
            print("[Replied]")
            if self.verbose:
                print(response_header)
            print('\n\n')
            if self.output_file:
                self.output_to_file(response_body)
                print(">>> The response was written in {}".format(self.output_file))
            else:
                print(response_body)

        finally:
            # close the connection
            client_socket.close()


    def GET(self):
        self.request_method = 'GET'

        # Request-URI = [ path ][ "?" query ]
        request_uri = "{}?{}".format(self.path, self.query) if self.query else self.path
        # Request-Line = Method SP Request-URI SP HTTP-Version CRLF
        request_line = "GET {} HTTP/1.0\r\n".format(request_uri)
        # Request-Heaer = Headers CRLF User-Agent CRLF
        request_headers = self.create_request_headers()
        self.request_message = "{}{}\r\n".format(request_line, request_headers)

        print("[Sent]")
        print(self.request_message)

        self.run_client()
        #return self.request_message


    def POST(self):
        self.request_method = 'POST'

        # Request-URI = [ path ][ "?" query ]
        request_uri = "{}?{}".format(self.path, self.query) if self.query else self.path
        # Request-Line = Method SP Request-URI SP HTTP-Version CRLF
        request_line = "POST {} HTTP/1.0\r\n".format(request_uri)
        # Request-Body
        request_body = self.create_request_body()
        # Request-Heaer = Headers CRLF User-Agent CRLF
        request_headers = self.create_request_headers()

        self.request_message = "{}{}\r\n{}\r\n".format(request_line, request_headers, request_body)

        print("[Sent]")
        print(self.request_message)

        self.run_client()
        #return self.request_message


if __name__ == "__main__":
    print("========= 1st Request =========")
    url = 'http://httpbin.org/status/418'
    request = HttpcRequests(url)
    request.GET()
    
    print("========= 2nd Request =========")
    url = 'http://httpbin.org/status/418'
    headers = {'key':'value'}
    request = HttpcRequests(url, headers=headers)
    request.GET()

    print("========= 3rd Request =========")
    request = HttpcRequests(url, headers=headers, verbose=True)
    request.GET()

    print("========= 4th Request =========")
    url = 'http://httpbin.org/get?course=networking&assignment=1'
    headers = {'key1':'value1'}
    request = HttpcRequests(url, headers=headers)
    request.GET()

    print("========= 5th Request =========")
    url = 'http://httpbin.org/post'
    data = {'Assignment': 1}
    headers = {"Content-Type":"application/json"}
    request = HttpcRequests(url, headers=headers, post_inline_data=data)
    request.POST()
    
    print("========= 6th Request =========")
    url = 'http://httpbin.org/post'    
    headers = {"Content-Type":"application/json"}
    request = HttpcRequests(url=url, headers=headers, post_input_file='file1.json')
    request.POST()
    
    print("========= 7th Request =========")
    url = 'http://httpbin.org/post'    
    headers = {"Content-Type":"application/json"}
    request = HttpcRequests(url=url, headers=headers, post_input_file='file1.json', output_file='result.txt')
    request.POST()