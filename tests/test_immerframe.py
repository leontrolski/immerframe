from dataclasses import dataclass

import attr
from immerframe import Proxy, produce


def test_list():
    l = [1, 2, 3, 4]

    proxy = Proxy()
    proxy[1] = "foo"
    proxy.pop()
    new_l = produce(proxy, l)

    assert new_l == [1, "foo", 3]
    assert l == [1, 2, 3, 4]


def test_set():
    l = {1, 2, 3}

    proxy = Proxy()
    proxy.add("foo")
    new_l = produce(proxy, l)

    assert new_l == {1, 2, 3, "foo"}
    assert l == {1, 2, 3}


def test_dict():
    d = {"foo": 1, "bar": 2}

    proxy = Proxy()
    proxy["foo"] = 100
    proxy["bar"] += 1
    new_d = produce(proxy, d)

    assert new_d == {"foo": 100, "bar": 3}
    assert d == {"foo": 1, "bar": 2}


def test_dataclass():
    @dataclass
    class Cat:
        name: str

    cat = Cat(name="Mary")

    proxy = Proxy()
    proxy.name = "Sam"
    new_cat = produce(proxy, cat)

    assert new_cat == Cat(name="Sam")


def test_attr():
    @attr.s(auto_attribs=True)
    class Dog:
        bark: str

    dog = Dog(bark="woof")

    proxy = Proxy()
    proxy.bark = "ruff"
    new_dog = produce(proxy, dog)

    assert new_dog == Dog(bark="ruff")
    assert dog == Dog(bark="woof")


def test_nested():
    @dataclass
    class Ant:
        age: int

    nested = {
        "foo": [Ant(age=2), "bar",],
    }

    proxy = Proxy()
    proxy["foo"][0].age += 1
    proxy["foo"].pop()
    proxy["qux"] = 99
    new_nested = produce(proxy, nested)

    assert new_nested == {
        "foo": [Ant(age=3),],
        "qux": 99,
    }
    assert nested == {
        "foo": [Ant(age=2), "bar",],
    }


def test_sharing():
    d = {"foo": 1}
    l = [d]

    proxy = Proxy()
    proxy.append(100)
    new_l = produce(proxy, l)
    assert new_l == [d, 100]
    assert new_l[0] is d
    assert l == [d]


def test_can_operate_on_proxy_made_objects():
    l = [1, 2, 3]

    proxy = Proxy()
    proxy[1] = []
    proxy[1].append(4)
    proxy[1].append(5)

    new_l = produce(proxy, l)
    assert new_l == [1, [4, 5], 3]


def test_use_proxy_twice():
    l = [1, 2, 3]

    proxy = Proxy()
    proxy[1] = "foo"

    new_l = produce(proxy, l)
    assert new_l == [1, "foo", 3]

    new_l = produce(proxy, l)
    assert new_l == [1, "foo", 3]


def test_use_value_arg():
    l = [1, 2, 3, 4]

    proxy = Proxy(l)
    proxy[1] = "foo"
    proxy.pop()
    new_l = produce(proxy)

    assert new_l == [1, "foo", 3]
    assert l == [1, 2, 3, 4]


def test_context_list():
    l = [1, 2, 3, 4]

    with Proxy(l) as (_, new_l):
        _[1] = "foo"
        _.pop()

    assert new_l == [1, "foo", 3]
    assert l == [1, 2, 3, 4]


def test_context_set():
    l = {1, 2}

    with Proxy(l) as (_, new_l):
        _.add("foo")
        _.remove(2)

    assert new_l == {1, "foo"}
    assert l == {1, 2}


def test_context_dict():
    l = {1: 2}

    with Proxy(l) as (_, new_l):
        _[3] = 4

    assert l == {1: 2}
    assert new_l == {1: 2, 3: 4}


def test_context_attr():
    @attr.s(auto_attribs=True)
    class Dog:
        bark: str

    dog = Dog(bark="woof")

    with Proxy(dog) as (_, new_dog):
        _.bark = "baa"

    assert new_dog == Dog("baa")
    assert dog == Dog("woof")


def test_context_dataclass():
    @dataclass
    class Dog:
        bark: str

    dog = Dog(bark="woof")

    with Proxy(dog) as (_, new_dog):
        _.bark = "baa"

    assert new_dog == Dog("baa")
    assert dog == Dog("woof")


def test_context_nested() -> None:
    @dataclass
    class Ant:
        age: int

    ant_10 = Ant(age=10)
    ant_20 = Ant(age=20)
    nested = {
        "ants": [ant_10, ant_20, None],
    }

    with Proxy(nested) as (p, new_nested):
        p["ants"][0].age += 1
        p["ants"].pop()
        p["foo"] = 99

    assert nested == {
        "ants": [ant_10, ant_20, None],
    }
    assert new_nested == {
        "ants": [Ant(age=11), ant_20],
        "foo": 99,
    }
    assert new_nested["ants"][1] is ant_20


def test_context_nested_and_loopy():
    @dataclass
    class Ant:
        age: int
        is_young: bool = False

    ant_10 = Ant(age=10)
    ant_20 = Ant(age=20)

    nested = {
        "ants": [ant_10, ant_20, None],
    }

    with Proxy(nested) as (p, new_nested):
        p["ants"][0].age += 1
        p["ants"].pop()
        p["foo"] = 99

    with Proxy(new_nested) as (p, new_nested):
        for k in new_nested:
            if isinstance(new_nested[k], int):
                # note about setting values over and over
                p[k] += 1

    with Proxy(new_nested) as (p, new_nested):
        for i, n in enumerate(new_nested["ants"]):
            if n is None:
                continue
            if n.age < 15:
                p["ants"][i].is_young = True

    assert nested == {
        "ants": [ant_10, ant_20, None],
    }
    assert new_nested == {
        "ants": [Ant(age=11, is_young=True), ant_20],
        "foo": 100,
    }
    assert new_nested["ants"][1] is ant_20
