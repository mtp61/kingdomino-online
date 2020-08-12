import pygame
import sys
import json


def draw_board(screen, w, h, x_offset, y_offset, tiles, tile_images, line_thickness, color, king_images):
    # format for tiles: (number (int), head_x (int), head_y (int), direction (char))

    #screen.fill((255, 255, 255))

    # draw grid
    x_gap = w // 9
    y_gap = h // 9

    x_extra = w % 9
    y_extra = h % 9

    for x in range(10):
        pygame.draw.rect(screen, (0, 0, 0), (x_offset + x * x_gap, y_offset, line_thickness, h - y_extra + line_thickness))
    for x in range(10):
        pygame.draw.rect(screen, (0, 0, 0), (x_offset, y_offset + x * y_gap, w - x_extra + line_thickness, line_thickness))

    # draw castle
    king_image = pygame.transform.scale(king_images[color], (x_gap, y_gap))
    screen.blit(king_image, (4 * x_gap + x_offset, 4 * y_gap + y_offset))

    # draw tiles
    for tile in tiles:
        # draw based on direction
        if tile[3] == 'N':
            tile_img = pygame.transform.scale(tile_images[tile[0]], (x_gap * 2, y_gap))
            tile_img = pygame.transform.rotate(tile_img, 270)
            screen.blit(tile_img, ((tile[1] + 4) * x_gap + x_offset, (tile[2] + 4) * y_gap + y_offset))
        elif tile[3] == 'W':
            tile_img = pygame.transform.scale(tile_images[tile[0]], (x_gap * 2, y_gap))
            screen.blit(tile_img, ((tile[1] + 4) * x_gap + x_offset, (tile[2] + 4) * y_gap + y_offset))
        elif tile[3] == 'S':
            tile_img = pygame.transform.scale(tile_images[tile[0]], (x_gap * 2, y_gap))
            tile_img = pygame.transform.rotate(tile_img, 90)
            screen.blit(tile_img, ((tile[1] + 4) * x_gap + x_offset, (tile[2] + 3) * y_gap + y_offset))
        elif tile[3] == 'E':
            tile_img = pygame.transform.scale(tile_images[tile[0]], (x_gap * 2, y_gap))
            tile_img = pygame.transform.rotate(tile_img, 180)
            screen.blit(tile_img, ((tile[1] + 3) * x_gap + x_offset, (tile[2] + 4) * y_gap + y_offset))


def draw_tile(screen, number, x, y, size, direction, tile_images):
    if direction == 'N':
        tile_img = pygame.transform.scale(tile_images[number], (size * 2, size))
        tile_img = pygame.transform.rotate(tile_img, 270)
        screen.blit(tile_img, (x, y))
    elif direction == 'W':
        tile_img = pygame.transform.scale(tile_images[number], (size * 2, size))
        screen.blit(tile_img, (x, y))
    elif direction == 'S':
        tile_img = pygame.transform.scale(tile_images[number], (size * 2, size))
        tile_img = pygame.transform.rotate(tile_img, 90)
        screen.blit(tile_img, (x, y))
    elif direction == 'E':
        tile_img = pygame.transform.scale(tile_images[number], (size * 2, size))
        tile_img = pygame.transform.rotate(tile_img, 180)
        screen.blit(tile_img, (x, y))


def draw_king(screen, color, x, y, size, king_images):
    king_img = pygame.transform.scale(king_images[color], (size, size))
    screen.blit(king_img, (x, y))


def tile_loader():
    tile_images = {}

    tileset = pygame.image.load('assets/tiles.png')
    w, h = tileset.get_size()

    for tile_x in range(6):
        for tile_y in range(8):
            rect = (tile_x * w / 6, tile_y * h / 8, w / 6, h / 8)
            tile_images[tile_x * 8 + tile_y + 1] = tileset.subsurface(rect)

    return tile_images


def king_loader():
    king_images = {}

    colors = ['p', 'y', 'g', 'b']
    for color in colors:
        king_images[color] = pygame.image.load(f"assets/king_{color}.png")

    return king_images


def tiles_to_grid(tiles, tile_lookup):
    '''
    grid key
    c - castle
    e - empty
    g - grass
    t - trees
    w - water
    f - field
    d - desert
    m - mine
    '''

    # make the grid
    grid = []
    for y in range(9):
        row = []
        for x in range(9):
            row.append(('e', 0))
        grid.append(row)

    # make the center
    grid[4][4] = ('c', 0)

    # loop thru tiles
    for tile in tiles:
        # update head
        grid[tile[1] + 4][tile[2] + 4] = (tile_lookup[str(tile[0])]['head_type'], tile_lookup[str(tile[0])]['head_crowns'])

        # update tail
        if tile[3] == 'N':
            grid[tile[1] + 4][tile[2] + 5] = (
            tile_lookup[str(tile[0])]['tail_type'], tile_lookup[str(tile[0])]['tail_crowns'])
        elif tile[3] == 'W':
            grid[tile[1] + 5][tile[2] + 4] = (
            tile_lookup[str(tile[0])]['tail_type'], tile_lookup[str(tile[0])]['tail_crowns'])
        elif tile[3] == 'S':
            grid[tile[1] + 4][tile[2] + 3] = (
            tile_lookup[str(tile[0])]['tail_type'], tile_lookup[str(tile[0])]['tail_crowns'])
        elif tile[3] == 'E':
            grid[tile[1] + 3][tile[2] + 4] = (
            tile_lookup[str(tile[0])]['tail_type'], tile_lookup[str(tile[0])]['tail_crowns'])

    return grid


def test_new_tile(tiles, new_tile, tile_lookup):
    # tile format: [number, x, y, direction]

    grid = tiles_to_grid(tiles, tile_lookup)

    # get head position
    head_x = new_tile[1]
    head_y = new_tile[2]

    # get tail position based on direction
    if new_tile[3] == "N":
        tail_x = head_x
        tail_y = head_y + 1
    elif new_tile[3] == "W":
        tail_x = head_x + 1
        tail_y = head_y
    elif new_tile[3] == "S":
        tail_x = head_x
        tail_y = head_y - 1
    elif new_tile[3] == "E":
        tail_x = head_x - 1
        tail_y = head_y

    # test if the tile is in the grid
    # test head
    if head_x > 4 or head_x < -4 or head_y > 4 or head_y < -4:
        return False
    # test tail
    if tail_x > 4 or tail_x < -4 or tail_y > 4 or tail_y < -4:
        return False

    # test if the tile is in the center
    # test head
    if head_x == 0 and head_y == 0:
        return False
    # test tail
    if tail_x == 0 and tail_y == 0:
        return False

    # test if the tile is on old tiles
    # test head
    if grid[head_x + 4][head_y + 4][0] != 'e':
        return False
    # test tail
    if grid[tail_x + 4][tail_y + 4][0] != 'e':
        return False

    # test if the tile is within a 5x5
    grid_bound_N, grid_bound_W, grid_bound_S, grid_bound_E = 0, 0, 0, 0
    for y in range(9):
        for x in range(9):
            if grid[x][y][0] != 'e':
                if y - 4 < grid_bound_N:
                    grid_bound_N = y - 4
                if x - 4 < grid_bound_W:
                    grid_bound_W = x - 4
                if y - 4 > grid_bound_S:
                    grid_bound_S = y - 4
                if x - 4 > grid_bound_E:
                    grid_bound_E = x - 4
    # test head
    if head_y < grid_bound_N:
        grid_bound_N = head_y
    if head_x < grid_bound_W:
        grid_bound_W = head_x
    if head_y > grid_bound_S:
        grid_bound_S = head_y
    if head_x > grid_bound_E:
        grid_bound_E = head_x
    # test tail
    if tail_y < grid_bound_N:
        grid_bound_N = tail_y
    if tail_x < grid_bound_W:
        grid_bound_W = tail_x
    if tail_y > grid_bound_S:
        grid_bound_S = tail_y
    if tail_x > grid_bound_E:
        grid_bound_E = tail_x
    # test if too big
    if grid_bound_S - grid_bound_N + 1 > 5 or grid_bound_E - grid_bound_W + 1 > 5:
        return False

    # test if the tile matches up
    # find the tiles to test
    head_type = tile_lookup[str(new_tile[0])]['head_type']
    tail_type = tile_lookup[str(new_tile[0])]['tail_type']
    # test head
    to_test_head = []
    to_test_head.append((head_x + 1, head_y))
    to_test_head.append((head_x - 1, head_y))
    to_test_head.append((head_x, head_y + 1))
    to_test_head.append((head_x, head_y - 1))
    for coords in to_test_head:
        if -4 <= coords[0] <= 4 and -4 <= coords[1] <= 4:  # if in the map
            if grid[coords[0] + 4][coords[1] + 4][0] == head_type or grid[coords[0] + 4][coords[1] + 4][0] == 'c':
                return True
    # test tail
    to_test_tail = []
    to_test_tail.append((tail_x + 1, tail_y))
    to_test_tail.append((tail_x - 1, tail_y))
    to_test_tail.append((tail_x, tail_y + 1))
    to_test_tail.append((tail_x, tail_y - 1))
    for coords in to_test_tail:
        if -4 <= coords[0] <= 4 and -4 <= coords[1] <= 4:  # if in the map
            if grid[coords[0] + 4][coords[1] + 4][0] == tail_type or grid[coords[0] + 4][coords[1] + 4][0] == 'c':
                return True

    # if a match was found already returned, else return false
    return False


def get_grid_coords(x, y, board_w, board_h, board_x_offset, board_y_offset):
    x_size = board_w // 9
    y_size = board_h // 9

    return ((x - board_x_offset) // x_size - 4, (y - board_y_offset) // y_size - 4)


def neighbors(coords):
    neighbors = []
    if coords[0] > 0:
        neighbors.append((coords[0] - 1, coords[1]))
    if coords[0] < 8:
        neighbors.append((coords[0] + 1, coords[1]))
    if coords[1] > 0:
        neighbors.append((coords[0], coords[1] - 1))
    if coords[1] < 8:
        neighbors.append((coords[0], coords[1] + 1))

    return neighbors


def calculate_score(tiles, tile_lookup):
    grid = tiles_to_grid(tiles, tile_lookup)

    region_grid = []
    for y in range(9):
        row = []
        for x in range(9):
            row.append(-1)
        region_grid.append(row)

    to_search = []
    for x in range(9):
        for y in range(9):
            to_search.append((x,y))

    num_regions = 0
    while len(to_search) > 0:
        region_to_search = [(to_search[0][0], to_search[0][1])]
        region_searched = []
        region_type = grid[to_search[0][0]][to_search[0][1]][0]
        while len(region_to_search) > 0:
            # search neighbors, adding new nodes
            new_region_to_search = []
            for coords in region_to_search:
                for neighbor in neighbors(coords):
                    if neighbor not in region_searched and neighbor in to_search:
                        if grid[neighbor[0]][neighbor[1]][0] == region_type:
                            if neighbor not in region_to_search and neighbor not in new_region_to_search:
                                new_region_to_search.append(neighbor)

            # move to to search to searched
            for coords in region_to_search:
                region_searched.append(coords)
            region_to_search = list(new_region_to_search)

        # remove region searched from to search and assign a new reigon
        for coords in region_searched:
            to_search.remove(coords)

        new_region = int(num_regions)
        num_regions += 1

        # update region grid
        for coords in region_searched:
            region_grid[coords[0]][coords[1]] = new_region

    # add up the region scores
    region_crowns = {}
    region_area = {}
    for x in range(num_regions):
        region_crowns[x] = 0
        region_area[x] = 0
    for y in range(9):
        for x in range(9):
            region_area[region_grid[x][y]] += 1
            region_crowns[region_grid[x][y]] += grid[x][y][1]

    # add up the score
    score = 0
    for x in range(num_regions):
        score += region_area[x] * region_crowns[x]

    return score


def can_place(tiles, new_number, tile_lookup):
    # loop thru all possible tile positions, if can't place return false
    for x in range(-4, 5):
        for y in range(-4, 5):
            for direction in ['N', 'W', 'S', 'E']:
                if test_new_tile(tiles, [new_number, x, y, direction], tile_lookup):
                    return True
    # can't place anywhere
    return False


def in_rect(mousePos, x, y, w, h):
    if mousePos[0] >= x and mousePos[0] <= x + w and mousePos[1] >= y and mousePos[1] <= y + h:
        return True
    return False


if __name__ == "__main__":
    main()
