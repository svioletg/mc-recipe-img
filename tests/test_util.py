from collections.abc import Iterable

import pytest

from mc_recipe_img import util


@pytest.mark.parametrize(('it', 'expected'),
    [
        ([1, 2, 3, 4, 5], [1, 2, 3, 4, 5]),
        ([1, 2, [3, 4], 5], [1, 2, 3, 4, 5]),
        ([1, 2, [3, 4], 5, [6, 7, [8, 9], 10, [11, [12, [13, [14, 15, 16, 17, [18]]]]]]],
         [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]),
    ],
)
def test_flattened(it: Iterable, expected: list) -> None:
    assert util.flattened(it) == expected

@pytest.mark.parametrize(('it', 'flatten_str', 'expected'),
    [
        (['a', 'b', 'c', 'def'], False, ['a', 'b', 'c', 'def']),
        (['a', 'b', 'c', 'def'], True, ['a', 'b', 'c', 'd', 'e', 'f']),
        (['a', 'b', 'c', 'def', ['g', 'h', 'i', 'jkl']], False, ['a', 'b', 'c', 'def', 'g', 'h', 'i', 'jkl']),
        (['a', 'b', 'c', 'def', ['g', 'h', 'i', 'jkl']], True,
         ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l']),
    ],
)
def test_flattened_with_str(it: Iterable, flatten_str: bool, expected: list) -> None:
    assert util.flattened(it, flatten_str=flatten_str) == expected
