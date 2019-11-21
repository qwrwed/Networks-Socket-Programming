"""Server program for anonymous bulletin board system"""
import sys      # cmd-line arguments
import json     # list/dict serialisation
import datetime # date, time
import os       # filesystem
import re       # file_name verification
import socket
import threading



def get_command_line_args(default_server_address, default_server_port):
    """determine address/port from command-line arguments, or default values otherwise"""
    if len(sys.argv) == 3:
        return (sys.argv[1], int(sys.argv[2]))
    return (default_server_address, default_server_port)

def send_response(response, connection_socket, success_flag=True, show_response=True):
    """
    for all responses, combine with a success/failure flag,
    convert to JSON and encode before sending
    """
    connection_socket.send(json.dumps((response, success_flag)).encode())
    info_string = "Response sent to client"
    if show_response:
        info_string += ": \n{}".format(response)
    else:
        info_string += "."
    print(info_string)

def get_board_list():
    """list all directories(boards) in folder"""
    return sorted([f for f in os.listdir('./board') if not f.startswith('.')], key=str.lower)
    #source: https://stackoverflow.com/a/26554941


def get_messages(args):
    """create and return a list of messages for the specified board"""
    # error handling for missing parameter(s) or nonexistent board:
    if args is None:
        return "ERROR: No parameters provided.", False
    try:
        board_name = args['board_name']
    except KeyError as error:
        return "ERROR: Missing parameter {}".format(error), False
    if board_name not in get_board_list():
        return "ERROR: Board \"{}\" does not exist.".format(board_name), False

    board_path = './board/{}'.format(board_name)
    message_list = next(os.walk(board_path))[2] # list all files (messages) in folder
    # source: https://stackoverflow.com/a/142535
    message_list.sort() # ordered alphanumerically by name (and therefore ordered by date)
    message_list = message_list[-100:] # 100 most recent messages

    # construct a list of title-content arrays, but only from files that follow naming convention:
    response_data = []
    for message_title in message_list:
        if re.search("[0-9]{8}-[0-9]{6}-.+[.]txt", message_title) is not None:
            file = open('{}/{}'.format(board_path, message_title), 'r')
            message_content = file.read()
            response_data.append([message_title, message_content])
            file.close()
    return response_data, True

def post_message(args, request_timestamp):
    """create a new message file in the specified board with the specified data"""
    # error handling for missing parameter(s) or nonexistent board:
    if args is None:
        return "ERROR: No parameters provided.", False
    try:
        board_name = args['board_name']
        if not board_name in get_board_list():
            return "ERROR: Board \"{}\" does not exist.".format(board_name), False
        board_path = './board/{}'.format(board_name)
        message_title = args['post_title']
        message_content = args['message_content']
    except KeyError as error:
        return "ERROR: Missing parameter {}".format(error), False
    # create file_name from timestamp and title:
    file_name = request_timestamp.strftime('%Y%m%d-%H%M%S') #YYYYMMDD-HHMMSS
    file_name += '-'
    file_name += '{}.txt'.format(message_title.replace(' ', '_'))
    # create and write to file:
    file = open('{}/{}'.format(board_path, file_name), 'w+')
    file.write(message_content)
    file.close()
    return "Message successfully posted.", True

def handle_connection(connection_socket, addr):
    """handle the connection in its own thread for simultaneous clients"""
    print("Client connected: ", addr)
    request = json.loads(connection_socket.recv(2048).decode())
    request_timestamp = datetime.datetime.now()
    print("Message received from client: {}".format(request))
    request_type = request['request_type']
    args = request['args']
    if request_type == "GET_BOARDS":
        response, success_flag = get_board_list(), True
        # will always be successful as message boards have been confirmed to be defined
        send_response(response, connection_socket, success_flag)
    elif request_type == "GET_MESSAGES":
        response, success_flag = get_messages(args)
        send_response(response, connection_socket, success_flag, False)
    elif request_type == "POST_MESSAGE":
        response, success_flag = post_message(args, request_timestamp)
        send_response(response, connection_socket, success_flag)
    else:
        success_flag = False
        response = "ERROR: Request ({}) not recognised.".format(request_type)
        send_response(response, connection_socket, success_flag)
    print()
    # record details in server.log
    log_line = ""
    log_line += (addr[0] + ":" + str(addr[1]))
    log_line += "\t\t"
    log_line += request_timestamp.strftime('%Y/%m/%d %H:%M:%S')
    log_line += "\t\t"
    log_line += format(request_type, '<12')
    log_line += "\t\t"
    log_line += {True: "OK", False: "Error"}[success_flag]
    log_line += "\n"
    file = open("server.log", 'a+')
    file.write(log_line)
    file.close()


def handle_main_thread(server_socket):
    """accepts client connections and opens a new thread for each"""
    server_socket.listen(1)
    print("Initialisation finished - now listening...")
    while True:
        c_sckt, addr = server_socket.accept()
        connection_handler = threading.Thread(target=handle_connection, args=(c_sckt, addr))
        connection_handler.start()

def main():
    """main function: initialise server socket and start main thread"""
    # variables:
    default_server_address = '127.0.0.1'
    default_server_port = 12000

    # ensure message boards are defined:
    if not os.path.isdir('./board'):
        print("Board folder is missing. Ending process...")
        return
    if len(get_board_list()) == 0:
        print("No boards defined. Ending process...")
        return

    # attempt to create server socket:
    server_info = get_command_line_args(default_server_address, default_server_port)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind(server_info)
    except OSError:
        print("ERROR: Unavailable/busy port. Ending process...")
        return

    # create a seperate thread for server_socket.accept() so it can be stopped by KeyboardInterrupt:
    main_thread = threading.Thread(target=handle_main_thread, args=(server_socket,))
    # set thread as daemon so that it can be stopped by sys.exit():
    main_thread.daemon = True
    while True:
        try:
            if not main_thread.isAlive():
                main_thread.start()
        except KeyboardInterrupt:
            print("KeyboardInterrupt received. Ending process...\n")
            sys.exit()


if __name__ == "__main__":
    main()
