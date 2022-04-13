import argparse
from argparse import RawTextHelpFormatter as rtf
import sys
from console_messages import HttpcManuals
from libhttpc import HttpcRequests

#print(HttpcManuals.LOGO)
#print(HttpcManuals.WELCOME)
#print(HttpcManuals.DESCRIPTION)

INPUTS_DIR = './inputs/'

class HTTPC:
    def __init__(self):
        self.url = ''
        self.headers = ''
        self.verbose = False
        self.inline_data = ''
        self.file = ''
        self.output_file= ''

        parser = argparse.ArgumentParser(prog='httpc', conflict_handler='resolve', usage=argparse.SUPPRESS, description=HttpcManuals.HELP, epilog=HttpcManuals.HELP_EPILOG, formatter_class=rtf)
        parser.add_argument('command')
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            print('!!! httpc error: unrecognized arguments:', args.command)
            print()
            parser.print_help()
        else:   # use dispatch pattern to invoke method with same name
            getattr(self, args.command)()


    def convert_headers_to_dict(self):
        self.headers = [header.split(':') for header in self.headers]
        self.headers = {header[0]:header[1] for header in self.headers}
        
        
    def file_is_valid(self, file):
        try:
            f = open(file, 'rb')
        except FileNotFoundError:
            print("!!! httpc error: File {file} not found.  Aborting")
            sys.exit(1)
        except OSError:
            print("!!! httpc error: OS error occurred trying to open {file}")
            sys.exit(1)
        except Exception as err:
            print("!!! httpc error: Unexpected error opening {file} is",repr(err))
            sys.exit(1)
        else:
            return True


    def get(self):
        parser = argparse.ArgumentParser(prog='httpc', conflict_handler='resolve', usage=argparse.SUPPRESS, description=HttpcManuals.GET_HELP, formatter_class=rtf)
        parser.add_argument('-v', '--verbose', action='store_true', help=HttpcManuals.V_HELP)
        parser.add_argument('-h', '--headers', action='extend', nargs='*', metavar='key:value', help=HttpcManuals.H_HELP)
        parser.add_argument('URL', help='server host')
        parser.add_argument('-o', '--output', help=HttpcManuals.O_HELP)
        args = parser.parse_args(sys.argv[2:])  # sys.argv[0] = httpc.py, sys.argv[1] = get

        self.url = args.URL
        self.headers = args.headers
        self.verbose = args.verbose
        self.output_file = args.output
        
        # Convert string headers into dict if exists
        if self.headers:
            self.convert_headers_to_dict()

        # Register information to create request messages and send GET request
        request_messages = HttpcRequests(url=self.url, headers=self.headers, verbose=self.verbose, output_file=self.output_file)
        request_messages.GET()


    def post(self):
        parser = argparse.ArgumentParser(prog='httpc', conflict_handler='resolve', usage=argparse.SUPPRESS, description=HttpcManuals.POST_HELP, epilog=HttpcManuals.POST_EPILOG, formatter_class=rtf)
        parser.add_argument('-v', '--verbose', action='store_true', help=HttpcManuals.V_HELP)
        parser.add_argument('-h', '--headers', action='extend', nargs='*', metavar='key:value', help=HttpcManuals.H_HELP)
        parser.add_argument('-d', '--inline-data', metavar='string', help=HttpcManuals.D_HELP, dest='inline_data')
        parser.add_argument('-f', '--file', help=HttpcManuals.F_HELP, dest='file')
        parser.add_argument('URL', help='server host')
        parser.add_argument('-o', '--output', help=HttpcManuals.O_HELP)
        args = parser.parse_args(sys.argv[2:])

        self.url = args.URL
        self.headers = args.headers
        self.verbose = args.verbose
        self.inline_data = args.inline_data
        self.file = args.file
        
        if self.inline_data and self.file:  # both -d and -v cannot be used
            print("!!! httpc error: -d and -f cannot be used together")
        else:
            # Convert string headers into dict if exists
            if self.headers:
                self.convert_headers_to_dict()
            
            if self.file:
                self.file = INPUTS_DIR + self.file
                self.file_is_valid(self.file)   # validate file
            self.output_file = args.output
                
            # Register information to create request messages and send POST request
            request_messages = HttpcRequests(url=self.url, headers=self.headers, post_inline_data=self.inline_data, post_input_file=self.file, verbose=self.verbose, output_file=self.output_file)
            request_messages.POST()


    # Custom help CLI argument
    def help(self):
        parser = argparse.ArgumentParser(prog='httpc', conflict_handler='resolve', usage=argparse.SUPPRESS, add_help=False, description=HttpcManuals.HELP, epilog=HttpcManuals.HELP_EPILOG, formatter_class=rtf)
        parser.add_argument('command', nargs='?', default='help')
        args = parser.parse_args(sys.argv[2:])
        if args.command == 'help':
            parser.print_help()
        elif args.command == 'get':
            print(HttpcManuals.GET_HELP_CUSTOM)
        elif args.command == 'post':
            print(HttpcManuals.POST_HELP_CUSTOM)
        else:
            print('!!! httpc error: unrecognized arguments:', args.command)
            print()
            parser.print_help()



if __name__ == '__main__':
    HTTPC()


''' help message '''
# python3 httpc.py help / -h / --help
# python3 httpc.py help get / python3 httpc.py get --help
# python3 httpc.py help post / python3 httpc.py post --help

''' error handling (check the unrecognized argument message) '''
# python3 httpc.py adfdasfdasf help
# python3 httpc.py adfadsfdsaf
# # python3 httpc.py --> following arg are required: 'command'

''' get '''
# python3 httpc.py get http://httpbin.org/status/418
# python3 httpc.py get https://httpbin.org/get
# python3 httpc.py get 'http://httpbin.org/get?course=networking&assignment=1'
''' get: verbose '''
# python3 httpc.py get http://httpbin.org/status/418 -v
# python3 httpc.py get -v 'http://httpbin.org/get?course=networking&assignment=1'
''' get: header '''
# python3 httpc.py get 'http://httpbin.org/get?course=networking&assignment=1' -h 'key:value'
''' get: header, verbose '''
# python3 httpc.py get 'http://httpbin.org/get?course=networking&assignment=1' -h 'key:value' -v
''' get: verbose, multiple headers '''
# python3 httpc.py get https://httpbin.org/get -v -h "Content-Type:application/json" "Cache-Control: max-age=0" "Connection: close"
# python3 httpc.py get "http://httpbin.org/headers" -v -h "Accept-Language: en us,en;q=0.5" -h "Content-Type: application/json; charset=utf-8"
''' get: verbose, output '''
# python3 httpc.py get -v 'http://httpbin.org/get?course=networking&assignment=1' -o output.txt

''' post: header '''
# python3 httpc.py post -h Content-Type:application/json http://httpbin.org/post
#   ---> reply content is null (0)
''' post: header, inline-data '''
# python3 httpc.py post -h Content-Type:application/json -d '{"Assignment": 1}' http://httpbin.org/post
''' post: verbose, multiple headers, inline-data '''
# python3 httpc.py post -v -h "Content-Type:application/json" "Cache-Control: max-age=0" "Connection: close" -d "{"Assignemnt": 1, "Course": "Networking"}" "http://httpbin.org/post"
''' post: verbose, multiple headers, file '''
# python3 httpc.py post -v -h Content-Type:application/json -f file1.json  http://httpbin.org/post
''' post: verbose, multiple headers, file, output '''
# python3 httpc.py post -v -h Content-Type:application/json -f file1.json  http://httpbin.org/post -o file1.json