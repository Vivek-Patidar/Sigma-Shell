import socket
import subprocess
import threading
import json
import os
import shutil
import psutil

# Dictionary to store connected clients
connected_clients = {}

def get_disk_usage(path):
    total_size = 0
    try:
        for dirpath, _, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
    except OSError as e:
        return f"Error: {e}"
    return total_size

def handle_client(client_socket, address):
    global connected_clients
    while True:
        try:
            # Receive command from client
            data = client_socket.recv(4096).decode()
            if not data:
                break
            
            # Parse JSON data
            try:
                message = json.loads(data)
                command = message.get('command')
                parameters = message.get('parameters')
            except json.decoder.JSONDecodeError:
                response = {"result": "Invalid JSON format. Please provide a valid JSON."}
                client_socket.send(json.dumps(response).encode())
                continue
            
            if command == 'exit':
                print(f"Connection with {address} closed by client.")
                del connected_clients[address]
                break

            # Execute the command
            try:
                if command == 'ls':
                    result = '\n'.join(os.listdir(parameters)) if parameters else '\n'.join(os.listdir())
            
                elif command.startswith('cd '):
                    directory = command.split(' ', 1)[1]  # Extract directory path
                    try:
                        os.chdir(directory)
                        result = f"Changed directory to: {os.getcwd()}"
                    except FileNotFoundError:
                        result = f"Directory not found: {directory}"
                    except PermissionError:
                        result = f"Permission denied: {directory}"
                
                elif command == 'cd..':
                    os.chdir('..')
                    result = f"Changed directory to parent directory: {os.getcwd()}"
                
                elif command == 'pwd':
                    result = os.getcwd()

                elif command.startswith('mkdir '):
                    new_directory = command.split(' ', 1)[1]  # Extract directory name
                    try:
                        os.mkdir(new_directory)
                        result = f"Directory created: {new_directory}"
                    except FileExistsError:
                        result = f"Directory already exists: {new_directory}"
                    except PermissionError:
                        result = f"Permission denied: {new_directory}"

                elif command.startswith('touch '):
                    filename = command.split(' ', 1)[1]  # Extract filename
                    with open(filename, 'a'):
                        os.utime(filename, None)
                    result = f"File created: {filename}"

                elif command.startswith('rm '):
                    filename = command.split(' ', 1)[1]  # Extract filename
                    try:
                        os.remove(filename)
                        result = f"File removed: {filename}"
                    except FileNotFoundError:
                        result = f"File not found: {filename}"
                    except PermissionError:
                        result = f"Permission denied: {filename}"

                elif command.startswith('rmdir '):
                    directory = command.split(' ', 1)[1]  # Extract directory name
                    try:
                        os.rmdir(directory)
                        result = f"Directory removed: {directory}"
                    except FileNotFoundError:
                        result = f"Directory not found: {directory}"
                    except OSError as e:
                        result = f"Error removing directory: {e}"

                elif command.startswith('cp '):
                    source, destination = command.split()[1:]
                    try:
                        shutil.copy(source, destination)
                        result = f"Copy successful: {source} -> {destination}"
                    except FileNotFoundError:
                        result = f"File not found: {source}"
                    except FileExistsError:
                        result = f"Destination already exists: {destination}"
                    except PermissionError:
                        result = f"Permission denied: {source} -> {destination}"

                elif command.startswith('mv '):
                    source, destination = command.split()[1:]
                    try:
                        shutil.move(source, destination)
                        result = f"Move successful: {source} -> {destination}"
                    except FileNotFoundError:
                        result = f"File not found: {source}"
                    except PermissionError:
                        result = f"Permission denied: {source} -> {destination}"

                elif command.startswith('cat '):
                    filename = command.split(' ', 1)[1]  # Extract filename
                    try:
                        with open(filename, 'r') as file:
                            result = file.read()
                    except FileNotFoundError:
                        result = f"File not found: {filename}"
                    except PermissionError:
                        result = f"Permission denied: {filename}"

                elif command.startswith('grep '):
                    pattern, filename = command.split()[1:]
                    try:
                        with open(filename, 'r') as file:
                            result = '\n'.join(line for line in file if pattern in line)
                    except FileNotFoundError:
                        result = f"File not found: {filename}"
                    except PermissionError:
                        result = f"Permission denied: {filename}"

                elif command.startswith('head '):
                    filename = command.split(' ', 1)[1]  # Extract filename
                    try:
                        with open(filename, 'r') as file:
                            result = ''.join(file.readline() for _ in range(10))
                    except FileNotFoundError:
                        result = f"File not found: {filename}"
                    except PermissionError:
                        result = f"Permission denied: {filename}"

                elif command.startswith('tail '):
                    filename = command.split(' ', 1)[1]  # Extract filename
                    try:
                        with open(filename, 'r') as file:
                            result = ''.join(file.readlines()[-10:])
                    except FileNotFoundError:
                        result = f"File not found: {filename}"
                    except PermissionError:
                        result = f"Permission denied: {filename}"

                elif command == 'ps':
                    result = subprocess.check_output(['ps']).decode()
                elif command.startswith('kill '):
                    pid = command.split()[1]
                    try:
                        subprocess.run(['kill', pid])
                        result = f"Process {pid} terminated."
                    except subprocess.CalledProcessError:
                        result = f"Failed to terminate process {pid}."
                elif command == 'df':
                    disk_usage = psutil.disk_usage('/')
                    result = f"Total: {disk_usage.total}, Used: {disk_usage.used}, Free: {disk_usage.free}"

                    
                elif command == 'du':
                    directory_path = '/path/to/directory'
                    total_disk_usage = get_disk_usage(directory_path)
                    result = f"Total disk usage: {total_disk_usage} bytes"

                elif command.startswith('wget '):
                    url = command.split()[1]
                    try:
                        subprocess.run(['wget', url])
                        result = f"File downloaded from {url}."
                    except subprocess.CalledProcessError:
                        result = f"Failed to download file from {url}."




                # Handle other commands similarly

                else:
                    result_bytes = subprocess.check_output(command + ' ' + parameters, shell=True, stderr=subprocess.STDOUT)
                    result = result_bytes.decode()  # Decode bytes to string
            except subprocess.CalledProcessError as e:
                result = e.output.decode()  # Decode bytes to string
            except FileNotFoundError:
                result = f"Command '{command}' not found."
            except Exception as e:
                result = f"Error: {e}"

            # Send the result back to client
            response = {
                "result": result
            }
            client_socket.send(json.dumps(response).encode())
        except ConnectionResetError:
            print(f"Connection with {address} closed unexpectedly.")
            del connected_clients[address]
            break

    # Close client socket
    client_socket.close()

# Define host and port
HOST = '127.0.0.1'
PORT = 5555

# Create a socket object
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the address
server_socket.bind((HOST, PORT))

# Listen for incoming connections
server_socket.listen(5)

print(f"Server listening on {HOST}:{PORT}...")

while True:
    # Accept connections from client
    client_socket, client_address = server_socket.accept()
    connected_clients[client_address] = client_socket
    print(f"Connection from {client_address} has been established.")
    
    # Display list of connected clients
    print("Connected clients:")
    for address in connected_clients:
        print(address)

    # Handle client in a separate thread
    client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
    client_thread.start()

# Close server socket
server_socket.close()
