import socket
import errno
import pygame
import sys
import json
from networking import send, \
    receive
from demo import tile_loader, \
    king_loader, \
    draw_board, \
    draw_tile, \
    draw_king, \
    in_rect, \
    get_grid_coords, \
    test_new_tile, \
    can_place

# VERSION = 0.1

# IP = "localhost
IP = "45.79.166.253"
PORT = 5555

WINDOW_W = 1200
WINDOW_H = 800
FRAMERATE = 30


def main():
    username = input("enter username: ")

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((IP, PORT))
    client_socket.setblocking(False)

    print(f"connected to server {IP}:{PORT}")

    # send username
    send(client_socket, {'username': username})

    server_data = []

    action = None

    placing = False

    active_game = False

    # main loop
    while True:
        # receive things
        try:
            while True:
                rec = receive(client_socket)
                if rec == False:
                    break
                server_data.append(rec)
        except IOError as e:
            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                print('reading error', str(e))
                continue
        except Exception as e:
            print('general error', str(e))

        # process server data
        for rec in server_data:
            if 'game_state' in rec.keys():
                game_state = rec['game_state']
                if not active_game:
                    screen, clock, tile_images, tile_lookup, king_images = start_game(WINDOW_W, WINDOW_H)
                    active_game = True
            if 'message' in rec.keys():
                print(rec['message'])
            if 'action' in rec.keys():
                if action != rec['action']:  # new action
                    if action is not None:
                        print(f"new action: {rec['action']}")
                    action = rec['action']
            else:
                action = None
        # all server data processed, clear the queue
        server_data = []

        # do game stuff
        if active_game:
            # check if closed
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            # actions
            if action is not None:
                if 'pick' in action.keys():
                    placing = False
                    # remove place if picking todo fix this later
                    #if 'place' in action.keys():
                    #    del action['place']
                    #    placing = False

                    # see if the mouse is pressed
                    if pygame.mouse.get_pressed()[0]:
                        if not mouse_was_down:
                            # see if you hit a tile todo dont hard code these, do along with better drawing
                            # get the options
                            pick_options = list(action['pick'])
                            for n, tile in enumerate(game_state['tiles_to_pick']):
                                if tile[1] is None:
                                    pick_options.append(n)

                            mousePos = pygame.mouse.get_pos()

                            for n, tile in enumerate(game_state['tiles_to_pick']):
                                tile_x = 300 + 600 + 150
                                tile_y = 0 + 50 + n * 75
                                tile_h = 50
                                tile_w = 100
                                if in_rect(mousePos, tile_x, tile_y, tile_w, tile_h):
                                    if n in pick_options:  # if the tile has not been picked
                                        print(f"picked tile {n+1}")
                                        send(client_socket, {'pick': n})
                                        break
                            mouse_was_down = True
                    else:
                        mouse_was_down = False

                elif 'place' in action.keys():


                    for tile in game_state['you']['tiles']:
                        if action['place'] == tile[0]:
                            print('already have this tile!')


                    if not placing:
                        placing = True
                        placing_number = action['place']
                        placing_direction = 'W'
                        dragging = False
                        placing_x = 550
                        placing_y = 700

                        if action['place'] is None:
                            print(f"tile duplication glitch")
                            send(client_socket, {'place': None})
                            placing = False
                            action['place'] = None
                        elif not can_place(game_state['you']['tiles'], placing_number, tile_lookup):
                            print(f"impossible to place tile, discarding")
                            send(client_socket, {'place': None})
                            placing = False
                            action['place'] = None

                    if pygame.mouse.get_pressed()[0]:  # if mouse down
                        mousePos = pygame.mouse.get_pos()
                        if dragging:  # if currently dragging
                            placing_x = mousePos[0] - dragging_offset_x
                            placing_y = mousePos[1] - dragging_offset_y
                        else:
                            # see if we hit it
                            if placing_direction == 'W' or placing_direction == 'E':
                                w = 50 * 2
                                h = 50
                            else:
                                w = 50
                                h = 50 * 2
                            if in_rect(mousePos, placing_x, placing_y, w, h):
                                # setup dragging
                                dragging_offset_x = mousePos[0] - placing_x
                                dragging_offset_y = mousePos[1] - placing_y
                                dragging = True

                    else:
                        # check if we were dragging
                        if dragging:
                            dragging = False
                            # check if we can place it here
                            grid_coords = get_grid_coords(placing_x + 25, placing_y + 25, 500, 500, 350, 150)
                            grid_x = grid_coords[0]
                            grid_y = grid_coords[1]
                            if placing_direction == 'W':
                                pass
                            elif placing_direction == 'N':
                                pass
                            elif placing_direction == 'E':
                                grid_x += 1
                            elif placing_direction == 'S':
                                grid_y += 1

                            if test_new_tile(game_state['you']['tiles'], [placing_number, grid_x, grid_y, placing_direction], tile_lookup):

                                game_state['you']['tiles'].append([placing_number, grid_x, grid_y, placing_direction])
                                send(client_socket, {'place': [placing_number, grid_x, grid_y, placing_direction]})
                                placing = False
                                action['place'] = None

                        # check for rotation
                        if pygame.key.get_pressed()[pygame.K_a]:

                            if rotation is None:
                                rotation = 'l'
                            else:
                                rotation = 'held'
                        elif pygame.key.get_pressed()[pygame.K_d]:
                            if rotation is None:
                                rotation = 'r'
                            else:
                                rotation = 'held'
                        elif pygame.key.get_pressed()[pygame.K_LEFT]:
                            if rotation is None:
                                rotation = 'l'
                            else:
                                rotation = 'held'
                        elif pygame.key.get_pressed()[pygame.K_RIGHT]:
                            if rotation is None:
                                rotation = 'r'
                            else:
                                rotation = 'held'
                        else:
                            rotation = None

                        # todo why is this not working
                        '''
                        for event in pygame.event.get():
                            if event.type == pygame.KEYDOWN:
                                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                                    rotation = 'l'

                                if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                                    rotation = 'r' 
                        '''

                        if rotation is not None and rotation != 'held':  # if there is a key down
                            if rotation == 'l':
                                if placing_direction == 'N':
                                    placing_direction = 'W'
                                elif placing_direction == 'W':
                                    placing_direction = 'S'
                                elif placing_direction == 'S':
                                    placing_direction = 'E'
                                elif placing_direction == 'E':
                                    placing_direction = 'N'
                            elif rotation == 'r':
                                if placing_direction == 'N':
                                    placing_direction = 'E'
                                elif placing_direction == 'E':
                                    placing_direction = 'S'
                                elif placing_direction == 'S':
                                    placing_direction = 'W'
                                elif placing_direction == 'W':
                                    placing_direction = 'N'

                else:
                    placing = False

                if 'game_over' in action.keys():
                    print('game over in action keys')
                    if action['game_over']:
                        active_game = False
                        pygame.quit()
                        action = None
                        continue

            # draw
            screen.fill((255, 255, 255))

            # draw your board
            draw_board(screen, 500, 500, 350, 150, game_state['you']['tiles'], tile_images, 2, game_state['you']['color'], king_images)

            # draw other boards
            for n, other in enumerate(game_state['others']):
                draw_board(screen, 200, 200, 50, 50 + 250 * n, other['tiles'], tile_images, 1, other['color'], king_images)

            # draw tiles
            # to pick
            # todo put this in a function
            for n, tile in enumerate(game_state['tiles_to_pick']):
                if tile[0] is not None:
                    draw_tile(screen, tile[0], 300 + 600 + 150, 0 + 50 + n * 75, 50, 'W', tile_images)
                if tile[1] is not None:
                    draw_king(screen, tile[1], 300 + 600 + 50, 0 + 50 + n * 75, 50, king_images)
            # picked
            for n, tile in enumerate(game_state['tiles_picked']):
                if tile[0] is not None:
                    draw_tile(screen, tile[0], 300 + 600 + 150, 400 + 50 + n * 75, 50, 'W', tile_images)
                if tile[1] is not None:
                    draw_king(screen, tile[1], 300 + 600 + 50, 400 + 50 + n * 75, 50, king_images)

            # draw placing tile
            if placing:

                draw_tile(screen, placing_number, placing_x, placing_y, 50, placing_direction, tile_images)

            # update display
            pygame.display.update()

            # limit framerate
            clock.tick(FRAMERATE)


def start_game(window_w, window_h):
    pygame.init()
    screen = pygame.display.set_mode((window_w, window_h))

    clock = pygame.time.Clock()

    tile_images = tile_loader()

    king_images = king_loader()

    with open('assets/tile_lookup.json', 'r') as file:
        tile_lookup = json.loads(file.read())

    return screen, clock, tile_images, tile_lookup, king_images


def send_action_complete():
    pass


if __name__ == "__main__":
    main()
