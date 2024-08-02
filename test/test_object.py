import contor.object as co


def test_path():
    assert len(co.coords(co.make_path(1, co.example_path))) ==\
           len(co.example_path)
