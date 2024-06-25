import socket
import json

# Define host and port
HOST = '127.0.0.1'
PORT = 5555

# Create a socket object
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to the server
client_socket.connect((HOST, PORT))
print("Connected to server...")

while True:
    # Take command input from user
    command = input("Enter command to execute (or 'exit' to quit): ")

    if command.lower() == 'exit':
        # Send exit request to server
        exit_request = {
            "command": "exit"
        }
        client_socket.send(json.dumps(exit_request).encode())
        break

    # Prepare command request
    command_request = {
        "command": command,
        "parameters": ""
    }

    # Send the command to the server
    client_socket.send(json.dumps(command_request).encode())

    # Receive and print the result from the server
    response = client_socket.recv(4096).decode()
    result = json.loads(response).get('result')
    print(result)

# Close the socket
client_socket.close()
