import socket
import os
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
from packet import Packet

# global server folder where all directories should reside
GLOBAL_SERVER_DIR = 'server'
# Default server port to be used for listening incoming packets
DEFAULT_SERVER_PORT = 8010
# compute current date (accessed date)
DATE = format_date_time(mktime(datetime.now().timetuple()))
# html body response depends on the user agent (default is user agent from terminal)
DEFAULT_USER_AGENT = 'Concordia-HTTP/1.0'
# dict of status code with corresponding messages
STATUS_MESSAGE = {
    200: 
    {
        'message': 'OK'
    },
    400: 
    {
        'message': 'Bad Request',
        'htmlbody': '<html><body><center style="padding: 20px"><h1>Error 400: Bad Request</h1></center></body></html>',
    }, 
    403: 
    {
        'message': 'File Access Forbidden', 
        'htmlbody': '<html><body><center style="padding: 20px"><h1>Error 403: File Access Forbidden</h1></center></body></html>',
    },
    404: 
    {
        'message': 'File Not Found',
        'htmlbody': '<html><body><center style="padding: 20px"><h1>Error 404: File Not Found</h1></center></body></html>',
    }
}


def run_server(host='', port=DEFAULT_SERVER_PORT, directory='', verbose=True):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        server_socket.bind(('', port))
        print('\n\n* * * * * Server is listening at {} * * * * *'.format(port))
        
        # Create or Assign Server Directory
        if directory: # if custom directory chosen then create new directory inside the global server folder
            directory = directory.replace('/', '')
            directory = GLOBAL_SERVER_DIR + '/' + directory
            if not os.path.exists(directory): # if custom directory does not exist
                os.mkdir(directory)
                print(">>> New server folder '{}' created.".format(directory))
            print(">>> Server folder '{}' was assigned.".format(directory))
        else: # if default directory chosen then 'server/default' server folder will be chosen.
            directory = GLOBAL_SERVER_DIR + '/default'
            print(">>> Default server folder: '{}' was assigned.".format(directory)) if verbose else ''

        while True:
            # Server receives packet with the carrier address (router address)
            packet_data, sender_addr = server_socket.recvfrom(1024)
            print(">>> Received a packet from client via router.")
            
            # Extracts message's payload
            handle_client(server_socket, packet_data, sender_addr, directory, verbose)
    
    finally:
        server_socket.close()


def handle_client(server_socket, packet_data, sender_addr, server_dir, verbose):
    print('\n\n==============================================')
    
    try:
        # Convert from network-byte (big-endian order) to host-byte when receiving packet
        packet = Packet.from_bytes(packet_data)
        
        # TODO: if packet type = 0 (data packet) then retrieve / parse http request
        
        # Extracts response message payload
        payload = packet.payload.decode("utf-8")
        
        # parse and retrieve http request data
        headers, body, request_method, request_path, protocol_ver = parse_request(payload)
        
        # Output client packet message
        print("---> Router: ", sender_addr)
        print("---> Packet: ", packet)
        print("---> Payload: ", payload)
        print("---> Payload Queries: \n\t - headers: {} \n\t - body: {} \n\t - request method: {} \n\t - request path: {} \n\t - protocol version: {}\
            ".format(headers, body, request_method, request_path, protocol_ver)) if verbose else ''
        
        # create respone message
        print(">>> Creating response.")
        response_msg = create_response_msg(headers, body, request_method, request_path, protocol_ver, server_dir, verbose)
        print('>>> Response message created.') if verbose else ''

        # store the server response message back to packet
        packet.payload = response_msg.encode("utf-8")
        
        # convert from host-byte (big-endian order) to network-byte when sending packet
        packet = packet.to_bytes()
        
        # send back the response to client via router
        print(">>> Send response packet back to client via router")
        print(">>> Response payload: {}".format(response_msg).strip()) if verbose else ''
        server_socket.sendto(packet, sender_addr)
        print(">>> Successfully sent.") if verbose else ''
        
    except Exception as e:
        print("!!! Error occured when handling response message from client: \n", e)
        

def parse_request(http_request_msg):
    '''
    http_request_msg[0] <- [method][server dir][http protocol ver] & [header line]
    http_request_msg[1] <- [body]
    '''
    http_request_msg = http_request_msg.split('\r\n\r\n')
    metadata = http_request_msg[0].split('\r\n')
    metadata = list(filter(None, metadata))

    request_lines = metadata[0].split(' ')
    request_method = request_lines[0]
    request_path = request_lines[1]
    protocol_ver = request_lines[2] if len(request_lines) > 2 else ''

    headers = metadata[1:]
    if len(http_request_msg) == 1:
        body = ''
    else:
        body = http_request_msg[1]

    return headers, body, request_method, request_path, protocol_ver


def create_response_msg(headers, post_body_message, request_method, request_path, protocol_ver, server_dir, verbose):
    # initialize variables
    response = ''
    response_body = ''
    status_code = 200
    content_type = ''
    content_length = 0
    connection = 'close'
    request_abs_path = server_dir + request_path

    ######## INVALID SECURE ACCESS ########
    if '/..' in request_abs_path:
        status_code = 403
        response_body = '' if any(DEFAULT_USER_AGENT in header for header in headers) else STATUS_MESSAGE[status_code]['htmlbody']
        
    ########## GET ##########
    elif request_method == 'GET':
        # 1. GET / or GET /folder
        if request_path == '/' or os.path.isdir(request_abs_path):
            files = os.listdir(request_abs_path)
            content_type = 'text/plain'
            response_body = '\n'.join(files) if len(files) > 0 else '\n{}\nNo files have found in this directory "{}"'.format(status_code, server_dir)
        # 2. GET /filename
        elif os.path.isfile(request_abs_path):
            with open(request_abs_path, 'r') as file:
                content_type = 'text/plain' ##########
                response_body += file.read()
        # INVALID: PATH DOES NOT EXIST
        else:
            status_code = 404
            response_body = '' if any(DEFAULT_USER_AGENT in header for header in headers) else STATUS_MESSAGE[status_code]['htmlbody']
    
    ########## POST ##########
    elif request_method == 'POST':
        # INVALID: FILE NOT SPECIFIED
        if request_path == '/' or os.path.isdir(request_abs_path):
            status_code = 400
            response_body = '' if any(DEFAULT_USER_AGENT in header for header in headers) else STATUS_MESSAGE[status_code]['htmlbody']
        # 3. POST /filename
        else:
            request_path = request_path.rsplit('/', 1)
            filename = request_path[1] # extract filename
            directories = server_dir + request_path[0] # if directories path also listed
            # if dir does not exist, then create
            if not os.path.exists(directories):
                os.makedirs(directories)
            # if file does not exist, then create, otherwise overwrite to the existing file
            with open(os.path.join(directories, filename), 'w') as file:
                file.write(post_body_message)
            content_type = 'text/plain' ##########

    ######## INVALID REQUEST METHOD ########
    else:
        status_code = 400
        response_body = '' if any(DEFAULT_USER_AGENT in header for header in headers) else STATUS_MESSAGE[status_code]['htmlbody']
    
    # set the content length
    content_length = len(response_body)

    # replace certain header queries if client specified them manually in the header of request method
    if status_code == 200:
        for header in headers:
            if 'Content-Length' in header:
                content_length = header.replace('Content-Length:', '').strip()
            if 'Content-Type' in header:
                content_type = header.replace('Content-Type:', '').strip()

    response += "{} {} {}\r\nDate: {}\r\n".format(protocol_ver, status_code, STATUS_MESSAGE[status_code]['message'], DATE)
    response += "Content-Type: {}\r\n".format(content_type) if content_type else ''
    response += "Content-Length: {}\r\n".format(content_length)
    response += "Connection: {}".format(connection)
    response += "\r\n\r\n{}".format(response_body)

    return response



if __name__ == "__main__":
    #run_server(port=8007)
    run_server(port=8010)