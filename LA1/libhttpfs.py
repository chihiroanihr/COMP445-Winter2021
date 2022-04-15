import socket
import threading
import os
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime

# global server folder where all directories should reside
GLOBAL_SERVER_DIR = 'server'
# compute current date (accessed date)
DATE = format_date_time(mktime(datetime.now().timetuple()))
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
# html body response depends on the user agent (default is user agent from terminal)
DEFAULT_USER_AGENT = 'Concordia-HTTP/1.0'


def run_server(host='', port=8007, directory='', verbose=True):
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        listener.bind((host, port))
        listener.listen(5)

        print('\n\n* * * * * Server is listening at {} * * * * *'.format(port))

        # if custom directory chosen then create new directory inside the global server folder
        if directory:
            directory = directory.replace('/', '')
            directory = GLOBAL_SERVER_DIR + '/' + directory
            if not os.path.exists(directory): # if custom directory does not exist
                os.mkdir(directory)
                print("New server folder '{}' created.".format(directory))
            print("Server folder '{}' was assigned.".format(directory))
        else: # if default directory chosen then 'server/default' server folder will be chosen.
            directory = GLOBAL_SERVER_DIR + '/default'
            print("Default server folder: '{}' was assigned.".format(directory)) if verbose else ''

        while True:
            conn, addr = listener.accept()
            threading.Thread(target=handle_client, args=(conn, addr, directory, verbose)).start()
    finally:
        listener.close()


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

    print('* Response message created') if verbose else ''
    return response


def handle_client(conn, addr, server_dir, verbose):
    print('\n\n==============================================')
    print("* New client from {}".format(addr))

    try:
        while True:
            http_request_msg = conn.recv(4096).decode()
            if not http_request_msg:
                break

            # parse http request
            headers, body, request_method, request_path, protocol_ver = parse_request(http_request_msg)
            print('\n\n----------------------------------------------')
            print("* Request Messages: \n{}".format(http_request_msg.strip())) if verbose else ''
            print("\n* Request Message Queries: \n\theaders: {} \n\tbody: {} \n\trequest method: {} \n\trequest path: {} \n\tprotocol version: {}\
                ".format(headers, body, request_method, request_path, protocol_ver)) if verbose else ''

            # create respone message
            response = create_response_msg(headers, body, request_method, request_path, protocol_ver, server_dir, verbose)

            # send back response message
            conn.sendall(response.encode("utf-8"))
            print("* Response sent to {}".format(addr)) if verbose else ''
            print("* Response: \n\n{}".format(response).strip()) if verbose else ''
            print()

    finally:
        conn.close()
        print('* Connection closed') if verbose else ''



if __name__ == "__main__":
    #run_server(port=8007)
    run_server(port=8010)

    ''' get: /, verbose '''
    # python3 httpc.py get https://localhost:8007/ -v
    ''' get: /filename '''
    # python3 httpc.py get https://localhost:8007/file1.txt
    ''' get: /foldername '''
    # python3 httpc.py get https://localhost:8007/folder2
    # python3 httpc.py get https://localhost:8007/../ -v
    # --> 403 Security Error
    ''' get: /, verbose, header '''
    # python3 httpc.py get http://localhost:8007/ -v -h "key:value"  
    # python3 httpc.py get https://localhost:8007/ -v -h Content-Type:application/json
    # python3 httpc.py get https://localhost:8007/folder1 -v -h Content-Type:application/json
    # python3 httpc.py get https://localhost:8007/a.txt -v -h Content-Type:application/json
    # python3 httpc.py get https://localhost:8007/foo -v -h Content-Type:application/json
    # --> 404 File Not Found

    ''' post: /, verbose '''
    # python3 httpc.py post https://localhost:8007/ -v
    # --> 400 Bad Request since posting to folder
    # python3 httpc.py post https://localhost:8007/../../ -v
    # --> 403 Security Error
    ''' post: /foldername, verbose, header '''
    # python3 httpc.py post https://localhost:8007/folder1/file1.json -v -h Content-Type:application/json
    # python3 httpc.py post https://localhost:8007/folder1 -v -h Content-Type:application/json
    # --> 400 Bad Request since posting to folder
    ''' post: /filename, verbose, header, inline-data '''
    # python3 httpc.py post https://localhost:8007/folder1/file2.txt
    # python3 httpc.py post https://localhost:8007/folder1/file2.txt -d "hi, i am file2.txt"
    # python3 httpc.py post https://localhost:8007/folder1/file3.txt -h Content-Length:2 -d "hi, i am file3.txt"
    # python3 httpc.py post https://localhost:8007/folder1/file4.json -f file1.json
    # python3 httpc.py post https://localhost:8007/ -f file1.json -v
    # --> 400 Bad Request simce posting to folder