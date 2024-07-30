import math
from itertools import product as cartesian_product
from operator import itemgetter


K = math.cos(math.radians(30))  # outer/inner radius ratio
DIRECTIONS = {
    "N":  (+1,  0),
    "NE": (+1, +1),
    "SE": ( 0, +1),
    "S":  (-1,  0),
    "SW": (-1, -1),
    "NW": ( 0, -1),
}


def _j(i, j):
    return -j+i//2


def _tile_x(R, i, j):
    return i*3/2*R


def _tile_y(R, i, j):
    return (i - 2*j)*K*R


def _tile(R, i, j):
    return {
        "type": "Tile",
        "x": _tile_x(R, i, j),
        "y": _tile_y(R, i, j),
        "R": R,
        "r": K*R,
        "_i": i,
        "_j": j,
    }


def _neighbor_index(tile, direction):
    i, j = tile["_i"], tile["_j"]
    di, dj = DIRECTIONS[direction]
    ni, nj = i + di, j + dj
    return (ni, nj)


def make_grid(radius, width, height):
    tiles = {
        (i, _j(i, j)): _tile(radius, i, _j(i, j))
        for i, j in cartesian_product(range(width), range(height))
    }

    for tile in tiles.values():
        neighbors = tile["neighbor"] = {}
        for direction in DIRECTIONS:
            ni, nj = _neighbor_index(tile, direction)
            neighbor = tiles.get((ni, nj))
            if neighbor:
                neighbors[direction] = neighbor

    return list(tiles.values())


example_path = [
    (0, 0),
    (1, 0),
    (1, 1),
    (0, 2),
    (0, 3),
    (1, 3),
    (1, 4),
    (1, 5),
    (2, 6),
    (3, 5),
    (3, 4),
    (4, 4),
    (4, 3),
    (3, 2),
    (3, 1),
    (3, 0),
    (4, 0),
    (5, 0),
    (5, 1),
    (5, 2),
    (6, 3),
    (6, 4),
    (5, 4),
    (5, 5),
    (6, 6),
]


def make_path(R, points):
    return [
        (_tile_x(R, i, _j(i, j)), _tile_y(R, i, _j(i, j)))
        for i, j in points]


def vectorize(func):
    return lambda obj: list(map(func, obj))


xy = itemgetter("x", "y")
xs = vectorize(itemgetter(0))
ys = vectorize(itemgetter(1))
neighbors = itemgetter("neighbor")


if __name__ == "__main__":
    from matplotlib import pyplot as plt

    R = 5
    path = make_path(R, example_path)
    tiles = make_grid(radius=R, height=7, width=8)

    plt.plot(xs(path), ys(path), color="dodgerblue")

    for tile in tiles:
        plt.scatter(*xy(tile), color="crimson")
        plt.text(*xy(tile), f'({tile["_i"]}, {_j(tile["_i"], tile["_j"])})')

    test = tiles[47]
    for n in neighbors(test).values():
        plt.plot(*zip(xy(test), xy(n)), color="crimson")

    plt.gca().set_aspect('equal')
    plt.show()
