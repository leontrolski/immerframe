import pytest

from immerframe import El, Path, Proxy, produce, NoAttributeToCallError


# TODO: split up these tests
def test_current_path():
    proxy = Proxy()
    proxy.foo
    assert proxy._current_path == [
        El(type="getattr", key="foo"),
    ]
    assert proxy._paths == []

    proxy = Proxy()
    proxy[0]
    assert proxy._current_path == [
        El(type="getitem", key=0),
    ]
    assert proxy._paths == []

    proxy = Proxy()
    proxy.foo = 42
    assert proxy._current_path == []
    assert proxy._paths == [
        [El(type="getattr", key="foo"), El(type="setattr", value=42),]
    ]

    proxy = Proxy()
    proxy[0] = 42
    assert proxy._current_path == []
    assert proxy._paths == [[El(type="getitem", key=0), El(type="setitem", value=42),]]

    proxy = Proxy()
    with pytest.raises(NoAttributeToCallError):
        proxy()

    proxy = Proxy()
    with pytest.raises(NoAttributeToCallError):
        proxy[0]()

    proxy = Proxy()
    proxy.pop(1, 2, c=3)
    assert proxy._current_path == []
    assert proxy._paths == [[El(type="call", key="pop", args=(1, 2), kwargs={"c": 3}),]]

    proxy = Proxy()
    proxy.foo += 42
    assert proxy._current_path == []
    assert proxy._paths == [
        [El(type="getattr", key="foo"), El(type="setattr", value=None),]
    ]
    assert proxy._paths[0].op == "__add__"
    assert proxy._paths[0].other == 42
