import contor.object as co


example_path = [
    (0, 0),
    (1, 0),
    (1, 1),
]


def test_path():
    assert len(co.coords(co.make_path(1, example_path))) ==\
           len(example_path)
