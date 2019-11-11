import sys
import json
from socket import *

def getCommandLineArgs(defaultServerAddress, defaultServerPort):
    if len(sys.argv) == 3:
        return sys.argv[1], int(sys.argv[2])
    else:
        return defaultServerAddress, defaultServerPort

def showBoardList(boardList):
    boardListString = 'BOARD LIST:\n'
    delimiterString = '\n'
    for i in range(len(boardList)):
        boardListString += "{}. {}".format(str(i), boardList[i])
        if i < len(boardList)-1:
            boardListString += delimiterString
    boardListString = '\n'
    print(boardListString)

def parseFileTitle(fileTitle):
    #YYYYMMDD-HHMMSS -> YYYY/MM/DD HH/MM/SS
    dateStringList = list(fileTitle[:15].replace('-', ' '))
    dateStringList.insert(4, '/')
    dateStringList.insert(7, '/')
    dateStringList.insert(13, ':')
    dateStringList.insert(16, ':')
    messageTitle = fileTitle[16:-4].replace('_', ' ')
    return ''.join(dateStringList), messageTitle
    
    
def showMessageList(boardName, fileList):
    fileCount = len(fileList)
    if fileCount == 0:
        print('No messages to show for board \"{}\".\n'.format(boardName))
        return
    delimiterString = '====\n'
    messageListString = 'Showing most recent {} message(s) for board \"{}\":\n\n'.format(fileCount, boardName)
    #messageListString += delimiterString
    for i in range(fileCount):
        fileTitle, fileContent = fileList[i][0], fileList[i][1]
        
        messageDate, messageTitle = parseFileTitle(fileTitle)
        
        messageListString += 'Title: {}\n'.format(messageTitle)
        messageListString += 'Date: {}\n'.format(messageDate)
        messageListString += 'Content: {}\n'.format(fileContent)
        if i < fileCount-1:
            messageListString += delimiterString
    print(messageListString)

def disconnect(clientSocket):
    request = {'requestType': 'QUIT'}
    clientSocket.send(json.dumps(request).encode())
    response = clientSocket.recv(1024)
    print('Message from server:', response.decode())
    clientSocket.close()

def main():
    # variables
    socketTimeout = 5
    defaultServerAddress = '127.0.0.1'
    defaultServerPort = 12000

    serverAddress, serverPort = getCommandLineArgs(defaultServerAddress, defaultServerPort)
    print('Setting up connection to server at address {}, port {}...'.format(serverAddress, serverPort))
    
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.settimeout(socketTimeout)
    
    try:
        clientSocket.connect((serverAddress, serverPort))
    except ConnectionRefusedError:
        print('ERROR: Connection refused; server is unavailable. Exiting...')
        return
    except timeout:
        print('ERROR: Connection timed out (no response from server within {}s). Exiting...'.format(socketTimeout))
        return
    
    request = {'requestType': 'GET_BOARDS'}
    clientSocket.send(json.dumps(request).encode())
    encodedResponse = clientSocket.recv(1024)
    response = json.loads(encodedResponse.decode())
    if type(response) == list:
        boardList = response
        showBoardList(boardList)
    else:
        print('Error from server: {}.\nDisconnecting...'.format(response))
        disconnect(clientSocket)
        print("Exiting...")
        return

    while True:
        print('OPTIONS (case-sensitive):')
        print('Type a number {}-{} to show the 100 most recent messages in the specified board.'.format(0, len(boardList)-1))
        print('Type \"POST\" to create a new message.')
        print('Type \"QUIT\" to quit.')
        userChoice = input('Input: ')
        print()
        if userChoice == 'QUIT':
            disconnect(clientSocket)
            break
        elif userChoice.isnumeric() and int(userChoice) in range(len(boardList)):
            args = {}
            boardName = boardList[int(userChoice)]
            args['boardName'] = boardName
            request = {'requestType': 'GET_MESSAGES', 'args': args}
            clientSocket.send(json.dumps(request).encode())
            response = clientSocket.recv(1024)
            fileList = json.loads(response.decode())
            showMessageList(boardName, fileList)
            input('Press Enter to continue.')
            print()
        elif userChoice == 'POST':
            args = {}
            boardNumber = int(input('Enter number of board to post message on: '))
            args['boardName'] = boardList[boardNumber]
            args['postTitle'] = input('Enter post title: ')
            args['messageContent'] = input('Enter message content: ')
            request = {'requestType': 'POST_MESSAGE', 'args': args}
            clientSocket.send(json.dumps(request).encode())
            response = clientSocket.recv(1024)
            print('server says:', response.decode())
        else:
            input('User input not recognised. Press Enter to continue.')
main()
