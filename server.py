import socket
import threading
import ctypes
import sqlite3
import updateDatabase
import os
import sys
from dashboard_sender import send_to_dashboard

shutdown_server = False     # When True, server will shutdown
cwd_dir = ""
server_socket = socket.socket()
max_timeouts = 5
timeout_limit = 5

sql_table_to_connect_to = 'AFFECTED_FILES'

class FileMatch(ctypes.Structure):
    _fields_ = [
        ("operation",   ctypes.c_uint32),
        ("entityName",   ctypes.c_char * 64),
        ("filePath",    ctypes.c_char * 256),
        ("_reserved",   ctypes.c_char * 188)
    ]

operationMap = {0: "Derived", 1 : "Variable", 2 : "Field"}

def create_or_connect_to_database():
    global sql_table_to_connect_to

    print("create_database")
    conn = sqlite3.connect(cwd_dir + "/test.db")
    c = conn.cursor()
    c.execute('''Select count(name) FROM sqlite_master WHERE type='table' AND name='{tab}' '''.format(tab = sql_table_to_connect_to))

    if c.fetchone()[0] == 1:
        print("Pre-scanned table exists, creating table for new ocurrences")
        sql_table_to_connect_to = 'MODIFIED_OCURRENCES'
    else:
        print("Pre-scanned table is not exist, creating")

    conn.execute('''DROP TABLE IF EXISTS {tab}; '''.format(tab = sql_table_to_connect_to))
    conn.execute('''CREATE TABLE {tab}
                    (FILE_PATH TEXT NOT NULL,
                    ENTITY_NAME TEXT NOT NULL,
                    OPERATION TEXT NOT NULL,
                    LINE TEXT NOT NULL,
                    UNIQUE (FILE_PATH, ENTITY_NAME, OPERATION, LINE)); '''.format(tab = sql_table_to_connect_to))

    print("Table created successfulyy")
    c.close()

# Decodes data
def decode_data(sql_connection, data):
    global shutdown_server
    dataReceived = data

    size = len(dataReceived.decode('utf-8').split(','))
    if not dataReceived or size < 3:
        shutdown_server = True
        return
    
    isWin = sys.platform == 'win32'

    filePathWithLine    = os.path.abspath(dataReceived.decode('utf-8')).split(',')[0]
    if isWin == True:
        filePath            = filePathWithLine.split(':')[0] + ':' + filePathWithLine.split(':')[1]
        line                = filePathWithLine.split(':')[2]
    else:
        filePath            = filePathWithLine.split(':')[0]
        line                = filePathWithLine.split(':')[1]
    entityName          = dataReceived.decode('utf-8').split(',')[1]
    operationType       = int(dataReceived.decode('utf-8').split(',')[2])
    operation           = operationMap[operationType] if 0 <= operationType <= 2 else ""

    
    print("Processing occurence: " + filePath + ":" + line + "\n"
        + "entityName: " + entityName + "\n"
        + "operation: " + operation)

    # Adding entry to SQL Database
    sql_connection.execute("INSERT INTO " + sql_table_to_connect_to  + " (FILE_PATH, ENTITY_NAME, OPERATION, LINE) values (?, ?, ?, ?)",(filePath, entityName, operation, line))
    sql_connection.commit()
    
    print("Records added successfully to the table")

def client_handler(connection):
    #connection.send(str.encode('You are now connected to the server...'))

    # Establish connection to SQL Database
    sql_connection = sqlite3.connect(cwd_dir + "/test.db")

    while True:
        try:
            # Receive ctype structure with size of 512 bytes
            data = connection.recv(512)
            
            # If data is empty, then client closed connection
            if not data:
                break

            # Decode data and reset timeout_counter
            decode_data(sql_connection, data)
            timeout_counter = max_timeouts

            if shutdown_server is True:
                break

        # Close connection to client after MAX_TIMEOUT (5) timeouts consecutively
        except socket.timeout:
            timeout_counter = timeout_counter - 1
            if timeout_counter == 0:
                break
            pass

        except sqlite3.IntegrityError as e:
            print("Entity is already in the database", e)
            pass

    # Close connection to SQL Database, close connection to client
    sql_connection.close()
    connection.close()

def start_server(cwd, update_server=True):
    global cwd_dir, server_socket
    
    cwd_dir = cwd
    client_threads = []

    # Make sure that socket is does not exist
    #try:
    #    os.unlink(sock_path)
    #except OSError:
    #    if os.path.exists(sock_path):
    #        raise

    # Init database
    create_or_connect_to_database()

    # Create Socket
    HOST = '127.0.0.1'
    PORT = 3490
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        server_socket.bind((HOST, PORT))
    except socket.error as e:
        print(str(e))
    
    server_socket.settimeout(timeout_limit)
    server_socket.listen(1)

    print(f"Server Socket is listening on HOST:{HOST}" + ", PORT:", PORT)
    # Accept clients, create new thread for each incoming client
    while True:
        try:
            Client, address = server_socket.accept()
            print("Connection: " + str(Client))

            thread = threading.Thread(target=client_handler, args=(Client, ))
            thread.start()
            client_threads.append(thread)

        # Continue execution until server shutdown message is received
        except socket.timeout:
            pass

        # Print other exceptions, hoping it does not get here
        except Exception as e:
            print("Except: ", e)
            break

        # Break if shutdown was initialisez
        if shutdown_server is True:
            break

    # Wait for threads to finish sending
    for thread in client_threads:
        thread.join()
    
    # Close server socket
    server_socket.close()

    print("Upload statistics to Governance Dashboard: " + str(update_server))
    if update_server == True:
        send_result_to_dashboard()

    #updateDatabase.update()

def send_result_to_dashboard():
    conn = sqlite3.connect(cwd_dir + "/test.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM AFFECTED_FILES")
    qwidget_occurances = cursor.fetchone()[0]
    # Print the count
    print("Number of entries in the AFFECTED_FILES table:", qwidget_occurances)

    cursor_total_files_count = conn.cursor()
    cursor_total_files_count.execute("SELECT COUNT(DISTINCT(FILE_PATH)) FROM AFFECTED_FILES")
    qwidget_occurrence_files_count = cursor_total_files_count.fetchone()[0]
    # Print the file count
    print("Total number of files in which Qwidget is using:", qwidget_occurrence_files_count)

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    send_to_dashboard(qwidget_occurances, qwidget_occurrence_files_count)
