from collections import namedtuple

import attr
from immerframe import Lens, Proxy, produce


def test_list():
    l = [1, 2, 3, 4]

    proxy = Proxy()
    proxy[1] = 'foo'
    proxy.pop()
    new_l = produce(proxy, l)

    assert new_l == [1, 'foo', 3]
    assert l == [1, 2, 3, 4]


def test_tuple():
    l = (1, 2, 3)

    proxy = Proxy()
    proxy[1] = 'foo'
    new_l = produce(proxy, l)

    assert new_l == (1, 'foo', 3)
    assert l == (1, 2, 3)


def test_set():
    l = {1, 2, 3}

    proxy = Proxy()
    proxy.add('foo')
    new_l = produce(proxy, l)

    assert new_l == {1, 2, 3, 'foo'}
    assert l == {1, 2, 3}


def test_dict():
    d = {'foo': 1, 'bar': 2}

    proxy = Proxy()
    proxy['foo'] = 100
    proxy['bar'] += 1
    new_d = produce(proxy, d)

    assert new_d == {'foo': 100, 'bar': 3}
    assert d == {'foo': 1, 'bar': 2}


def test_namedtuple():
    Cat = namedtuple('Cat', 'name')
    cat = Cat(name='Mary')

    proxy = Proxy()
    proxy.name = 'Sam'
    new_cat = produce(proxy, cat)

    assert new_cat == Cat(name='Sam')


def test_attr():
    @attr.s(auto_attribs=True)
    class Dog:
        bark: str

    dog = Dog(bark='woof')

    proxy = Proxy()
    proxy.bark = 'ruff'
    new_dog = produce(proxy, dog)

    assert new_dog == Dog(bark='ruff')
    assert dog == Dog(bark='woof')


def test_nested():
    Ant = namedtuple('Ant', 'age')
    nested = {
        'foo': [
            Ant(age=2),
            'bar',
        ],
    }

    proxy = Proxy()
    proxy['foo'][0].age += 1
    proxy['foo'].pop()
    proxy['qux'] = 99
    new_nested = produce(proxy, nested)

    assert new_nested == {
        'foo': [
            Ant(age=3),
        ],
        'qux': 99,
    }
    assert nested == {
        'foo': [
            Ant(age=2),
            'bar',
        ],
    }


def test_sharing():
    d = {'foo': 1}
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
    proxy[1] = 'foo'

    new_l = produce(proxy, l)
    assert new_l == [1, 'foo', 3]

    new_l = produce(proxy, l)
    assert new_l == [1, 'foo', 3]


def test_lens():
    d = {'foo': [1, 2, 3, 4]}

    lens = Lens(Proxy()['foo'][1])
    new_d = lens.set(d, 100)
    assert d == {'foo': [1, 2, 3, 4]}
    assert new_d == {'foo': [1, 100, 3, 4]}
    assert lens.get(d) == 2
