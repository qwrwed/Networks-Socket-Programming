import sys
import json
import datetime
from socket import *

def getCommandLineArgs(defaultServerAddress, defaultServerPort):
    if len(sys.argv) == 3:
        return (sys.argv[1], int(sys.argv[2]))
    else:
        return (defaultServerAddress, defaultServerPort)
    
def makeRequest(serverInfo, requestType, args = None):
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.settimeout(serverInfo[1])
    try:
        clientSocket.connect(serverInfo[0])
    except ConnectionRefusedError:
        print("Error: Server unavailable. Exiting...")
        sys.exit()
    request = {'requestType': requestType, 'args' : args}
    clientSocket.send(json.dumps(request).encode())
    try:
        [response, successFlag] = json.loads(clientSocket.recv(1024).decode())
    except timeout:
        print("Error: Connection timed out (no response within {}s). Exiting...".format(serverInfo[1]))
        clientSocket.close()
        sys.exit()
    clientSocket.close()
    if successFlag == True:
        print("Command \"{}\" successful".format(requestType))
    else:
        print("Command \"{}\" unsuccessful".format(requestType))
    return response, successFlag

def showBoardList(boardList):
    boardListString = 'BOARD LIST:\n'
    delimiterString = '\n'
    for i in range(len(boardList)):
        boardListString += "{}. {}".format(str(i), boardList[i])
        if i < len(boardList)-1:
            boardListString += delimiterString
    boardListString += '\n'
    print(boardListString)

def parseFileTitle(fileTitle):
    #YYYYMMDD-HHMMSS -> YYYY/MM/DD HH/MM/SS
    datetimeObject = datetime.datetime.strptime(fileTitle[:15],'%Y%m%d-%H%M%S')
    dateString = datetimeObject.strftime('%Y/%m/%d %H:%M:%S')
    messageTitle = fileTitle[16:-4].replace('_', ' ')
    return dateString, messageTitle

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

    
def main():
    defaultServerAddress = '127.0.0.1'
    defaultServerPort = 12000
    socketTimeout = 10

    serverInfo = [getCommandLineArgs(defaultServerAddress, defaultServerPort), socketTimeout]
    response, successFlag = makeRequest(serverInfo, 'GET_BOARDS')
    if successFlag == True:
        boardList = response
        showBoardList(boardList)
    else:
        print(response)
        print("Board retrieval failed; Exiting program")
        return
    
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
            boardName = boardList[int(userChoice)]
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
            args = {}
            try:
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
            input('User input not recognised. Press Enter to continue.')
            print()
#        res = makeRequest(serverInfo, 'ECHO', {'string': st})
#        print(res)
    
main()
