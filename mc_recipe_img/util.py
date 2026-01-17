import os
from collections.abc import Callable, Generator, Iterable
from pathlib import Path


def dict_try_keys[K, V](d: dict[K, V], *keys: K, default: V | None = None) -> V | None:
    """
    Attempts to retrieve a value from a dictionary by trying every key given from left to right, finally returning
    `default` if none were found.
    """
    for k in keys:
        if (v := d.get(k)) is not None:
            return v
    return default

def ensure_list[T](it: T | list[T]) -> list[T]:
    """
    Returns `it` if already a list, otherwise returns a list containing `it` as its only item.
    Note that this will only work for one-dimensional lists, i.e. not lists of lists.
    """
    return it if isinstance(it, list) else [it]

def flattened[T](it: Iterable, typ: type[T] = object, *, flatten_str: bool = False) -> list[T]:
    """
    Flattens nested iterable into a one-dimensional `list` of their items. Since the final depth of these nestings is
    arbitrary, you can specify the list type using the `typ` argument.

    :param flatten_str: Whether to flatten `str` into individual characters, or leave them intact.
    """
    acc = []
    for i in it:
        if isinstance(i, Iterable) and ((not isinstance(i, str)) or (flatten_str and len(i) > 1)):
            acc.extend(flattened(i, typ, flatten_str=flatten_str))
        else:
            acc.append(i)
    return acc

def group_as_dict[T, K, V](it: Iterable[T], fn: Callable[[T], tuple[K, V]]) -> dict[K, list[V]]:
    """
    Groups `it` into a dictionary of lists of its items by calling `fn` on every item and using its return value as the
    keys and values.

    >>> it = ['John Doe', 'Jane Smith', 'Terry Smith', 'William Good', 'Jack Doe']
    >>> by_surname = group_by(it, lambda name: name.split()[0], name)
    >>> assert by_surname == {
        'Doe': ['John Doe', 'Jack Doe'],
        'Smith': ['Jane Smith', 'Terry Smith'],
        'Good': ['William Good']
        }

    >>> it = ['John Doe', 'Jane Smith', 'Terry Smith', 'William Good', 'Jack Doe']
    >>> by_surname = group_by(it, lambda name: tuple(name.split()))
    >>> assert by_surname == {
        'Doe': ['John', 'Jack'],
        'Smith': ['Jane', 'Terry'],
        'Good': ['William']
        }

    :param fn: A function that takes an item from `it`, and returns or two values to use as key and value, where its
        first tuple value is used as a dictionary key, and the second is appended onto a list associated with that key.
    """
    d: dict[K, list[V]] = {}
    for i in it:
        key, value = fn(i)
        if key not in d:
            d[key] = []
        d[key].append(value)
    return d

def partition[T](predicate: Callable[[T], bool], it: Iterable[T]) -> tuple[Generator[T], Generator[T]]:
    """
    Returns two generators in which the left yields all items of `it` for which `predicate(i)` equals `True`, and the
    right yields the opposite.
    """
    return ((i for i in it if predicate(i)), (i for i in it if not predicate(i)))

def partitioned[T](predicate: Callable[[T], bool], it: Iterable[T]) -> tuple[list[T], list[T]]:
    """
    An alternative to `partition` that returns two `list`s instead of generators.

    Sorts the items of `it` into two lists by their outcome of being passed to `predicate`.
    The left list contains all items in `it` for which `predicate(i)` equals `True`, and the right list contains the
    opposite.
    """
    passed: list[T] = []
    failed: list[T] = []
    for i in it:
        (passed if predicate(i) else failed).append(i)
    return (passed, failed)

def parse_envvar_paths(key: str, *, delim: str = ':', strict: bool = False) -> list[Path]:
    """
    Parses the value of an environment variable into a list of paths, splitting based on `delim`. An empty list is
    returned if the variable is unset.

    :param strict: If `True`, `FileNotFoundError` is raised is any paths in the list do not exist.
    """
    value: str | None = os.getenv(key)
    if value is None:
        return []
    paths: list[Path] = [Path(fp.strip()) for fp in value.split(delim)]
    if strict and (missing := [str(fp) for fp in paths if not fp.exists()]):
        raise FileNotFoundError(', '.join(missing))
    return paths
