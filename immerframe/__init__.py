from copy import copy
from typing import TypeVar, Any

import attr


T = TypeVar('T')
empty = object()

# todo: rename to Proxy, more tests, publish


@attr.s(auto_attribs=True, frozen=True)
class El:
    type: str  # getattr|getitem|setattr|call
    key: Any = empty
    value: Any = empty
    args: Any = empty
    kwargs: Any = empty


class Path(list):
    def __init__(self):
        self.op = empty
        self.other = empty
        super().__init__()


class Proxy:
    def __init__(self) -> None:
        self._paths = []
        self._current_path = Path()

    def __getattr__(self, key) -> 'Proxy':
        if key in {'_paths', '_current_path'}:
            return self.__dict__[key]
        self._current_path.append(El(type='getattr', key=key))
        return self

    def __getitem__(self, key) -> 'Proxy':
        self._current_path.append(El(type='getitem', key=key))
        return self

    def __setattr__(self, key, value) -> None:
        if key in {'_paths', '_current_path'}:
            self.__dict__[key] = value
            return
        self._current_path.append(El(type='getattr', key=key))
        self._current_path.append(El(type='setattr', value=value))
        self._paths.append(self._current_path)
        self._current_path = Path()

    def __setitem__(self, key, value) -> None:
        self._current_path.append(El(type='getitem', key=key))
        self._current_path.append(El(type='setitem', value=value))
        self._paths.append(self._current_path)
        self._current_path = Path()

    def __call__(self, *args, **kwargs):
        prev_path = self._current_path.pop()
        if prev_path.type != 'getattr':
            raise RuntimeError('Can only call methods on known attributes')
        el = El(type='call', key=prev_path.key, args=args, kwargs=kwargs)
        self._current_path.append(el)
        self._paths.append(self._current_path)
        self._current_path = Path()
        return self

    def __add__(self, other):
        self._current_path.pop()
        self._current_path.op = '__add__'
        self._current_path.other = other

    def __sub__(self, other):
        self._current_path.pop()
        self._current_path.op = '__sub__'
        self._current_path.other = other

    def __mul__(self, other):
        self._current_path.pop()
        self._current_path.op = '__mul__'
        self._current_path.other = other

    def __truediv__(self, other):
        self._current_path.pop()
        self._current_path.op = '__truediv__'
        self._current_path.other = other


def _safe_getitem(obj, key):
    try:
        return obj[key]
    except (KeyError, IndexError):
        return empty


def _get(obj, el):
    gets = {'getattr': getattr, 'getitem': _safe_getitem}
    return gets[el.type](obj, el.key)


def produce(proxy: Any, obj: T) -> T:
    assert proxy._paths, 'Something must be done with the proxy!'
    for path in proxy._paths:
        path = copy(path)
        final = path.pop()
        chain = [obj]
        for el in path:

            gets = {'getattr': getattr, 'getitem': _safe_getitem}
            chain.append(_get(chain[-1], el))

        tip = chain.pop()
        if final.type in {'setattr', 'setitem'}:
            if path.op is empty:
                value = final.value
            else:
                value = getattr(tip, path.op)(path.other)
        elif final.type == 'call':
            # shallow copy, then run whatever mutatey function
            value = copy(tip)
            getattr(value, final.key)(*final.args, **final.kwargs)
        else:
            raise RuntimeError('Final path appears no have no effect')

        for container, el in reversed(list(zip(chain, path))):
            value = _handle(container, el, value)

        obj = value
    return obj


class Lens:
    def __init__(self, proxy):
        self.proxy = proxy

    def get(self, obj):
        for el in self.proxy._current_path:
            obj = _get(obj, el)
        return obj

    def set(self, obj, value):
        # a bit ugly, but does the trick
        self.proxy._current_path.append(El(type='setitem', value=value))
        self.proxy._paths.append(self.proxy._current_path)
        new_obj = produce(self.proxy, obj)
        self.proxy._paths.pop()
        self.proxy._current_path.pop()
        return new_obj


def _is_attr(obj):
    return hasattr(obj, '__attrs_attrs__')


def _handle_attr(obj, path, value):
    new = {n.name: getattr(obj, n.name) for n in obj.__attrs_attrs__}
    new[path.key] = value
    return type(obj)(**new)


plugins = [
    (_is_attr, _handle_attr),
]


def _handle(obj, path, value):
    for switch, handler in plugins:
        if switch(obj):
            return handler(obj, path, value)
    if isinstance(obj, dict):
        new = dict(obj)
        new[path.key] = value
        return new
    if isinstance(obj, list):
        new = list(obj)
        new[path.key] = value
        return new
    if isinstance(obj, tuple):
        if hasattr(obj, '_asdict'):
            new = obj._asdict()
            new[path.key] = value
            return type(obj)(**new)
        return obj[:path.key] + (value,) + obj[path.key + 1:]
    else:
        raise RuntimeError(f"Can't handle objects of type: {type(obj)}")
