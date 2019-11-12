import sys      # cmd-line arguments
import json     # list/dict serialisation
import datetime # date, time
import os       # filesystem
import re       # filename verification
from socket import *

#TODO: Clarify Spaces in board titles should be replacedwith underscores(“_”).

def getCommandLineArgs(defaultServerAddress, defaultServerPort):
    # determine address/port from command-line arguments, or default values otherwise:
    if len(sys.argv) == 3:
        return (sys.argv[1], int(sys.argv[2]))
    else:
        return (defaultServerAddress, defaultServerPort)

def sendResponse(response, connectionSocket, successFlag = True, showResponse = True):
    # all responses are combined with a success/failure flag, converted to JSON and encoded:
    connectionSocket.send(json.dumps((response, successFlag)).encode())
    infoString = "Response sent to client"
    if showResponse == True:
        infoString += ": \n{}".format(response)
    else:
        infoString += "."
    print(infoString)
    
def getBoardList():
    return next(os.walk('.\\board'))[1]
    # list all directories(boards) in folder
    # source: https://stackoverflow.com/a/142535

def getMessages(args):
    # error handling for missing parameter(s) or nonexistent board:
    if args == None:
        return "ERROR: No parameters provided.", False
    try:
        boardName = args['boardName']
    except KeyError as e:
        return "ERROR: Missing parameter {}".format(e), False
    if boardName not in getBoardList():
        return "ERROR: Board \"{}\" does not exist.".format(boardName), False
    
    boardPath = '.\\board\\{}'.format(boardName)
    messageList = next(os.walk(boardPath))[2] # list all files (messages) in folder
    messageList.sort() # ordered alphanumerically by name (and therefore ordered by date)
    messageList = messageList[0:100] # 100 most recent messages

    # construct a list of title-content arrays, but only from files that follow naming convention:
    responseData = []
    for messageTitle in messageList:
        if re.search("[0-9]{8}-[0-9]{6}-.+\.txt", messageTitle) != None:
            f = open('{}\\{}'.format(boardPath, messageTitle), 'r')
            messageContent = f.read()
            responseData.append([messageTitle, messageContent])
            f.close()
    return responseData, True

def postMessage(args, requestTimestamp):
    # error handling for missing parameter(s) or nonexistent board:
    if args == None:
        return "ERROR: No parameters provided.", False
    try:
        boardName = args['boardName']
        if not boardName in getBoardList():
            return "ERROR: Board \"{}\" does not exist.".format(boardName), False
        boardPath = '.\\board\\{}'.format(boardName)
        messageTitle = args['postTitle']
        messageContent = args['messageContent']
    except KeyError as e:
        return "ERROR: Missing parameter {}".format(e), False
    # create filename from timestamp and title:
    fileName = requestTimestamp.strftime('%Y%m%d-%H%M%S') #YYYYMMDD-HHMMSS
    fileName += '-'
    fileName += '{}.txt'.format(messageTitle.replace(' ', '_'))
    # create and write to file:
    f = open('{}\\{}'.format(boardPath, fileName), 'w+')
    f.write(messageContent)
    f.close()
    return "Message successfully posted.", True

def main():
    # variables:
    defaultServerAddress = '127.0.0.1'
    defaultServerPort = 12000
    
    # ensure message boards are defined:
    if not os.path.isdir('.\\board'):
        print("Board folder is missing. Ending process...")
        return
    elif len(getBoardList()) == 0:
        print("No boards defined. Ending process...")
        return

    # attempt to create server socket
    serverInfo = getCommandLineArgs(defaultServerAddress, defaultServerPort)
    serverSocket = socket(AF_INET,SOCK_STREAM)
    try:
        serverSocket.bind(serverInfo)
    except OSError:
        print("ERROR: Unavailable/busy port. Ending process...")
        return
    serverSocket.listen(1)
    print("Initialisation finished - starting listening...")

    # handle client requests:
    while True:
        print("Waiting for a client to connect...")
        connectionSocket, addr = serverSocket.accept()
        print("Client connected: ", addr)
        request = json.loads(connectionSocket.recv(1024).decode())
        requestTimestamp = datetime.datetime.now()
        print("Message received from client: {}".format(request))
        requestType = request['requestType']
        args = request['args']
        if requestType == "GET_BOARDS":
            response, successFlag = getBoardList(), True
            # will always be successful when message boards are defined; this has already been verified
            sendResponse(response, connectionSocket, successFlag)
        elif requestType == "GET_MESSAGES":
            response, successFlag = getMessages(args)
            sendResponse(response, connectionSocket, successFlag, False)
        elif requestType == "POST_MESSAGE":
            response, successFlag = postMessage(args, requestTimestamp)
            sendResponse(response, connectionSocket, successFlag)
        else:
            successFlag = False
            sendResponse("ERROR: Request ({}) not recognised.".format(requestType), connectionSocket, successFlag)
        print()
        # record details in server.log
        logLine = ""
        logLine += (addr[0] + ":" + str(addr[1]))
        logLine += "\t\t"
        logLine += requestTimestamp.strftime('%Y/%m/%d %H:%M:%S')
        logLine += "\t\t"
        logLine += format(requestType, '<12')
        logLine += "\t\t"
        logLine += {True: "OK", False: "Error"}[successFlag]
        logLine += "\n"
        f = open("server.log", 'a+')
        f.write(logLine)
        f.close()
        
if __name__ == "__main__":
    main()
