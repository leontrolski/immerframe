# immerframe
Create the next immutable object by simply modifying the current one

*This is a Python port of [immer](https://github.com/mweststrate/immer).*

```bash
pip install immerframe
```

Want to do a deep update on a Python data structure without mutating it? No problem:

```python
from immerframe import Proxy, produce

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
```

`new_nested` will now equal

```python
{
    'foo': [
        Ant(age=3),
    ],
    'qux': 99,
}
```

while `nested` will remain unchanged.

"What about my typing?"

```python
from typing import cast

Cat = namedtuple('Cat', 'name')

proxy = cast(Cat, Proxy())
# continue as before but with autocomplete and type checking!
proxy.name = 'Felix'
```

`immerframe` uses structural sharing, so should be efficient in most cases:

```python
d = {'foo': 1}
l = [d]

proxy = Proxy()
proxy.append(100)
new_l = produce(proxy, l)
assert new_l == [d, 100]
assert new_l[0] is d
```

`immerframe` supports:

- `dict`s
- `list`s
- `set`s
- `tuples`s
- `namedtuples`s
- `attrs`s

## `Lens`

`immerframe` comes with a `Lens` class to help with path reuse, it has `.get`, `.set`, `.modify`:

```python
d = {'foo': [1, 2, 3, 4]}

lens = Lens(Proxy()['foo'][1])

new_d = lens.set(d, 100)
assert new_d == {'foo': [1, 100, 3, 4]}
assert d == {'foo': [1, 2, 3, 4]}
assert lens.get(d) == 2

another_d = lens.modify(d, lambda n: n + 1000)
assert another_d == {'foo': [1, 1002, 3, 4]}
```

`Lens`s are composable via their `.proxy()` method, (this duplicates of the originally provided proxy) `Lens(Lens(Proxy()['foo']).proxy()[1])` is equivalent to `Lens(Proxy()['foo'][1])`.

## Plugins:

`immerframe` currently has an `attrs` plugin, registering plugins is pretty easy, just mutate the `immerframe.plugins` list (see [here](https://github.com/leontrolski/immerframe/blob/master/immerframe/__init__.py#L171) for the structure of the existing attr plugin).
