import json


def send(socket, j):
    socket.send(json.dumps(j).encode('utf-8'))


def send_mult(sockets, j):
    for socket in sockets:
        send(socket, j)


def receive(client_socket):
    try:
        # TODO add the header shit from the tutorial
        rec = client_socket.recv(2048)
        return json.loads(rec.decode('utf-8'))
    except:
        return False
