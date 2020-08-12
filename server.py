import socket
import select
import time
from networking import send, receive
from game import Game

# constants for the server
IP = ""
PORT = 5555
SERVER_RATE = 4

# constants for the game
MIN_PLAYERS = 1
COUNTDOWN_TIME = 5

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind((IP, PORT))
server_socket.listen()

print(f"server running on {IP}:{PORT}")

sockets_list = [server_socket]

clients = {}

client_data = {}

# stuff to run the game
game = False
game_countdown = False

# main loop
while True:
    # do socket shit
    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list, 1 / SERVER_RATE)

    for notified_socket in read_sockets:
        if notified_socket == server_socket:
            client_socket, client_address = server_socket.accept()

            rec = receive(client_socket)
            if rec is False:
                continue
            else:
                username = rec['username']

            sockets_list.append(client_socket)

            clients[client_socket] = username

            client_data[client_socket] = []

            print(f"{username} connected - {client_address[0]}:{client_address[1]}")
        else:
            rec = receive(notified_socket)

            if rec is False:
                print(f"{clients[notified_socket]} disconnected")
                sockets_list.remove(notified_socket)
                del clients[notified_socket]
                continue
            else:
                client_data[notified_socket].append(rec)

    for notified_socket in exception_sockets:
        print(f"{clients[client_socket]} disconnected with exception")
        sockets_list.remove(notified_socket)
        del clients[notified_socket]

    # do the game
    if game == False:  # if there is not a game currently
        if len(clients.keys()) >= 4:
            player_sockets = list(clients.keys())[:4]
            usernames = []
            for client_socket in player_sockets:
                usernames.append(clients[client_socket])
            for client_socket in player_sockets:
                send(client_socket, {'message': f"starting game with {usernames}"})
            print(f"starting game with {usernames}")
            game = True
            game_countdown = False
        elif len(clients.keys()) >= MIN_PLAYERS:
            if game_countdown == False:
                usernames = []
                for client_socket in clients.keys():
                    usernames.append(clients[client_socket])
                for client_socket in clients.keys():
                    send(client_socket, {'message': f"starting {COUNTDOWN_TIME}s countdown for game with {usernames}"})
                print(f"starting {COUNTDOWN_TIME}s countdown for game with {usernames}")
                game_countdown = time.time()
            elif int(COUNTDOWN_TIME - time.time() + game_countdown) <= 0:
                player_sockets = list(clients.keys())
                usernames = []
                for client_socket in player_sockets:
                    usernames.append(clients[client_socket])
                for client_socket in player_sockets:
                    send(client_socket, {'message': f"starting game with {usernames}"})
                print(f"starting game with {usernames}")
                game = True
                game_countdown = False

        else:
            if game_countdown != False:
                game_countdown = False

    elif game == True:  # create the game
        game = Game(player_sockets, usernames)

    else:  # there is a game
        # check if any players have disconnected
        players_keys = list(game.players.keys())
        for client_socket in players_keys:
            if client_socket not in clients.keys():
                print('a player has disconnected!')
                game.player_disconnect(client_socket)
                if len(game.players.keys()) <= 0:
                    print('no remaining players, canceling game')
                    game = False
                    continue
        if game == False:
            continue

        # process actions from clients
        for client_socket in game.players.keys():
            if client_socket in client_data.keys():
                for rec in client_data[client_socket]:
                    if 'pick' or 'place' in rec.keys():
                        game.update_action(client_socket, rec)
            client_data[client_socket] = []  # reset the client data

        # update shit
        game.game_update()

        # send to clients
        for client_socket in game.players.keys():
            send_data = {}
            send_data['game_state'] = game.get_game_state(client_socket)
            send_data['action'] = game.get_action(client_socket)
            if game.game_over:
                print('game over')
                # send messages
                send_data['message'] = f"\n\n\ngame over\nScores:\n{game.get_scores(clients)}\n"

            send(client_socket, send_data)

        if game.game_over:
            # end the game
            del game
            game = False
            game_countdown = False
