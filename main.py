import argparse
import server
import scanner
import time
import os
import socket

from threading import Thread
from enum import Enum

# Line command settings
F360_PATH = None
HOST = '127.0.0.1'
PORT = 3490

PR = None
HEADER_REGEX = None
WORKERS_SCANNER = 4
WORKERS_SERVER = 4
SUBMODULES = []
IGNORE_PATHS = []
CHECK = '-*,fusion-qwidget'
SCANNER_PATH = None
CMDS_PATH = None
TIDY_CONFIG_PATH = None
UPDATE_DASHBOARD = True

# Enum that describes working mode
class Mode(Enum):
    SERVER = 0
    CLIENT = 1
    BOTH = 2

MODE = Mode.BOTH # 0 = server
         # 1 = client
         # 2 = both

def main():
    argumentParser()
    serverThread = None
    scannerThread = None
    cwd_dir = os.getcwd()

    if MODE == Mode.SERVER or MODE == Mode.BOTH:
        print("Starting server thread...")
        serverThread = Thread(target=server.start_server, args=(cwd_dir, UPDATE_DASHBOARD,))
        serverThread.start()
        time.sleep(1) # Sleep for 1 second to ensure server is online before client sends data

    if MODE == Mode.CLIENT or MODE == Mode.BOTH:
        print("Starting scanner thread...")
        scannerThread = Thread(target=scanner.start_scanner, args=(F360_PATH, SCANNER_PATH, CMDS_PATH, TIDY_CONFIG_PATH, WORKERS_SCANNER, PR, SUBMODULES, IGNORE_PATHS, HEADER_REGEX))
        scannerThread.start()

    if scannerThread is not None:
        scannerThread.join()
        print("Joined scanner thread...")

        
        file_match = server.FileMatch(4, b'\x00' * 64, b'\x00' * 256, b'\x00' * 188)
        # use the below line instead of the above when we can find out the maximum lenght of string received from client
        #file_match = (b'\x00'* largestStringReceived)

        # Send shutdown package to server
        os.chdir(cwd_dir)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        sock.sendall(bytes(file_match))
        sock.close()

    if serverThread is not None:
        serverThread.join()
        print("Joined server thread...")

def argumentParser():                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   
    parser = argparse.ArgumentParser(
        description='Utility that runs Static Code Analysis and identifies the QWidgets classes for the Fusion360 project')
    parser.add_argument('--f360', required=True, help='Location of Fusion360 project')
    parser.add_argument('--scanner', required=True, help='Path to clang-static-analzer. Use default ~/clang-static-analyzer if not path is present.')
    parser.add_argument('--cmds', required=True, help='Specify compile commands file path.')
    parser.add_argument('--mode', choices={'server', 'scanner', 'both'}, help='selects the mode')
    parser.add_argument('--scan-pr', help='Scan Pull Request with given hash. Scan whole project if not hash is available.')
    parser.add_argument('--scan-submodule', help='Scan only listed submodules. Scan whole project if no submodules are present.')
    parser.add_argument('--ignore-paths', nargs='+', help='Ignore files that have paths specified in ignore list.')
    parser.add_argument('--header-filter-regex', help='Filter scanning of headers based on the provided regex.')
    parser.add_argument('--number-workers-scanner', help='Specify number of workers for clang-tidy.')
    parser.add_argument('--number-workers-server', help='Specify number of workers for server.')
    parser.add_argument('--tidy-config', help='Specify clang tidy config file path.')
    parser.add_argument('--update-dashboard', choices={'true', 'false'}, help='Upload statistics to Governance Dashboard.')

    args = parser.parse_args()

    global F360_PATH
    F360_PATH = args.f360

    global SCANNER_PATH
    SCANNER_PATH = args.scanner

    global CMDS_PATH
    CMDS_PATH = args.cmds

    # Parse mode
    global MODE
    
    if args.mode is not None:
        if args.mode == 'server':
            MODE = Mode.SERVER
        elif args.mode == 'client':
            MODE = Mode.CLIENT
        else:
            MODE = Mode.BOTH

    global PR
    if args.scan_pr is not None:
        PR = args.scan_pr

    global SUBMODULES
    if args.scan_submodule is not None:
        SUBMODULES = args.scan_submodule

    global IGNORE_PATHS
    if args.ignore_paths is not None:
        IGNORE_PATHS = args.ignore_paths

    global HEADER_REGEX
    if args.header_filter_regex is not None:
        HEADER_REGEX = args.header_filter_regex

    global WORKERS_SCANNER
    if args.number_workers_scanner is not None:
        WORKERS_SCANNER = args.number_workers_scanner

    global WORKERS_SERVER
    if args.number_workers_server is not None:
        WORKERS_SERVER = args.number_workers_server

    global TIDY_CONFIG_PATH
    if args.tidy_config is not None:
        TIDY_CONFIG_PATH = args.tidy_config

    global UPDATE_DASHBOARD
    if args.update_dashboard is not None:
        if args.update_dashboard == 'true':
            UPDATE_DASHBOARD = True
        else:
            UPDATE_DASHBOARD = False

if __name__ == "__main__":
    main()


