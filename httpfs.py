import argparse
from argparse import RawTextHelpFormatter as rtf
from console_messages import HttpfsManuals
from libhttpfs import run_server

class HTTPFS:
    def __init__(self):
        self.verbose = False
        self.port = 8007  # DEFAULT PORT
        self.directory = ''

        parser = argparse.ArgumentParser(prog='httpfs', conflict_handler='resolve', usage=argparse.SUPPRESS, description=HttpfsManuals.HELP, formatter_class=rtf)
        parser.add_argument('-v', '--verbose', action='store_true', help=HttpfsManuals.V_HELP)
        parser.add_argument('-p', '--port', type=int, default=self.port, help=HttpfsManuals.P_HELP)
        parser.add_argument('-d', '--directory', type=str, help=HttpfsManuals.D_HELP)
        args = parser.parse_args()

        self.verbose = args.verbose
        self.port = args.port
        self.directory = args.directory

        run_server('', self.port, self.directory, self.verbose)

if __name__ == '__main__':
    args = HTTPFS()
    print(args.verbose, args.port, args.directory)
    print()
