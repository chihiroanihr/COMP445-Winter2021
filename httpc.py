import argparse
from argparse import RawTextHelpFormatter as rtf
import sys
from httpc_manuals import HttpcManuals
from libhttpc import HttpcRequests

#print(HttpcManuals.LOGO)
#print(HttpcManuals.WELCOME)
#print(HttpcManuals.DESCRIPTION)

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
            print('httpc: error: unrecognized arguments:', args.command)
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
            print(f"File {file} not found.  Aborting")
            sys.exit(1)
        except OSError:
            print(f"OS error occurred trying to open {file}")
            sys.exit(1)
        except Exception as err:
            print(f"Unexpected error opening {file} is",repr(err))
            sys.exit(1)
        else:
            return True


    def get(self):
        parser = argparse.ArgumentParser(prog='httpc', conflict_handler='resolve', usage=argparse.SUPPRESS, description=HttpcManuals.GET_HELP, formatter_class=rtf)
        parser.add_argument('-v', '--verbose', action='store_true', help=HttpcManuals.V_HELP)
        parser.add_argument('-h', '--headers', action='append', metavar='key:value', default=[], help=HttpcManuals.H_HELP)
        parser.add_argument('URL', help='server host')
        parser.add_argument('-o', '--output', help=HttpcManuals.O_HELP)
        args = parser.parse_args(sys.argv[2:])

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
        parser.add_argument('-h', '--headers', action='append', metavar='key:value', default=[], help=HttpcManuals.H_HELP)
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
        
        # Convert string headers into dict if exists
        if self.headers:
            self.convert_headers_to_dict()
        
        if self.file:
            self.file_is_valid(self.file)   # validate file
        self.output_file = args.output
        
        if self.inline_data and self.file:  # both -d and -v cannot be used
            print("-d and -f cannot be used together")
            sys.exit(1)
            
        # Register information to create request messages and send POST request
        request_messages = HttpcRequests(url=self.url, headers=self.headers, inline_body=self.inline_data, file=self.file, verbose=self.verbose, output_file=self.output_file)
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
            print('httpc: error: unrecognized arguments:', args.command)
            print()
            parser.print_help()



if __name__ == '__main__':
    HTTPC()
