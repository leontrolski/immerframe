from contextlib import contextmanager


@contextmanager
def foo():
    yield 2, 3


b = 5

with foo() as (a, b):
    print(a, b)
