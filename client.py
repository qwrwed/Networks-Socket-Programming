import sys      # cmd-line arguments
import json     # list/dict serialisation
import datetime # date, time
from socket import *

def getCommandLineArgs(defaultServerAddress, defaultServerPort):
    # determine address/port from command-line arguments, or default values otherwise:
    if len(sys.argv) == 3:
        return (sys.argv[1], int(sys.argv[2]))
    else:
        return (defaultServerAddress, defaultServerPort)
    
def makeRequest(serverInfo, requestType, args = None):
    # new socket opened, used and closed for each new request:

    # send request, receive response, and handle errors:
    try:
        clientSocket = socket(AF_INET, SOCK_STREAM)
        clientSocket.settimeout(serverInfo['timeout'])
        clientSocket.connect(serverInfo['addr'])
        request = {'requestType': requestType, 'args' : args}
        clientSocket.send(json.dumps(request).encode())
        [response, successFlag] = json.loads(clientSocket.recv(1024).decode())
        clientSocket.close()
    except ConnectionRefusedError:
        print("Error: Server unavailable. Exiting...")
        clientSocket.close()
        sys.exit()
    except timeout:
        print("Error: Connection timed out (no response within {}s). Exiting...".format(serverInfo[1]))
        clientSocket.close()
        sys.exit()

    # client must inform the user if command was successful or not:
    if successFlag == True:
        print("Command \"{}\" successful".format(requestType))
    else:
        print("Command \"{}\" unsuccessful".format(requestType))
    return response, successFlag

def showBoardList(boardList):
    # convert received board array into user-friendly format:
    boardListString = 'BOARD LIST:\n'
    delimiterString = '\n'
    for i in range(len(boardList)):
        boardListString += "{}. {}".format(str(i), boardList[i])
        # add delimiter after every element except the last one
        if i < len(boardList)-1:
            boardListString += delimiterString
    boardListString += '\n'
    print(boardListString)

def parseFileTitle(fileTitle):
    # convert YYYYMMDD-HHMMSS to YYYY/MM/DD HH/MM/SS in date component:
    datetimeObject = datetime.datetime.strptime(fileTitle[:15],'%Y%m%d-%H%M%S')
    dateString = datetimeObject.strftime('%Y/%m/%d %H:%M:%S')
    # convert underscores to spaces in title component
    messageTitle = fileTitle[16:-4].replace('_', ' ')
    return dateString, messageTitle

def showMessageList(boardName, fileList):
    fileCount = len(fileList)
    if fileCount == 0:
        print('No messages to show for board \"{}\".\n'.format(boardName))
        return
    delimiterString = '====\n'
    messageListString = 'Showing most recent {} message(s) for board \"{}\":\n\n'.format(fileCount, boardName)
    for i in range(fileCount):
        fileTitle, fileContent = fileList[i][0], fileList[i][1] # unpack title and content from received list
        # convert data to user-friendly format:
        messageDate, messageTitle = parseFileTitle(fileTitle)
        messageListString += 'Title: {}\n'.format(messageTitle)
        messageListString += 'Date: {}\n'.format(messageDate)
        messageListString += 'Content: {}\n'.format(fileContent)
        if i < fileCount-1:
            # add delimiter after every element except the last one
            messageListString += delimiterString
    print(messageListString)

    
def main():
    # variables
    defaultServerAddress = '127.0.0.1'
    defaultServerPort = 12000
    socketTimeout = 10

    # define server info and make initial request for boards
    serverInfo = {'addr': getCommandLineArgs(defaultServerAddress, defaultServerPort), 'timeout': socketTimeout}
    response, successFlag = makeRequest(serverInfo, 'GET_BOARDS')

    # error checking
    if successFlag == True:
        boardList = response
        showBoardList(boardList)
    else:
        print(response)
        print("Board retrieval failed; Exiting program")
        return

    # get and act on user's input until quit
    while True:    
        print('OPTIONS (case-sensitive):')
        print('Type a board number ({}-{}) to show the 100 most recent messages in the specified board.'.format(0, len(boardList)-1))
        print('Type \"POST\" to create a new message.')
        print('Type \"QUIT\" to quit.')
        userChoice = input('Input: ')
        print()
        if userChoice == 'QUIT':
            break
        elif userChoice.isnumeric() and int(userChoice) in range(len(boardList)):
            # convert user-input board number to server-required board name:
            boardName = boardList[int(userChoice)]
            # define arguments, make request, and act on result:
            args = {'boardName': boardName}
            response, successFlag = makeRequest(serverInfo, "GET_MESSAGES", args)
            if successFlag == True:
                fileList = response
                showMessageList(boardName, fileList)
            else:
                print(response)
            input('Press Enter to continue.')
            print()
        elif userChoice == 'POST':
            # define arguments, make request, and act on result:
            args = {}
            try:
                # convert user-input board number to server-required board name:
                boardNumber = int(input('Enter number of board to post message on: '))
                args['boardName'] = boardList[boardNumber]
            except (IndexError, ValueError):
                print("Error: Invalid board number.")
                input('Press Enter to continue.')
                print()
                continue
            args['postTitle'] = input('Enter post title: ')
            args['messageContent'] = input('Enter message content: ')
            response, successFlag = makeRequest(serverInfo, "POST_MESSAGE", args)
            print(response)
            input('Press Enter to continue.')
            print()
        else:
            # error checking
            input('User input not recognised. Press Enter to continue.')
            print()
    
main()
