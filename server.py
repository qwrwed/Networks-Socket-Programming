import sys      # cmd-line arguments
import os       # filesystem
import json     # list/dict serialisation
import re       # filename verification
import datetime # date, time

from socket import *

if len(sys.argv) == 3:
    serverAddress, serverPort = sys.argv[1], int(sys.argv[2])
else:
    serverAddress, serverPort = '127.0.0.1', 12000

def getBoardList():
    return next(os.walk('.\\board'))[1]
    # Source: https://stackoverflow.com/a/142535

def getMessages(boardName):
    boardPath = '.\\board\\{}'.format(boardName)
    messageList = next(os.walk(boardPath))[2]
    messageList.sort()
    messageList = messageList[0:100]
    response = []
    for message in messageList:
        if re.search("[0-9]{8}-[0-9]{6}-.+\.txt", message) != None:
            f = open('{}\\{}'.format(boardPath, message), 'r')
            response.append([message, f.read()])
            f.close()
    return response

def postMessage(args):
    boardName = args['boardName']
    boardPath = '.\\board\\{}'.format(boardName)
    messageTitle = args['postTitle']
    messageContent = args['messageContent']
    #TODO: Verify board name
    messageDate = datetime.datetime.now()
    fileTitle = ''
    fileTitle += messageDate.strftime('%Y%m%d-%H%M%S')
    fileTitle += '-'
    fileTitle += '{}.txt'.format(messageTitle.replace(' ', '_'))
    
    f = open('{}\\{}'.format(boardPath, fileTitle), 'w+')
    f.write(messageContent)
    f.close()
    
    

def startListening():
    serverSocket = socket(AF_INET,SOCK_STREAM)
    serverSocket.bind((serverAddress, serverPort))
    serverSocket.listen(1)
    i = 0
    while True:
        print('Waiting for client connection...')
        connectionSocket, addr = serverSocket.accept()
        while True:
            print('Waiting on client message...')
            print(i)
            i += 1
            rawRequest = connectionSocket.recv(1024)
            print("Raw request:", rawRequest)
            request = json.loads(rawRequest.decode())
            requestType = request['requestType']
            print("Request recieved from client: \"{}\"".format(requestType))
            if 'args' in request:
                args = request['args']
                print("Arguments: {}".format(args))
            if requestType == 'GET_BOARDS':
                print('Sending board list to client.')
                response = getBoardList()
                connectionSocket.send(json.dumps(response).encode())
            elif requestType == 'GET_MESSAGES':
                boardName = args['boardName']
                print('Sending latest messages to client for board "{}"'.format(boardName))
                response = getMessages(boardName)
                connectionSocket.send(json.dumps(response).encode())
            elif requestType == 'QUIT':
                print('Closing connection to client.')
                connectionSocket.send('Closing connection to client.'.encode())
                connectionSocket.close()
                break
            elif requestType == 'POST_MESSAGE':
                postMessage(args)
                response = 'Message posting finished'
                connectionSocket.send(json.dumps(response).encode())
            else:
                errorString = 'Client request {} not recognised'.format(requestType)
                print(errorString)
                response = errorString
                connectionSocket.send(json.dumps(response).encode())

startListening()
