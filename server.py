import socket
import select
import time
from networking import send, receive
from game import Game

# constants for the server
IP = "localhost"
PORT = 3331
SERVER_RATE = 4

# constants for the game
MIN_PLAYERS = 1
COUNTDOWN_TIME = 0

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind((IP, PORT))
server_socket.listen()

print(f"server running on {IP}:{PORT}")

socket_list = [server_socket]

clients = {}

client_data = {}

# stuff to run the game
active = False
game_countdown = -1

# main loop
while True:
    # do socket shit
    read_sockets, _, exception_sockets = select.select(socket_list, [], socket_list, 1 / SERVER_RATE)

    for notified_socket in read_sockets:
        if notified_socket == server_socket:
            client_socket, client_address = server_socket.accept()

            rec = receive(client_socket)
            if rec is False:
                continue
            else:
                username = rec['username']

            socket_list.append(client_socket)
            clients[client_socket] = username
            client_data[client_socket] = []

            print(f"{username} connected - {client_address[0]}:{client_address[1]}")
        else:
            rec = receive(notified_socket)

            if rec is False:
                print(f"{clients[notified_socket]} disconnected")
                socket_list.remove(notified_socket)
                del clients[notified_socket]
                continue
            else:
                client_data[notified_socket].append(rec)

    for notified_socket in exception_sockets:
        print(f"{clients[client_socket]} disconnected with exception")
        socket_list.remove(notified_socket)
        del clients[notified_socket]

    # do the game
    if not active:  # if there is not a game currently
        if len(clients.keys()) >= MIN_PLAYERS:
            if len(clients.keys()) >= 4:
                player_sockets = list(clients.keys())[:4]
            else:
                if game_countdown == -1:  # start countdown if it hasnt been already
                    usernames = []
                    for client_socket in clients.keys():
                        usernames.append(clients[client_socket])
                    
                    for client_socket in clients.keys():
                        send(client_socket, {'message': f"starting {COUNTDOWN_TIME}s countdown for game with {usernames}"})
                    
                    print(f"starting {COUNTDOWN_TIME}s countdown for game with {usernames}")
                    game_countdown = time.time()
                
                    continue
                
                elif time.time() - game_countdown <= COUNTDOWN_TIME:  # continue if still waiting
                    continue
                
                player_sockets = list(clients.keys())

            # get usernames
            usernames = []
            for client_socket in player_sockets:
                usernames.append(clients[client_socket])
            for client_socket in player_sockets:
                send(client_socket, {'message': f"starting game with {usernames}"})
            print(f"starting game with {usernames}")

            # update vars    
            active = True                   
            game_countdown = False

            # create the game
            game = Game(player_sockets, usernames)
        
        else:
            if game_countdown >= 0:
                game_countdown = -1

    else:  # there is a game, active is True
        # check if any players have disconnected
        players_keys = list(game.players.keys())
        for client_socket in players_keys:
            if client_socket not in clients.keys():
                print('a player has disconnected!')
                game.player_disconnect(client_socket)
                if len(game.players.keys()) == 0:
                    print('no remaining players, canceling game')
                    active = False
                    continue

        # process actions from clients
        for client_socket in game.players.keys():
            if client_socket in client_data.keys():
                for rec in client_data[client_socket]:
                    if 'action' in rec.keys():
                        game.update_action(client_socket, rec)
            client_data[client_socket] = []  # reset the client data

        # update shit
        game.game_update()

        # send to clients
        for client_socket in game.players.keys():
            send_data = {}
            send_data['game_state'] = game.get_game_state(client_socket)
            
            if game.game_over:
                print('game over')
                # send messages
                send_data['message'] = f"\n\n\ngame over\nScores:\n{game.get_scores(clients)}\n"

            send(client_socket, send_data)

        if game.game_over:
            # end the game
            del game
            active = False
            game_countdown = -1
