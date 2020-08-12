import random
import copy
import json
from demo import calculate_score


class Game:
    def __init__(self, player_sockets, usernames):
        # random shuffle the deck
        deck = []
        for x in range(48):
            deck.append(x + 1)
        random.shuffle(deck)
        self.deck = deck

        # make player dict
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
        player_actions = {}
        player_actions_complete = {}
        for client_socket in player_sockets:
            player_actions[client_socket] = None
            player_actions_complete[client_socket] = None
        self.player_actions = player_actions
        self.player_actions_complete = player_actions_complete

        # setup first action
        self.player_actions[player_order[0]] = {"pick": [0, 1, 2, 3]}

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

        if len(numbers) == 0:
            return False

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

        return game_state

    def get_action(self, client_socket):
        return self.player_actions[client_socket]

    def update_action(self, client_socket, action_complete):
        self.player_actions_complete[client_socket] = action_complete

    def get_scores(self, players):
        scores_str = ""
        for client_socket in self.players.keys():
            score = str(calculate_score(self.player_tiles[client_socket], self.tile_lookup))
            scores_str += f"{players[client_socket]} - {score}\n"

        return scores_str

    def game_update(self):
        # set up useful variables
        num_players = len(list(self.players.keys()))

        # process actions
        need_update = False
        for client_socket in self.players.keys():
            if self.player_actions_complete[client_socket] is not None:
                if 'pick' in list(self.player_actions_complete[client_socket].keys()):
                    self.tiles_to_pick[self.player_actions_complete[client_socket]['pick']][1] = self.player_colors[client_socket]

                    # update picked tiles
                    self.player_actions[client_socket] = None
                    for n, tile in enumerate(self.tiles_picked):
                        if tile[1] == self.player_colors[client_socket]:
                            if tile[0] is not None:
                                # give new action
                                self.player_actions[client_socket] = {'place': tile[0]}
                            self.tiles_picked[n] = [None, None]
                            break

                    # let the next player pick
                    # check if there is another player to pick
                    num_tiles_picked = 0
                    for tile in self.tiles_to_pick:
                        if tile[1] is not None:
                            num_tiles_picked += 1
                    if num_tiles_picked < num_players:  # there are more to pick
                        # let the next player pick
                        available_tiles = []
                        for n, tile in enumerate(self.tiles_to_pick):
                            if tile[1] is None:
                                available_tiles.append(n)
                        self.player_actions[self.player_order[num_tiles_picked]] = {'pick': available_tiles}

                    self.player_actions_complete[client_socket] = None

                elif 'place' in list(self.player_actions_complete[client_socket].keys()):
                    if self.player_actions_complete[client_socket]['place'] is not None:
                        self.player_tiles[client_socket].append(self.player_actions_complete[client_socket]['place'])
                    self.player_actions_complete[client_socket] = None
                    self.player_actions[client_socket] = None

                need_update = True

        # update the game
        if need_update:
            # see if we are waiting for actions to be completed
            actions_complete = True
            for client_socket in self.players.keys():
                if self.player_actions[client_socket] is not None:
                    actions_complete = False
                    break
            if actions_complete:
                print(f"stepping the game forward")
                # make the old to pick the new picked
                self.player_order = []  # reset the player order
                self.tiles_picked = []
                for n, tile in enumerate(self.tiles_to_pick):
                    if tile[1] is not None:
                        self.tiles_picked.append(copy.deepcopy(tile))
                        for client_socket in self.players.keys():
                            if self.player_colors[client_socket] == tile[1]:
                                self.player_order.append(client_socket)
                                break

                # draw new cards
                self.tiles_to_pick = self.draw_tiles()
                if self.tiles_to_pick == False:  # if there are no more tiles
                    self.tiles_to_pick = []
                    for x in range(4):
                        self.tiles_to_pick.append([None, None])

                    # if there are no tiles to place game over
                    if len(self.tiles_picked) == 0:
                        for client_socket in self.players.keys():
                            self.player_actions[client_socket] = {'game_over': True}
                        self.game_over = True
                    else:
                        # send action to place
                        for client_socket in self.players.keys():
                            for tile in self.tiles_picked:
                                if tile[1] == self.player_colors[client_socket]:
                                    self.player_actions[client_socket] = {'place': tile[0]}
                                    break

                        self.tiles_picked = []

                else:
                    self.player_actions[self.player_order[0]] = {"pick": [0, 1, 2, 3]}
