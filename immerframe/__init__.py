from copy import copy
from dataclasses import dataclass, fields, is_dataclass
from typing import TypeVar, Any, Generic, List, Optional, Tuple, Union, cast

import attr


T = TypeVar("T")


class Empty:
    def __repr__(self) -> str:
        return "<empty>"


empty = Empty()


class ImmerframeError(RuntimeError):
    pass


class NoAttributeToCallError(ImmerframeError):
    pass


class ProduceError(ImmerframeError):
    pass


class HandleTypeError(ImmerframeError):
    pass


@dataclass(frozen=True)
class El:
    type: str  # getattr|getitem|setattr|call
    key: Any = empty
    value: Any = empty
    args: Any = empty
    kwargs: Any = empty


class Path(List[El]):
    def __init__(self) -> None:
        self.op: Union[str, Empty] = empty
        self.other: Any = empty
        super().__init__()


class Proxy(Generic[T]):
    def __init__(self, value: T = None) -> None:
        self._value = value
        self._return_value: T = empty
        if value is not None:
            self._return_value = copy(self._value)
        self._paths: List[Path] = []
        self._current_path = Path()

    def __repr__(self) -> str:
        return f"<Proxy of: {self._value}>"

    def __enter__(self) -> Tuple[T, T]:  # the typing here is a lie on-purpose
        return cast(T, self), self._return_value

    def __exit__(self, type, value, tb):
        final_value = produce(self)
        v = self._return_value
        if isinstance(v, list):
            v.clear()
            v.extend(final_value)
        elif isinstance(v, (dict, set)):
            v.clear()
            v.update(final_value)
        elif is_dataclass(v):
            for field in fields(v):
                value = getattr(final_value, field.name)
                setattr(v, field.name, value)
        else:  # assume attrs
            for field in attr.fields(v.__class__):
                value = getattr(final_value, field.name)
                setattr(v, field.name, value)

    def _terminate_current_path(self) -> None:
        self._paths.append(self._current_path)
        self._current_path = Path()

    def __getattr__(self, key: str) -> "Proxy":
        self._current_path.append(El(type="getattr", key=key))
        return self

    def __getitem__(self, key: Any) -> "Proxy":
        self._current_path.append(El(type="getitem", key=key))
        return self

    def __setattr__(self, key: str, value: Any) -> None:
        if key in {
            "_value",
            "_return_value",
            "_paths",
            "_current_path",
            "_terminate_current_path",
        }:
            self.__dict__[key] = value
            return
        self._current_path.append(El(type="getattr", key=key))
        self._current_path.append(El(type="setattr", value=value))
        self._terminate_current_path()

    def __setitem__(self, key: Any, value: Any) -> None:
        self._current_path.append(El(type="getitem", key=key))
        self._current_path.append(El(type="setitem", value=value))
        self._terminate_current_path()

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        if not self._current_path:
            raise NoAttributeToCallError("cannot call an unmodified Proxy object")
        prev_path = self._current_path.pop()
        if prev_path.type != "getattr":
            raise NoAttributeToCallError("can only call methods on known attributes")

        el = El(type="call", key=prev_path.key, args=args, kwargs=kwargs)
        self._current_path.append(el)
        self._terminate_current_path()

    # TODO: fill in all the magic methods
    def __add__(self, other: Any) -> None:
        self._current_path.pop()
        self._current_path.op = "__add__"
        self._current_path.other = other

    def __sub__(self, other: Any) -> None:
        self._current_path.pop()
        self._current_path.op = "__sub__"
        self._current_path.other = other

    def __mul__(self, other: Any) -> None:
        self._current_path.pop()
        self._current_path.op = "__mul__"
        self._current_path.other = other

    def __truediv__(self, other: Any) -> None:
        self._current_path.pop()
        self._current_path.op = "__truediv__"
        self._current_path.other = other


def _safe_getitem(obj: Any, key: Any) -> Any:
    try:
        return obj[key]
    except (KeyError, IndexError):
        return empty


def _get(obj: Any, el: El) -> Any:
    gets = {"getattr": getattr, "getitem": _safe_getitem}
    return gets[el.type](obj, el.key)


def produce(proxy: Proxy, obj: Optional[T] = None) -> T:
    if obj is None:
        obj = proxy._value
    for path_ in proxy._paths:
        op, other = path_.op, path_.other
        *path, final = path_

        chain = [obj]
        for el in path:
            *_, tip = chain
            chain.append(_get(tip, el))

        tip = chain.pop()
        if final.type in {"setattr", "setitem"}:
            if op is empty:
                value = final.value
            else:
                value = getattr(tip, op)(other)
        elif final.type == "call":
            # shallow copy, then run whatever mutatey function
            value = copy(tip)
            getattr(value, final.key)(*final.args, **final.kwargs)
        else:
            raise ProduceError("final path appears no have no effect")

        for inner_obj, el in reversed(list(zip(chain, path))):
            value = _copy_and_set(inner_obj, el, value)

        obj = value
    return obj


def _copy_and_set(obj: T, el: El, value: Any) -> T:
    new = copy(obj)
    if isinstance(obj, (dict, list)):
        new[el.key] = value
        return new
    setattr(new, el.key, value)
    return new
