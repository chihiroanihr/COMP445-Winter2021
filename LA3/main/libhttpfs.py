import socket
import os
from packet import Packet
from utils.shell_output import shell_boxing
from utils.global_config import (
    GLOBAL_SERVER_DIR,
    DEFAULT_SERVER_PORT,
    DATE,
    DEFAULT_USER_AGENT,
    STATUS_MESSAGE,
    MAX_SEQ_NUM,
    MAX_WINDOW_SIZE,
    PacketType
)


class HttpfsRequests:
    def __init__(self,
                 server_port=DEFAULT_SERVER_PORT,
                 server_dir='',
                 verbose=False,
                 ):
        self.server_port = server_port
        self.server_dir = server_dir
        self.verbose = verbose

        self.peer_ip_addr = ''
        self.request_message_queries = ''
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def run_server(self):

        try:
            # Create or Assign Server Directory
            # if custom directory chosen then create new directory inside the global server folder
            if self.server_dir:
                self.server_dir = self.server_dir.replace('/', '')
                self.server_dir = GLOBAL_SERVER_DIR + '/' + self.server_dir
                # if custom directory does not exist
                if not os.path.exists(self.server_dir):
                    os.mkdir(self.server_dir)
                    print(f">>> New server folder {self.server_dir} created.")
                print(f">>> Server folder {self.server_dir} was assigned.")
            # if default directory chosen then 'server/default' server folder will be chosen.
            else:
                self.server_dir = GLOBAL_SERVER_DIR + '/default'
                print(
                    f">>> Default server folder: {self.server_dir} was assigned.")

            # start the server socket
            self.server_socket.bind(('', self.server_port))
            print(
                f"\n\n* * * * * * Server is listening at {self.server_port} * * * * * *")

            # receive packets from router via selective repeat protocol
            seq_start = 0  # sequence number of first frame in window
            window_buffers = []  # array of max window size
            seq_nums_window = []
            received_buffer = []

            while True:
                # Server receives packet with the carrier address (router address)
                packet, sender_addr = self.server_socket.recvfrom(1024)

                # Convert from network-byte (big-endian order) to host-byte when receiving packet
                packet = Packet.from_bytes(packet)

                # packet from different peer addr -> initialize
                if self.peer_ip_addr != packet.peer_ip_addr \
                        or self.request_message_queries['request_method'] == "GET" \
                        or self.request_message_queries['request_method'] == "POST":
                    self.peer_ip_addr = packet.peer_ip_addr
                    self.request_message_queries = ''
                    # initialize every attrs
                    window_buffers = []
                    seq_nums_window = []
                    received_buffer = []
                    seq_start = 0
                
                # parse and retrieve http request data
                self.request_message_queries = self.parse_request(packet)

                # update available sequence numbers in window
                for i in range(MAX_WINDOW_SIZE):
                    if i + seq_start <= MAX_SEQ_NUM:
                        if i + seq_start not in seq_nums_window:
                            seq_nums_window.append(i + seq_start)
                    else:
                        if i + seq_start - MAX_SEQ_NUM not in seq_nums_window:
                            seq_nums_window.append(i + seq_start - MAX_SEQ_NUM)

                packet_type = packet.packet_type
                seq_num = packet.seq_num

                if packet_type == PacketType.DATA and seq_num == seq_start:
                    # return ACK with message
                    print(f">>> Packet #{seq_num} received, send ACK back.")

                    if seq_num == MAX_SEQ_NUM:
                        seq_start = 0
                    else:
                        seq_start = seq_num + 1
                    seq_nums_window.pop(0)

                    # check all the received buffer as well and move sequence start position all at once
                    received_buffer_copy = received_buffer
                    for received_seq in received_buffer_copy:
                        if seq_start == received_seq:
                            received_buffer.remove(received_seq)

                            if received_seq == MAX_SEQ_NUM:
                                seq_start = 0
                            else:
                                seq_start = received_seq + 1
                            seq_nums_window.pop(0)

                elif packet_type == PacketType.DATA and seq_num in seq_nums_window:
                    # return ACK with message
                    print(f">>> Packet #{seq_num} received, send ACK back.")
                    received_buffer.append(seq_num)

                else:
                    print()
                    print(f">>> This packet with sequence number #{seq_num} is already received, " +
                          "thus no request operation performed.")
                    print()

                # Extracts message's payload
                self.handle_client(packet, sender_addr, PacketType.ACK)

        except KeyboardInterrupt:
            print("* * * * * * Session Finished with ctrl-C * * * * * *")

        finally:
            self.server_socket.close()

    def handle_client(self, packet, sender_addr, packet_type):
        print('\n\n================================================')
        print(">>> Received a packet from client via router.")

        # try:
        # Output client packet message
        print("Router: ", sender_addr)
        print("Packet: ", packet)
        print(
            f"Payload: \n{shell_boxing(self.request_message_queries['request_message'])}")
        if self.verbose:
            print("Payload Queries: \n{}"
                  .format(
                      shell_boxing(
                          f"headers: {self.request_message_queries['headers']}\r\n" +
                          f"body: {self.request_message_queries['body']}\r\n" +
                          f"request method: {self.request_message_queries['request_method']}\r\n" +
                          f"request path: {self.request_message_queries['request_path']}\r\n" +
                          f"protocol version: {self.request_message_queries['protocol_ver']}",
                          output_queries=True
                      )
                  )
                  )

        # create respone message
        if self.verbose:
            print(">>> Performing request and Creating response message")
        response_msg = self.perform_request(self.request_message_queries)

        # # create response packet via storing the response message to packet
        if self.verbose:
            print(">>> Creating response packet")
        packet.payload = response_msg.encode("utf-8")
        packet.packet_type = packet_type
        if self.verbose:
            print('>>> Response packet created.')

        # output response packet message
        print("Packet: ", packet)
        print(f"Payload: \n{shell_boxing(response_msg)}")

        # convert from host-byte (big-endian order) to network-byte when sending packet
        packet = packet.to_bytes()

        # send back the response to client via router
        print(">>> Send response packet back to client via router")
        self.server_socket.sendto(packet, sender_addr)
        print(">>> Successfully sent.")

    def parse_request(self, packet):
        '''
        http_request_msg[0] <- [method][server dir][http protocol ver] & [header line]
        http_request_msg[1] <- [body]
        '''
        # Extracts response message payload
        payload = packet.payload.decode("utf-8")
        headers = ''

        if not self.request_message_queries:
            http_request_msg = payload.split('\r\n\r\n')
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

            self.request_message_queries = {
                'request_message': payload,
                'headers': headers,
                'body': body,
                'request_method': request_method,
                'request_path': request_path,
                'protocol_ver': protocol_ver
            }

        else:
            body = payload

        request_message_queries = self.request_message_queries
        request_message_queries['body'] = body

        return request_message_queries

    def perform_request(self, request_message_queries):
        request_path = request_message_queries['request_path']
        headers = request_message_queries['headers']

        # initialize variables
        response_body = ''
        status_code = 200
        content_type = ''
        content_length = 0
        connection = 'close'
        request_abs_path = self.server_dir + request_path

        ### INVALID SECURE ACCESS ###
        if '/..' in request_abs_path:
            status_code = 403
            response_body = '' if any(
                DEFAULT_USER_AGENT in header for header in headers) \
                else STATUS_MESSAGE[status_code]['htmlbody']

        #### GET ####
        elif request_message_queries['request_method'] == 'GET':
            # 1. GET / or GET /folder
            if request_path == '/' or os.path.isdir(request_abs_path):
                files = os.listdir(request_abs_path)
                content_type = 'text/plain'
                response_body = '\n'.join(files) if len(files) > 0 \
                    else f"\n{status_code}\nNo files have found in this directory '{self.server_dir}'"
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
        elif request_message_queries['request_method'] == 'POST':
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
                directories = self.server_dir + request_path[0]
                # if dir does not exist, then create
                if not os.path.exists(directories):
                    os.makedirs(directories)
                # if file does not exist, then create, otherwise overwrite to the existing file
                with open(os.path.join(directories, filename), 'w', encoding='utf-8') as file:
                    file.write(request_message_queries['body'])
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
                    content_length = header.replace(
                        'Content-Length:', '').strip()
                if 'Content-Type' in header:
                    content_type = header.replace('Content-Type:', '').strip()

        # create response message based on the info retrieved
        response = self.create_response_message(
            request_message_queries['protocol_ver'], status_code, connection, content_length, content_type, response_body)

        return response

    def create_response_message(self, protocol_ver, status_code, connection, content_length, content_type='', response_body=''):
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
    server = HttpfsRequests(server_port=8007)
    server.run_server()
