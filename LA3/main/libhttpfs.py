import socket
import os
from packet import Packet
from utils.shell_output import shell_boxing
from utils.global_config import (
    GLOBAL_SERVER_DIR,
    DEFAULT_SERVER_PORT,
    DATE,
    DEFAULT_USER_AGENT,
    STATUS_MESSAGE
)


def run_server(server_port=DEFAULT_SERVER_PORT, server_dir='', verbose=True):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        # Create or Assign Server Directory
        # if custom directory chosen then create new directory inside the global server folder
        if server_dir:
            server_dir = server_dir.replace('/', '')
            server_dir = GLOBAL_SERVER_DIR + '/' + server_dir
            # if custom directory does not exist
            if not os.path.exists(server_dir):
                os.mkdir(server_dir)
                print(f">>> New server folder {server_dir} created.")
            print(f">>> Server folder {server_dir} was assigned.")
        # if default directory chosen then 'server/default' server folder will be chosen.
        else:
            server_dir = GLOBAL_SERVER_DIR + '/default'
            print(
                f">>> Default server folder: {server_dir} was assigned." if verbose else '')

        # start the server socket
        server_socket.bind(('', server_port))
        print(
            f"\n\n* * * * * * Server is listening at {server_port} * * * * * *")

        while True:
            # Server receives packet with the carrier address (router address)
            packet, sender_addr = server_socket.recvfrom(1024)

            # Extracts message's payload
            handle_client(
                server_socket,
                packet,
                sender_addr,
                server_dir,
                verbose
            )

    except KeyboardInterrupt:
        print("* * * * * * Session Finished with ctrl-C * * * * * *")

    finally:
        server_socket.close()


def handle_client(server_socket, packet, sender_addr, server_dir, verbose):
    print('\n\n================================================')
    print(">>> Received a packet from client via router.")

    try:
        # Convert from network-byte (big-endian order) to host-byte when receiving packet
        packet = Packet.from_bytes(packet)

        # TODO: if packet type = 0 (data packet) then retrieve / parse http request

        # Extracts response message payload
        receive_payload = packet.payload.decode("utf-8")

        # parse and retrieve http request data
        headers, body, request_method, request_path, protocol_ver = parse_request(
            receive_payload)

        # Output client packet message
        print("Router: ", sender_addr)
        print("Packet: ", packet)
        print(f"Payload: \n{shell_boxing(receive_payload)}")
        print("Payload Queries: \n{}"
              .format(
                  shell_boxing(
                      f"headers: {headers}\r\n" +
                      f"body: {body}\r\n" +
                      f"request method: {request_method}\r\n" +
                      f"request path: {request_path}\r\n" +
                      f"protocol version: {protocol_ver}",
                      output_queries=True
                  )
              )
              if verbose else ''
              )

        # create respone message
        print(">>> Performing request and Creating response message" if verbose else '')
        response_msg = perform_request(
            headers, body, request_method, request_path, protocol_ver, server_dir
        )

        # # create response packet via storing the response message to packet
        print(">>> Creating response packet" if verbose else '')
        packet.payload = response_msg.encode("utf-8")
        print('>>> Response packet created.' if verbose else '')

        # output response packet message
        print("Packet: ", packet)
        print(f"Payload: \n{shell_boxing(response_msg)}")

        # convert from host-byte (big-endian order) to network-byte when sending packet
        packet = packet.to_bytes()

        # send back the response to client via router
        print(">>> Send response packet back to client via router")
        server_socket.sendto(packet, sender_addr)
        print(">>> Successfully sent.")

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


def perform_request(headers, post_body_message, request_method, request_path, protocol_ver, server_dir):
    # initialize variables
    response_body = ''
    status_code = 200
    content_type = ''
    content_length = 0
    connection = 'close'
    request_abs_path = server_dir + request_path

    ### INVALID SECURE ACCESS ###
    if '/..' in request_abs_path:
        status_code = 403
        response_body = '' if any(
            DEFAULT_USER_AGENT in header for header in headers) \
            else STATUS_MESSAGE[status_code]['htmlbody']

    #### GET ####
    elif request_method == 'GET':
        # 1. GET / or GET /folder
        if request_path == '/' or os.path.isdir(request_abs_path):
            files = os.listdir(request_abs_path)
            content_type = 'text/plain'
            response_body = '\n'.join(files) if len(files) > 0 \
                else f"\n{status_code}\nNo files have found in this directory '{server_dir}'"
        # 2. GET /filename
        elif os.path.isfile(request_abs_path):
            with open(request_abs_path, 'r', encoding='utf-8') as file:
                content_type = 'text/plain'
                response_body += file.read()
        # INVALID: PATH DOES NOT EXIST
        else:
            status_code = 404
            response_body = '' if any(
                DEFAULT_USER_AGENT in header for header in headers) \
                else STATUS_MESSAGE[status_code]['htmlbody']

    #### POST ####
    elif request_method == 'POST':
        # INVALID: FILE NOT SPECIFIED
        if request_path == '/' or os.path.isdir(request_abs_path):
            status_code = 400
            response_body = '' if any(
                DEFAULT_USER_AGENT in header for header in headers) \
                else STATUS_MESSAGE[status_code]['htmlbody']
        # 3. POST /filename
        else:
            request_path = request_path.rsplit('/', 1)
            filename = request_path[1]  # extract filename
            # if directories path also listed
            directories = server_dir + request_path[0]
            # if dir does not exist, then create
            if not os.path.exists(directories):
                os.makedirs(directories)
            # if file does not exist, then create, otherwise overwrite to the existing file
            with open(os.path.join(directories, filename), 'w', encoding='utf-8') as file:
                file.write(post_body_message)
            content_type = 'text/plain'

    ### INVALID REQUEST METHOD ###
    else:
        status_code = 400
        response_body = '' if any(
            DEFAULT_USER_AGENT in header for header in headers
        ) else STATUS_MESSAGE[status_code]['htmlbody']

    # set the content length
    content_length = len(response_body)

    # replace certain header queries if client specified them manually
    # in the header of request method
    if status_code == 200:
        for header in headers:
            if 'Content-Length' in header:
                content_length = header.replace('Content-Length:', '').strip()
            if 'Content-Type' in header:
                content_type = header.replace('Content-Type:', '').strip()

    # create response message based on the info retrieved
    response = create_response_message(
        protocol_ver, status_code, connection, content_length, content_type, response_body)

    return response


def create_response_message(protocol_ver, status_code, connection, content_length, content_type='', response_body=''):
    response = ''

    # create response message
    response += f"{protocol_ver} {status_code} {STATUS_MESSAGE[status_code]['message']}\r\n"
    response += f"Date: {DATE}\r\n"
    response += f"Content-Type: {content_type}\r\n" if content_type else ''
    response += f"Content-Length: {content_length}\r\n"
    response += f"Connection: {connection}"
    response += f"\r\n\r\n{response_body}"

    return response


if __name__ == "__main__":
    run_server(server_port=8007)
    # run_server(server_port=8010)
