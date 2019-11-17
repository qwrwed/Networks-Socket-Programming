"""Client program for anonymous bulletin board system"""
import sys      # cmd-line arguments
import json     # list/dict serialisation
import datetime # date, time
import socket

def get_command_line_args(default_server_address, default_server_port):
    """determine address/port from command-line arguments, or default values otherwise"""
    if len(sys.argv) == 3:
        return (sys.argv[1], int(sys.argv[2]))
    return (default_server_address, default_server_port)

def make_request(server_info, request_type, args=None):
    """for each request, a new socket is opened, used and closed"""

    # send request, receive response, and handle errors:
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(server_info['timeout'])
        client_socket.connect(server_info['addr'])
        request = {'request_type': request_type, 'args' : args}
        client_socket.send(json.dumps(request).encode())
        [response, success_flag] = json.loads(client_socket.recv(2048).decode())
        client_socket.close()
    except ConnectionRefusedError:
        print("Error: Server unavailable. Exiting...")
        client_socket.close()
        sys.exit()
    except socket.timeout:
        print("Error: Connection timed out (limit {}s). Exiting...".format(server_info['timeout']))
        client_socket.close()
        sys.exit()

    # client must inform the user if command was successful or not:
    if success_flag:
        print("Command \"{}\" successful".format(request_type))
    else:
        print("Command \"{}\" unsuccessful".format(request_type))
    return response, success_flag

def show_board_list(board_list):
    """convert received board array into user-friendly format"""
    board_list_string = 'BOARD LIST:\n'
    delimiter_string = '\n'
    board_count = len(board_list)
    for i in range(board_count):
        board_list_string += "{}. {}".format(str(i), board_list[i]).replace("_", " ")
        # add delimiter after every element except the last one
        if i < len(board_list)-1:
            board_list_string += delimiter_string
    board_list_string += '\n'
    print(board_list_string)

def parse_file_title(file_title):
    """parsing operations for file title"""
    # convert YYYYMMDD-HHMMSS to YYYY/MM/DD HH/MM/SS in date component:
    datetime_object = datetime.datetime.strptime(file_title[:15], '%Y%m%d-%H%M%S')
    date_string = datetime_object.strftime('%Y/%m/%d %H:%M:%S')
    # convert underscores to spaces in title component
    message_title = file_title[16:-4].replace('_', ' ')
    return date_string, message_title

def show_message_list(board_name, file_list):
    """convert received list of messages to user-friendly format"""
    file_count = len(file_list)
    if file_count == 0:
        print('No messages to show for board \"{}\".\n'.format(board_name))
        return
    delimiter_string = '====\n'

    message_list_string = "Showing most recent {} message(s)".format(file_count)
    message_list_string += "for board \"{}\":\n\n".format(board_name)
    for i in range(file_count):
        file_title, file_content = file_list[i][0], file_list[i][1]
        # convert data to user-friendly format:
        message_date, message_title = parse_file_title(file_title)
        message_list_string += 'Title: {}\n'.format(message_title)
        message_list_string += 'Date: {}\n'.format(message_date)
        message_list_string += 'Content: {}\n'.format(file_content)
        if i < file_count-1:
            # add delimiter after every element except the last one
            message_list_string += delimiter_string
    print(message_list_string)

def main():
    """main function"""
    # variables
    default_server_address = '127.0.0.1'
    default_server_port = 12000
    socket_timeout = 30

    # define server info and make initial request for boards
    server_info = {}
    server_info['addr'] = get_command_line_args(default_server_address, default_server_port)
    server_info['timeout'] = socket_timeout

    response, success_flag = make_request(server_info, 'GET_BOARDS')

    # error checking
    if success_flag:
        board_list = response
        show_board_list(board_list)
    else:
        print(response)
        print("Board retrieval failed; Exiting program")
        return

    # get and act on user's input until quit
    while True:
        print('OPTIONS (case-sensitive):')
        print('Type a board number to show the most recent messages in that board.')
        print('Type \"POST\" to create a new message.')
        print('Type \"QUIT\" to quit.')
        user_choice = input('Input: ')
        print()
        if user_choice == 'QUIT':
            print("Ending process...")
            sys.exit()
        if user_choice.isnumeric() and int(user_choice) in range(len(board_list)):
            # convert user-input board number to server-required board name:
            board_name = board_list[int(user_choice)]
            # define arguments, make request, and act on result:
            args = {'board_name': board_name}
            response, success_flag = make_request(server_info, "GET_MESSAGES", args)
            if success_flag:
                file_list = response
                show_message_list(board_name, file_list)
            else:
                print(response)
            input('Press Enter to continue.')
        elif user_choice == 'POST':
            # define arguments, make request, and act on result:
            try:
                # convert user-input board number to server-required board name:
                board_number = int(input('Enter number of board to post message on: '))
                args = {'board_name': board_list[board_number]}
            except (IndexError, ValueError):
                input("Error: Invalid board number. Press Enter to continue.")
                print()
                continue
            args['post_title'] = input('Enter post title: ')
            args['message_content'] = input('Enter message content: ')
            response, success_flag = make_request(server_info, "POST_MESSAGE", args)
            print(response)
            input('Press Enter to continue.')
        else:
            # error checking
            input('User input not recognised. Press Enter to continue.')
        print()

if __name__ == "__main__":
    main()
