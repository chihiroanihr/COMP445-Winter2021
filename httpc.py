import argparse
from argparse import RawTextHelpFormatter as rtf
from sys import argv
from httpc_manuals import HttpcManuals
from libhttpc import HttpcRequests

#print(HttpcManuals.LOGO)
#print(HttpcManuals.WELCOME)
#print(HttpcManuals.DESCRIPTION)

class HTTPC:
    def __init__(self):
        self.url = ''
        self.headers = {}
        self.verbose = False
        self.inline_data = ''
        self.file = ''

        parser = argparse.ArgumentParser(prog='httpc', conflict_handler='resolve', usage=argparse.SUPPRESS, description=HttpcManuals.HELP, epilog=HttpcManuals.HELP_EPILOG, formatter_class=rtf)
        parser.add_argument('command')
        args = parser.parse_args(argv[1:2])
        if not hasattr(self, args.command):
            print('httpc: error: unrecognized arguments:', args.command)
            print()
            parser.print_help()
        else:   # use dispatch pattern to invoke method with same name
            getattr(self, args.command)()


    def convert_headers_to_dict(self):
        self.headers = [header.split(':') for header in self.headers]
        self.headers = {header[0]:header[1] for header in self.headers}


    def get(self):
        parser = argparse.ArgumentParser(prog='httpc', conflict_handler='resolve', usage=argparse.SUPPRESS, description=HttpcManuals.GET_HELP, formatter_class=rtf)
        parser.add_argument('-v', '--verbose', action='store_true', help=HttpcManuals.V_HELP)
        parser.add_argument('-h', '--headers', action='append', metavar='key:value', default=[], help=HttpcManuals.H_HELP)
        parser.add_argument('URL', default='www.python.org', help='server host')
        args = parser.parse_args(argv[2:])

        self.url = args.URL
        self.headers = args.headers
        self.verbose = args.verbose
        
        # Convert string headers into dict if exists
        if self.headers:
            self.convert_headers_to_dict()

        # Register information to create request messages and send GET request
        request_messages = HttpcRequests(url=self.url, headers=self.headers, verbose=self.verbose)
        request_messages.GET()


    def post(self):
        parser = argparse.ArgumentParser(prog='httpc', conflict_handler='resolve', usage=argparse.SUPPRESS, description=HttpcManuals.POST_HELP, epilog=HttpcManuals.POST_EPILOG, formatter_class=rtf)
        parser.add_argument('-v', '--verbose', action='store_true', help=HttpcManuals.V_HELP)
        parser.add_argument('-h', '--headers', action='append', metavar='key:value', default=[], help=HttpcManuals.H_HELP)
        parser.add_argument('-d', '--inline-data', metavar='string', type=str, help=HttpcManuals.D_HELP, dest='inline_data')
        parser.add_argument('-f', '--file', help=HttpcManuals.F_HELP, dest='file')
        parser.add_argument('URL', default='http://httpbin.org', help='server host')
        args = parser.parse_args(argv[2:])
        
        self.url = args.URL
        self.headers = args.headers
        self.verbose = args.verbose


    # Custom help CLI argument
    def help(self):
        parser = argparse.ArgumentParser(prog='httpc', conflict_handler='resolve', usage=argparse.SUPPRESS, add_help=False, description=HttpcManuals.HELP, epilog=HttpcManuals.HELP_EPILOG, formatter_class=rtf)
        parser.add_argument('command', nargs='?', default='help')
        args = parser.parse_args(argv[2:])
        if args.command == 'help':
            parser.print_help()
        elif args.command == 'get':
            print(HttpcManuals.GET_HELP_CUSTOM)
        elif args.command == 'post':
            print(HttpcManuals.POST_HELP_CUSTOM)
        else:
            print('httpc: error: unrecognized arguments:', args.command)
            print()
            parser.print_help()



if __name__ == '__main__':
    HTTPC()
