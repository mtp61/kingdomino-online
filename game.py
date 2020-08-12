import random
import copy
import json
from shared import calculate_score


class Game:
    def __init__(self, player_sockets, usernames):
        # random shuffle the deck
        deck = []
        for x in range(1, 49):
            deck.append(x)
        random.shuffle(deck)
        self.deck = deck

        # make players dict
        players = {}
        for x in range(len(player_sockets)):
            players[player_sockets[x]] = usernames[x]
        self.players = players

        # assign colors
        colors = ['p', 'y', 'b', 'g']
        player_colors = {}
        for x in range(len(list(players.keys()))):
            player_colors[list(players.keys())[x]] = colors[x]
        self.player_colors = player_colors

        # make player tile lists
        player_tiles = {}
        for player in players.keys():
            player_tiles[player] = []
        self.player_tiles = player_tiles

        # determine starting order
        player_order = list(player_sockets)
        random.shuffle(player_order)
        self.player_order = player_order

        # make to pick and picked tile lists
        self.tiles_to_pick = self.draw_tiles()
        tiles_picked = []
        for client_socket in self.player_order:
            tiles_picked.append([None, self.player_colors[client_socket]])
        self.tiles_picked = tiles_picked

        # setup actions
        self.actions = [(player_order[0], "pick", [0, 1, 2, 3])]

        # tile lookup
        with open('assets/tile_lookup.json', 'r') as file:
            self.tile_lookup = json.loads(file.read())

        # game over
        self.game_over = False

    def draw_tiles(self):
        numbers = []
        for x in range(4):
            if len(self.deck) > 0:
                numbers.append(self.deck.pop(0))
        numbers.sort()

        new_tiles = []
        for number in numbers:
            new_tiles.append([number, None])

        return new_tiles

    def player_disconnect(self, client_socket):
        # todo update tile picking
        del self.players[client_socket]

    def get_game_state(self, client_socket):
        game_state = {}

        # add info for you
        you = {}
        you['color'] = self.player_colors[client_socket]
        you['tiles'] = self.player_tiles[client_socket]
        game_state['you'] = you

        # add info for other players
        others = []
        for other_socket in self.players.keys():
            if other_socket != client_socket:
                other = {}
                other['color'] = self.player_colors[other_socket]
                other['tiles'] = self.player_tiles[other_socket]
                others.append(other)
        game_state['others'] = others

        # add info about tiles
        game_state['tiles_to_pick'] = self.tiles_to_pick
        game_state['tiles_picked'] = self.tiles_picked

        # add action info
        for action in self.actions:
            if action[0] == client_socket:
                game_state['action'] = action[1:]
                break

        # game over
        game_state['game_over'] = self.game_over

        return game_state

    def get_scores(self, players):
        scores_str = ""
        for client_socket in self.players.keys():
            score = str(calculate_score(self.player_tiles[client_socket], self.tile_lookup))
            scores_str += f"{players[client_socket]} - {score}\n"

        return scores_str

    def update_action(self, client_socket, rec):
        # make sure it is for a real action
        rec_action = (client_socket, rec['action'][0], rec['action'][1])
        for action in self.actions:
            if action == rec_action:
                resp = rec['resp']
                action_player = action[0]
                if action[1] == "pick":
                    # make sure the move is legal 
                    # todo
                    
                    # remove the action
                    self.actions.remove(action)

                    # set the color of the tile to pick
                    self.tiles_to_pick[resp][1] = self.player_colors[action_player]

                    # updated picked tiles
                    for n, tile in enumerate(self.tiles_picked):
                        if tile[1] == self.player_colors[action_player]:
                            if tile[0] is not None:
                                # give new place action
                                self.actions.append((action_player, 'place', tile[0]))
                            self.tiles_picked[n] = [None, None]
                            break

                    # setup next action
                    # check if there is another player to pick
                    num_tiles_picked = 0
                    for tile in self.tiles_to_pick:
                        if tile[1] is not None:
                            num_tiles_picked += 1
                    if num_tiles_picked < len(self.players.keys()):
                        # let the next player pick
                        available_tiles = []
                        for n, tile in enumerate(self.tiles_to_pick):
                            if tile[1] is None:
                                available_tiles.append(n)
                        # add new action
                        self.actions.append((self.player_order[num_tiles_picked], 'pick', available_tiles))

                elif action[1] == "place":
                    # check if move legal
                    # todo

                    # remove the action
                    self.actions.remove(action)

                    # add tile if not pass
                    if resp is not None:
                        self.player_tiles[action_player].append(resp)
                    

    def game_update(self):
        # setup useful variables
        num_players = len(list(self.players.keys()))

        # make sure all actions are done
        if len(self.actions) == 0:  # need to update game and provide new action
            # make the old to pick the new picked
            self.player_order = []  # reset the player order
            self.tiles_picked = []  # reset picked tiles
            for n, tile in enumerate(self.tiles_to_pick):
                if tile[1] is not None:
                    self.tiles_picked.append(copy.deepcopy(tile))
                    for client_socket in self.players.keys():
                        if self.player_colors[client_socket] == tile[1]:
                            self.player_order.append(client_socket)
                            break
            
            # draw new tiles and check if the game is over
            self.tiles_to_pick = self.draw_tiles()
            if len(self.tiles_to_pick) == 0:  # if there are no more tiles
                # empty tiles to pick
                self.tiles_to_pick = []
                for x in range(4):
                    self.tiles_to_pick.append([None, None])

                # if there are no tiles to place game over
                if len(self.tiles_picked) == 0 and len(self.actions) == 0:                        
                    self.game_over = True
                else:
                    # send action to place
                    for client_socket in self.players.keys():
                        for tile in self.tiles_picked:
                            if tile[1] == self.player_colors[client_socket]:
                                self.actions.append((client_socket, 'place', tile[0]))
                                break

                    self.tiles_picked = []

            else:  # if there are still tiles to pick, the next player needs to pick
                self.actions.append((self.player_order[0], 'pick', [0, 1, 2, 3]))
