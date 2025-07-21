from typing import List, Set, TypeVar


T = TypeVar("T")


def uniq(xs: List[T]) -> List[T]:
    """
    Returns a list with unique elements from the input list.
    The order of elements is preserved.

    Example:
    >>> uniq([1, 2, 2, 3, 4, 4])
    [1, 2, 3, 4]
    """
    seen: Set[T] = set()
    return [x for x in xs if not (x in seen or seen.add(x))]
