# immerframe

Intuitively perform deep updates on python objects
- without mutating them
- while being efficient via structural sharing - no `deepcopy`
- while maintaining type correctness

*This is (almost) a Python port of [immer](https://github.com/mweststrate/immer).*

```bash
pip install immerframe
```

First, let's import some stuff

```
from dataclasses import dataclass
from immerframe import Proxy
```

Now, consider the data:

```python
@dataclass
class Ant:
    age: int

ant_10 = Ant(age=10)
ant_20 = Ant(age=20)
nested = {
    "ants": [ant_10, ant_20, None],
}
```

let's pretend to mutate it

```python
with Proxy(nested) as (p, new_nested):
    p["ants"][0].age += 1
    p["ants"].pop()
    p["foo"] = 99
```

(note `p` and `new_nested` should have the correct types in mypy)


`nested` will remain the same

```python
assert nested == {
    "ants": [ant_10, ant_20, None],
}
```

`new_nested` will be `nested`, but with the mutations with specified in the `with Proxy(...)` block

assert new_nested == {
    "ants": [Ant(age=11), ant_20],
    "foo": 99,
}
```

but it _won't_ be a deep copy

```python
assert new_nested["ants"][1] is ant_20
```

`immerframe` supports most thing's that can be `copy`ed

## Things to remember

#### Mutating the same thing in a block twice may not do what you'd expect in the following type of case:

```python
with Proxy([1]) as (l, new_l):
    l[0] += 5
    l[0] += 10
```

will give `l == [11]`

#### Use keys rather than references to loop over and mutate nested `dict`s/`list`s:

```python
with Proxy(new_nested) as (p, new_nested):
    for k in new_nested:
        p[k] += 1
    for i, n in enumerate(new_nested["ants"]):
        if n.age < 15:
            p["ants"][i].age + 10
```


### TODO

- implement all dunder methods
- finish typing
