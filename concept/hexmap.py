import math
import operator
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from collections import namedtuple
from itertools import chain, repeat, product as cartesian_product
from types import GeneratorType


# --- Framework

listify = lambda s: list(s) if isinstance(s, (tuple, GeneratorType)) else [s]

# prototype pattern
xml = type("xml", (dict,), {
    "__getattr__": lambda self, name: type(self)(tag=name),
    "__call__": lambda self, **kwargs: type(self)(**self, attributes=kwargs),
    "__getitem__": lambda self, args: type(self)(**self, children=listify(args))
})()

function = type("function", (dict,), {
    "__getattr__": lambda self, name: type(self)(name=name),
    "__call__": lambda self, *args: type(self)(**self, args=listify(args)),
})()


child_is_string = lambda children:\
    len(children) == 1 and isinstance(children[0], str)


def elify(obj):
    el = ET.Element(obj.get("tag"), attrib=obj.get("attributes", {}))

    # Doesn't handle multiple strings
    children = obj.get("children", [])
    if child_is_string(children):
        el.text = children[0]
    else:
        el.extend(list(map(elify, children)))

    return el


def kebab_case(key):
    return key.replace("_", "-")


def string(value):
    if isinstance(value, str):
        return value
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, list):
        return " ".join(map(string, value))
    elif isinstance(value, tuple):
        return ",".join(map(string, value))
    elif isinstance(value, type(function)):
        return f"{value['name']}({','.join(map(string, value['args']))})"
    elif isinstance(value, dict):
        return ";".join(
            f"{key}:{string(value)}" for key, value in value.items())
    else:
        raise TypeError(f"Unknown type '{type(value)}' for '{value}.'")


def dictmap(obj, k, v):
    return dict(zip(map(k, obj.keys()), map(v, obj.values())))


def stringify(obj):
    obj = obj.copy()

    attributes = obj.get("attributes", {})
    if "attributes" in obj:
        obj["attributes"] = dictmap(attributes, kebab_case, string)

    # Doesn't handle multiple strings
    children = obj.get("children", [])
    if not children or child_is_string(children):
        pass
    else:
        obj["children"] = list(map(stringify, children))

    return obj


def serialize(root):
    return minidom.parseString(ET.tostring(root)).toprettyxml(indent="   ")


# --- Coordinates

coord = namedtuple("coord", ["x", "y"])

def add(p1, p2):
    return type(p1)._make(map(operator.add, p1, p2))

def shift_by(offset):
    def shift(p):
        return add(offset, p)
    return shift


# --- Polygons

K = math.cos(math.radians(30))  # outer/inner radius ratio


def path_join(points):
    return " ".join(
        f"{a} {x} {y}"
        for (x, y), a
        in zip(points, chain("M", repeat("L"))))


def hexagon_points(c, radius):
    """
    hexagon_points((100, 100), 96) ~ [
        (148, 183.138438763306),
        ( 52, 183.138438763306),
        (  4, 100),
        ( 52,  16.8615612366939),
        (148,  16.8615612366939),
        (196, 100)
    ]
    """
    return list(map(shift_by(c), [
        (
            math.cos(math.radians(60 + angle))*radius,
            math.sin(math.radians(60 + angle))*radius,
        ) for angle in range(0, 360, 60)
    ]))


def parallelogram_points(c, length):
    return list(map(shift_by(c), [
        (-length*K*K/3, -length*K/2),
        (length*K*K, -length*K/2),
        (length*K*K/3, +length*K/2),
        (-length*K*K, +length*K/2),
    ]))


def square_points(c, length):
    return list(map(shift_by(c), [
        (-length/2, -length/2),
        (+length/2, -length/2),
        (+length/2, +length/2),
        ( -length/2, +length/2),
    ]))


def hexagon(c, radius, style={}):
    return xml.polygon(
        style={
            "fill": "none",
            "stroke": "#000000",
            # "stroke-width": "2.5px",
            "stroke-width": "1px",
        } | style,
        points=hexagon_points(c, radius),
    )


def hexagon_dashed(c, radius):
    points = list(map(shift_by(c), [
        (
            math.cos(math.radians(angle))*radius,
            math.sin(math.radians(angle))*radius,
        ) for angle in range(0, 360+1, 60)
    ]))

    return xml.g[
        xml.path(
            fill="none",
            d=path_join(points[0:3])
        ),
        xml.path(
            fill="none",
            stroke_dasharray=3,
            stroke_width=0.8,
            d=path_join(points[2:4])
        ),
        xml.path(
            fill="none",
            d=path_join(points[3:6])
        ),
        xml.path(
            fill="none",
            stroke_dasharray=3,
            stroke_width=0.8,
            d=path_join(points[5:7])
        ),
    ]


def parallelogram(c, length, style={}):
    return xml.polygon(
        style={
            "fill": "none",
            "stroke": "#000000",
            # "stroke-width": "2.5px",
            "stroke-width": "1px",
        } | style,
        points=parallelogram_points(c, length),
    )


def square(c, length, style={}):
    return xml.polygon(
        style={
            "fill": "none",
            "stroke": "#000000",
            # "stroke-width": "2.5px",
            "stroke-width": "1px",
        } | style,
        points=square_points(c, length),
    )


def hx(R, x, y): return x*3/2*R
def hy(R, x, y): return (x - 2*y)*K*R
def hc(C, R, x, y): return add(C, (hx(R, x, y), hy(R, x, y)))

def px(R, x, y): return (x + y/2)*R
def py(R, x, y): return -y*K*R
def pc(C, R, x, y): return add(C, (px(R, x, y), py(R, x, y)))

def sx(R, x, y): return x*R
def sy(R, x, y): return -y*R
def sc(C, R, x, y): return add(C, (sx(R, x, y), sy(R, x, y)))


# --- Axes

def marker(color):
    return xml.marker(
        id=f"arrow-{color}",
        viewBox=[0, 0, 10, 10],
        refX=5,
        refY=5,
        markerWidth=4,
        markerHeight=4,
        orient="auto-start-reverse",
        fill=color,
        stroke=color,
    )[xml.path(d=["M", 0, 0, "L", 10, 5, "L", 0, 10, "z"])]


def axes(R, x, y):
    def axis(color, dx, dy):
        return xml.line(
            x1=CX,
            y1=CY,
            x2=CX+x(R, dx, dy),
            y2=CY+y(R, dx, dy),
            stroke=color,
            marker_end=function.url(f"#arrow-{color}"),
        )

    for color, (dx, dy) in [
        ("red", (1, 0)),
        ("blue", (0, 1)),
        ("green", (1, 1)),
    ]:
        yield axis(color=color, dx=dx, dy=dy)


# --- Tiles

def hex_tile(C, R, x, y, style={}):
    return hexagon(hc(C, R, x, y), R, style)


def parallelogram_tile(C, R, x, y, style={}):
    return parallelogram(pc(C, R, x, y), R, style)


def square_tile(C, R, x, y, style={}):
    return square(sc(C, R, x, y), R, style)


# --- Map

def _neighbour_points():
    return [
        (+1, +0),
        (+0, +1),
        (+1, +1),
        (-1, +0),
        (+0, -1),
        (-1, -1),
    ]


def _neighours(tile, C, R, X, Y):
    return xml.g[
        (tile(C, R, X+dx, Y+dy)
        for dx, dy in _neighbour_points())
    ]


def square_neighbours(C, R, X, Y):
    return _neighours(square_tile, C, R, X, Y)


def parallelogram_neighbours(C, R, X, Y):
    return _neighours(parallelogram_tile, C, R, X, Y)


def _grid(tile, C, R, X, Y):
    return xml.g[
        *(tile(C, R, x, -y+x//2)
        for x, y in cartesian_product(range(X), range(Y))
        # if (x%2 == 0 or y != 0)  # remove top layer
        )
    ]


def square_grid(C, R, X, Y):
    return _grid(square_tile, C, R, X, Y)


def parallelogram_grid(C, R, X, Y):
    return _grid(parallelogram_tile, C, R, X, Y)


def hex_grid(C, R, X, Y):
    return _grid(hex_tile, C, R, X, Y)


def _path(shift, C, R, points):
    points = [
        shift(C, R, x, y)
        for x, y in points
    ]
    return xml.path(
        fill="none",
        d=path_join(points),
    )


def square_path(C, R, points):
    return _path(sc, C, R, points)


def parallelogram_path(C, R, points):
    return _path(pc, C, R, points)


def hex_path(C, R, points):
    return _path(hc, C, R, points)


# --- Grid

CX = CY = 50
C = coord(CX, CY)
R = 16
PATH = [
    (0, 0),
    (1, 0),
    (1, -1),
    (1, -2),
    (2, -2),
    (2, -3),
    (1, -4),
    (1, -5),
    (2, -5),
    (3, -4),
    (4, -3),
    (4, -2),
    (4, -1),
    (4, 0),
    (3, 0),
    (3, 1),
    (4, 2),
    (5, 2),
    (6, 2),
    (6, 1),
    (6, 0),
    (6, -1),
    (6, -2),
    (6, -3),
]


svg = xml.svg(
    xmlns="http://www.w3.org/2000/svg",
    id="id",
    viewBox=[0, 0, 250, 250],
    width=512,
    height=512,
    # fill="none",
    stroke="currentcolor",
    stroke_linecap="round",
    stroke_linejoin="round",
    stroke_width="1",
)[
    xml.defs[
        marker("red"),
        marker("green"),
        marker("blue")
    ],
    xml.g[
        square_tile(C, R, 0, 0),
        square_neighbours(C, R, 0, 0),
        *axes(R, sx, sy),
    ],
    xml.g(
        transform=function.translate(0, 1.3*CY),
    )[
        parallelogram_tile(C, R, 0, 0),
        parallelogram_neighbours(C, R, 0, 0),
        *axes(R, px, py),
    ],
    xml.g(
        transform=function.translate(0, 3*CY),
    )[
        hexagon_dashed(hc(C, R, 0, 0), R),

        hexagon_dashed(hc(C, R, 1, 0), R),
        hexagon_dashed(hc(C, R, 1, 1), R),
        hexagon_dashed(hc(C, R, 0, 1), R),
        hexagon_dashed(hc(C, R, -1, 0), R),
        hexagon_dashed(hc(C, R, -1, -1), R),
        hexagon_dashed(hc(C, R, 0, -1), R),

        *axes(R, hx, hy),
    ],
    xml.g(
        transform=function.translate(2.5*CX, -0.2*CY),
    )[
        square_grid(C, R/3, 7, 7),
        square_tile(C, R/3, 0, 0, style={"fill": "orange"}),
        square_tile(C, R/3, 6, -3, style={"fill": "dodgerblue"}),
        square_path(C, R/3, PATH),
    ],
    xml.g(
        transform=function.translate(2.5*CX, 1.2*CY),
    )[
        parallelogram_grid(C, R/2.5, 7, 7),
        parallelogram_tile(C, R/2.5, 0, 0, style={"fill": "orange"}),
        parallelogram_tile(C, R/2.5, 6, -3, style={"fill": "dodgerblue"}),
        parallelogram_path(C, R/2.5, PATH),
    ],
    xml.g(
        transform=function.translate(2.5*CX, 2.5*CY),
    )[
        hex_grid(C, R/3, 7, 7),
        hex_tile(C, R/3, 0, 0, style={"fill": "orange"}),
        hex_tile(C, R/3, 6, -3, style={"fill": "dodgerblue"}),
        hex_path(C, R/3, PATH),
    ],
]


if __name__ == "__main__":
    with open("/tmp/hex.svg", mode="w", encoding="utf-8", newline="") as f:
        print(serialize(elify(stringify(svg))), file=f)
