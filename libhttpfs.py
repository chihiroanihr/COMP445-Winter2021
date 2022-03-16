from http.client import responses
import socket
import threading
import os
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime


GLOBAL_SERVER_DIR = 'server' # global server folder where all directories should reside
STATUS_MESSAGE = {
    200: 'OK', 
    400: 'Bad Request', 
    403: 'File Access Forbidden', 
    404: 'File Not Found'
}

def run_server(host='', port=8007, directory='', verbose=True):
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        listener.bind((host, port))
        listener.listen(5)

        print('\n\n* * * * * Server is listening at {} * * * * *'.format(port))

        # if custom directory chosen then create new directory inside the global server folder
        if directory:
            directory = GLOBAL_SERVER_DIR + '/' + directory
            if not os.path.exists(directory): # if custom directory does not exist
                os.mkdir(directory)
                print("New server folder '{}' created.".format(directory))
            print("Server folder '{}' was assigned.".format(directory))
        else: # if default directory chosen then 'server/default' server folder will be chosen.
            print("Default server folder: 'server/default' was assigned.") if verbose else ''
            directory = GLOBAL_SERVER_DIR + '/default'

        while True:
            conn, addr = listener.accept()
            threading.Thread(target=handle_client, args=(conn, addr, directory, verbose)).start()

    finally:
        listener.close()


def parse_request(http_request_msg):
    '''
    # http_request_msg[0] <- [method] [server dir] [http protocol ver]
    # http_request_msg[1...n] <- [header line]
    # http_request_msg[-1] <- [body]
    '''
    http_request_msg = http_request_msg.split('\r\n\r\n')
    metadata = http_request_msg[0].split('\r\n')
    metadata = list(filter(None, metadata))

    request_lines = metadata[0].split(' ')
    request_method = request_lines[0]
    request_path = request_lines[1]
    protocol_ver = request_lines[2] if len(request_lines) > 2 else ''

    headers = metadata[1:]
    body = http_request_msg[1]

    return headers, body, request_method, request_path, protocol_ver


def create_response_msg(headers, body, request_method, request_path, protocol_ver, server_dir, verbose):
    response = ''
 
    status_code = 200
    content_type = ''
    content_length = 0
    connection = 'close'

    # Commpute Date
    now = datetime.now()
    stamp = mktime(now.timetuple())
    date = format_date_time(stamp)

    ########## GET ##########
    if request_method == 'GET':
        # 1. GET /
        if request_path == '/':
            files = os.listdir(server_dir)
            status_code = 200
            content_type = 'text/plain'
            body = '\n'.join(files) # convert list of files into string
        # 2. GET /filename
        else:
            try:
                with open(server_dir + request_path, 'r') as file:
                    status_code = 200
                    content_type = 'text/plain' ##########
                    body += file.read()
            except IOError:
                status_code = 404
    ########## POST ##########
    elif request_method == 'POST':
        if request_path == '/':
            status_code = 400
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
                file.write(body)
            content_type = 'text/plain' ##########
    ######## INVALID ########
    else:
        status_code = 400

    # extract necessary header queries if those exists in headers
    if status_code == 200:
        for header in headers:
            if 'content-length' in header.lower():
                content_length = header
            elif 'content-type' in header.lower():
                content_type = header
    
    # set the content length
    content_length = len(body)

    response += "{} {} {}\r\nDate: {}\r\n".format(protocol_ver, status_code, STATUS_MESSAGE[status_code], date)
    response += "Content-type: {}\r\n".format(content_type) if content_type else ''
    response += "Content-length: {}\r\nConnection: {}".format(content_length, connection)
    response += "\r\n\r\n{}".format(body)

    return response


def handle_client(conn, addr, server_dir, verbose):
    print('\n\n-----------------------------------------------')
    print("* New client from {}".format(addr))
    try:
        while True:
            http_request_msg = conn.recv(1024).decode()
            if not http_request_msg:
                break

            print("* Request Messages: \n{}".format(http_request_msg)) if verbose else ''

            # parse http request
            headers, body, request_method, request_path, protocol_ver = parse_request(http_request_msg)

            # create respone message
            response = create_response_msg(headers, body, request_method, request_path, protocol_ver, server_dir, verbose)

            # send back response message
            conn.sendall(response.encode("utf-8"))
            print("* Response sent to {}".format(addr)) if verbose else ''
            print("* Response: \n{}".format(response).strip()) if verbose else ''
            print()

    finally:
        conn.close()
        print('* Connection closed') if verbose else ''


if __name__ == "__main__":
    run_server(port=8007)