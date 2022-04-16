import argparse
from argparse import RawTextHelpFormatter as rtf
import sys
from utils.global_config import RequestMethod, INPUTS_DIR
from utils.console_messages import HttpcManuals
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

        parser = argparse.ArgumentParser(
            prog='httpc',
            conflict_handler='resolve',
            usage=argparse.SUPPRESS,
            description=HttpcManuals.HELP,
            epilog=HttpcManuals.HELP_EPILOG,
            formatter_class=rtf
        )
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
        self.headers = {header[0].strip():header[1].strip() for header in self.headers}


    def file_is_valid(self, file):
        try:
            open(file, 'rb')
        except FileNotFoundError:
            print(f"!!! httpc error: File {file} not found.  Aborting.")
            sys.exit(1)
        except OSError:
            print(f"!!! httpc error: Could not open/read file {file}. Aborting.")
            sys.exit(1)
        else:
            return True


    def get(self):
        parser = argparse.ArgumentParser(
            prog='httpc',
            conflict_handler='resolve',
            usage=argparse.SUPPRESS,
            description=HttpcManuals.GET_HELP,
            formatter_class=rtf
        )
        parser.add_argument(
            '-v',
            '--verbose',
            action='store_true',
            help=HttpcManuals.V_HELP
        )
        parser.add_argument(
            '-h',
            '--headers',
            action='extend',
            nargs='*',
            metavar='key:value',
            help=HttpcManuals.H_HELP
        )
        parser.add_argument(
            'URL',
            help='server host'
        )
        parser.add_argument(
            '-o',
            '--output',
            help=HttpcManuals.O_HELP
        )
        # sys.argv[0] = httpc.py, sys.argv[1] = get
        args = parser.parse_args(sys.argv[2:])

        self.url = args.URL
        self.headers = args.headers
        self.verbose = args.verbose
        self.output_file = args.output

        # Convert string headers into dict if exists
        if self.headers:
            self.convert_headers_to_dict()

        # Register information to create request messages and send GET request
        request = HttpcRequests(
            request_url=self.url,
            request_header=self.headers,
            verbose=self.verbose,
            output_file=self.output_file
        )
        request.request(RequestMethod.GET)


    def post(self):
        parser = argparse.ArgumentParser(
            prog='httpc',
            conflict_handler='resolve',
            usage=argparse.SUPPRESS,
            description=HttpcManuals.POST_HELP,
            epilog=HttpcManuals.POST_EPILOG,
            formatter_class=rtf
        )
        parser.add_argument(
            '-v',
            '--verbose',
            action='store_true',
            help=HttpcManuals.V_HELP
        )
        parser.add_argument(
            '-h',
            '--headers',
            action='extend',
            nargs='*',
            metavar='key:value',
            help=HttpcManuals.H_HELP
        )
        parser.add_argument(
            '-d',
            '--inline-data',
            metavar='string',
            help=HttpcManuals.D_HELP,
            dest='inline_data'
        )
        parser.add_argument(
            '-f',
            '--file',
            help=HttpcManuals.F_HELP,
            dest='file'
        )
        parser.add_argument(
            'URL',
            help='server host'
        )
        parser.add_argument(
            '-o',
            '--output',
            help=HttpcManuals.O_HELP
        )
        # sys.argv[0] = httpc.py, sys.argv[1] = post
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
            request = HttpcRequests(
                request_url=self.url,
                request_header=self.headers,
                post_inline_data=self.inline_data,
                post_input_file=self.file,
                verbose=self.verbose,
                output_file=self.output_file
            )
            request.request(RequestMethod.POST)


    # Custom help CLI argument
    def help(self):
        parser = argparse.ArgumentParser(
            prog='httpc',
            conflict_handler='resolve',
            usage=argparse.SUPPRESS,
            add_help=False,
            description=HttpcManuals.HELP,
            epilog=HttpcManuals.HELP_EPILOG,
            formatter_class=rtf
        )
        parser.add_argument(
            'command',
            nargs='?',
            default='help'
        )
        # sys.argv[0] = httpc.py, sys.argv[1] = help
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

# TODO: LA3
# python httpc.py --routerhost localhost --routerport 3000 --serverhost localhost --serverport 8007
# python httpc.py --routerhost localhost --routerport 3010 --serverhost localhost --serverport 8010
