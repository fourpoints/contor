import math
from itertools import product as cartesian_product
from operator import itemgetter, add
from typing import TypedDict, Literal, NotRequired
from collections.abc import Mapping


# Constants

K = math.cos(math.radians(30))  # outer/inner radius ratio
DIRECTIONS = {
    "N":  (+1,  0),
    "NE": (+1, +1),
    "SE": ( 0, +1),
    "S":  (-1,  0),
    "SW": (-1, -1),
    "NW": ( 0, -1),
}


# GeoJSON

## Primitives

type CoordinatePoint = list[float, float]
type CoordinateCollection = list[CoordinatePoint]
type Coordinates = CoordinatePoint | CoordinateCollection
type Direction = Literal["N", "NE", "SE", "S", "SW", "NW"]


## Geometries

class Geometry(TypedDict):
    type: str
    coordinates: CoordinatePoint


class Point(Geometry):
    type: Literal["Point"]
    coordinates: CoordinatePoint


class LineString(Geometry):
    type: Literal["LineString"]
    coordinates: CoordinateCollection


## Properties

class Properties(TypedDict):
    subType: str


## Features

class Feature(TypedDict):
    type: Literal["Feature"]
    geometry: Geometry
    properties: NotRequired[Properties]


class FeatureCollection(TypedDict):
    type: Literal["GeometryCollection"]
    features: list[Feature, ...]


# GeoJSON subtypes

class TileProperties(Properties):
    subType: Literal["Hexagon"]
    outerRadius: float
    innerRadius: float
    neighbors: Mapping[Direction, "Tile"]
    _id: list[int, int]


class PathProperties(Properties):
    subType: Literal["Path"]


class Tile(Feature):
    geometry: Point
    properties: TileProperties


class Path(Feature):
    geometry: LineString
    properties: PathProperties


class TileCollection(FeatureCollection):
    features: list[Tile, ...]


# Implementation

def _j(i, j):
    return -j+i//2


def _tile_xy(R, i, j):
    return [i*3/2*R, (i - 2*j)*K*R]


def _tile(R, i, j) -> Tile:
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": _tile_xy(R, i, j),
        },
        "properties": {
            "subType": "Hexagon",
            "outerRadius": R,
            "innerRadius": K*R,
            "neighbors": {},
            "_id": [i, j],
        },
    }


def _list_add(a, b):
    return list(map(add, a, b))


def _neighbor_index(tile, direction):
    return _list_add(tile["properties"]["_id"], DIRECTIONS[direction])


def make_grid(radius, width, height) -> TileCollection:
    tiles = {
        (i, _j(i, j)): _tile(radius, i, _j(i, j))
        for i, j in cartesian_product(range(width), range(height))
    }

    for tile in tiles.values():
        neighbors = tile["properties"]["neighbors"]
        for direction in DIRECTIONS:
            ni, nj = _neighbor_index(tile, direction)
            neighbor = tiles.get((ni, nj))
            if neighbor:
                neighbors[direction] = neighbor

    return {
        "type": "FeatureCollection",
        "features": list(tiles.values()),
    }


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


def make_path(R, points) -> Path:
    return {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [
                _tile_xy(R, i, _j(i, j))
                for i, j in points
            ],
        },
        "properties": {
            "subType": "Path",
        }
    }


# Helper functions

def coords(feature: Feature) -> Coordinates:
    return feature["geometry"]["coordinates"]


def neighbors(tile: Tile) -> Mapping[Direction, Tile]:
    return tile["properties"]["neighbors"]


def inner_radius(tile: Tile) -> float:
    return tile["properties"]["innerRadius"]


def outer_radius(tile: Tile) -> float:
    return tile["properties"]["outerRadius"]


def _id(tile: Tile) -> list[int, int]:
    return tile["properties"]["_id"]


if __name__ == "__main__":
    from matplotlib import pyplot as plt

    R = 5
    path = make_path(R, example_path)
    tiles = make_grid(radius=R, height=7, width=8)

    plt.plot(*zip(*coords(path)), color="dodgerblue")

    for tile in tiles["features"]:
        plt.scatter(*coords(tile), color="crimson")
        plt.text(*coords(tile), f'({_id(tile)[0]}, {_j(*_id(tile))})')

    test = tiles["features"][47]
    for n in neighbors(test).values():
        plt.plot(*zip(coords(test), coords(n)), color="crimson")

    plt.gca().set_aspect('equal')
    plt.show()
