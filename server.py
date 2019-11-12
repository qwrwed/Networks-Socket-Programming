import sys      # cmd-line arguments
import os       # filesystem
import json     # list/dict serialisation
import re       # filename verification
import datetime # date, time

from socket import *

#TODO: Spaces in board titles should be replacedwith underscores(“_”).

def getCommandLineArgs(defaultServerAddress, defaultServerPort):
    if len(sys.argv) == 3:
        return (sys.argv[1], int(sys.argv[2]))
    else:
        return (defaultServerAddress, defaultServerPort)

def sendResponse(response, connectionSocket, successFlag = True):
    connectionSocket.send(json.dumps((response, successFlag)).encode())
    print("Response sent to client")
    
def getBoardList():
    return next(os.walk('.\\board'))[1]
    # Source: https://stackoverflow.com/a/142535

def getMessages(args):
    if args == None:
        return "ERROR: No arguments provided.", False
    try:
        boardName = args['boardName']
    except KeyError as e:
        return "ERROR: Missing parameter {}".format(e), False
    if boardName not in getBoardList():
        print(getBoardList())
        print(boardName)
        return "ERROR: Board \"{}\" does not exist.".format(boardName), False
    boardPath = '.\\board\\{}'.format(boardName)
    messageList = next(os.walk(boardPath))[2]
    messageList.sort()
    messageList = messageList[0:100]
    responseData = []
    for message in messageList:
        if re.search("[0-9]{8}-[0-9]{6}-.+\.txt", message) != None:
            f = open('{}\\{}'.format(boardPath, message), 'r')
            responseData.append([message, f.read()])
            f.close()
    return responseData, True

def postMessage(args, requestTimestamp):
    if args == None:
        return "ERROR: No arguments provided.", False
    try:
        boardName = args['boardName']
        if not boardName in getBoardList():
            return "ERROR: Board \"{}\" does not exist.".format(boardName), False
        boardPath = '.\\board\\{}'.format(boardName)
        messageTitle = args['postTitle']
        messageContent = args['messageContent']
    except KeyError as e:
        return "ERROR: Missing parameter {}".format(e), False
    fileTitle = requestTimestamp.strftime('%Y%m%d-%H%M%S') #YYYYMMDD-HHMMSS
    fileTitle += '-'
    fileTitle += '{}.txt'.format(messageTitle.replace(' ', '_'))
    
    f = open('{}\\{}'.format(boardPath, fileTitle), 'w+')
    f.write(messageContent)
    f.close()
    return "Message successfully posted.", True

def main():
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
    
    while True:
        print("Waiting for a client to connect")
        connectionSocket, addr = serverSocket.accept()
        print("Client connected", addr)
        request = json.loads(connectionSocket.recv(1024).decode())
        requestTimestamp = datetime.datetime.now()
        print("Message received from client: {}".format(request))
        requestType = request['requestType']
        args = request['args']
        if requestType == "GET_BOARDS":
            response, successFlag = getBoardList(), True
            sendResponse(response, connectionSocket, successFlag)
        elif requestType == "GET_MESSAGES":
            response, successFlag = getMessages(args)
            sendResponse(response, connectionSocket, successFlag)
        elif requestType == "POST_MESSAGE":
            response, successFlag = postMessage(args, requestTimestamp)
            sendResponse(response, connectionSocket, successFlag)
        else:
            successFlag = False
            sendResponse("ERROR: Request ({}) not recognised.".format(requestType), connectionSocket, False)
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
        
main()
