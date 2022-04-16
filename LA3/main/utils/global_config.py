from enum import IntEnum
from time import mktime
from datetime import datetime
from wsgiref.handlers import format_date_time


# directories for post request input files
INPUTS_DIR = '../inputs/'
# directories for storing responses made by requests
OUTPUTS_DIR = '../outputs/'

# global server folder where all files/directories to be requested should reside
GLOBAL_SERVER_DIR = '../server'

# default router host and port to be used for listening incoming packets
DEFAULT_ROUTER_HOST = 'localhost'
DEFAULT_ROUTER_PORT = 3000

# default server host and port to be used for listening incoming packets
DEFAULT_SERVER_HOST = 'localhost'
DEFAULT_SERVER_PORT = 8007

# connection timeout
CONN_TIMEOUT = 5

# headers: default user agent (for console output)
# html body response depends on the user agent
DEFAULT_USER_AGENT = 'Concordia-HTTP/1.0'
# headers: compute current date (accessed date)
DATE = format_date_time(mktime(datetime.now().timetuple()))

# dict of status code with its corresponding message
STATUS_MESSAGE = {
    200:
    {
        'message': 'OK'
    },
    400:
    {
        'message': 'Bad Request',
        'htmlbody': '<html><body><center style="padding: 20px">' +
        '<h1>Error 400: Bad Request</h1></center></body></html>',
    },
    403:
    {
        'message': 'File Access Forbidden',
        'htmlbody': '<html><body><center style="padding: 20px">' +
        '<h1>Error 403: File Access Forbidden</h1></center></body></html>',
    },
    404:
    {
        'message': 'File Not Found',
        'htmlbody': '<html><body><center style="padding: 20px">' +
        '<h1>Error 404: File Not Found</h1></center></body></html>',
    }
}


class RequestMethod(IntEnum):
    GET, POST = range(0, 2)


class PacketType(IntEnum):
    '''
    [0] DATA: data packet
    [1] SYN: used to initiate and establish a connection 
    (also helps you to synchronize seq#s between devices)
    [2] SYNACK: SYN message from local device and ACK of the earlier packet
    [3] ACK: helps to confirm to the other side that it has received the SYN
    [4] NACK:
    [5] FIN:
    '''
    DATA, SYN, SYNACK, ACK, NACK, FIN = range(0, 6)


class PacketStatus(IntEnum):
    CREATED, SENT, RECEIVED = range(0, 3)
