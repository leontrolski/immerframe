# immerframe
Create the next immutable object by simply modifying the current one

*This is a Python port of [immer](https://github.com/mweststrate/immer).*

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

"What about my typing?":

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


## Plugins:

`immerframe` currently has an `attrs` plugin, registering plugins is pretty easy, just mutate the `immerframe.plugins` list (see [here](https://github.com/leontrolski/immerframe/blob/master/immerframe/__init__.py#L134) for the structure of the existing attr plugin).

