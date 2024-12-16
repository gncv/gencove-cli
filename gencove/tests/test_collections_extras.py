"""Tests for collections_extras of Gencove CLI."""
from collections_extras import LazyList


def test_lazy_evaluation():
    """Test that the generator is evaluated lazily."""

    def gen():
        yield 1
        yield 2
        yield 3

    lazy_list = LazyList(gen())
    assert len(lazy_list._cache) == 0  # pylint: disable=protected-access
    assert lazy_list[0] == 1
    assert len(lazy_list._cache) == 1  # pylint: disable=protected-access


def test_indexing():
    """Test indexing access."""

    def gen():
        yield from range(5)

    lazy_list = LazyList(gen())
    assert lazy_list[2] == 2
    assert lazy_list[4] == 4
    try:
        _ = lazy_list[5]
    except IndexError:
        pass
    else:
        assert False, "Expected IndexError not raised"


def test_iteration():
    """Test iteration over the LazyList."""

    def gen():
        yield from range(5)

    lazy_list = LazyList(gen())
    result = list(lazy_list)
    assert result == [0, 1, 2, 3, 4]
    assert len(lazy_list) == 5


def test_caching():
    """Test that values are cached after access."""

    def gen():
        yield from range(3)

    lazy_list = LazyList(gen())
    _ = lazy_list[1]
    assert lazy_list._cache == [0, 1]  # pylint: disable=protected-access


def test_repr():
    """Test the string representation of LazyList."""

    def gen():
        yield 1
        yield 2
        yield 3

    lazy_list = LazyList(gen())
    assert repr(lazy_list) == "LazyList([...])"
    _ = lazy_list[0]
    assert repr(lazy_list) == "LazyList([1] + [...])"
    _ = list(lazy_list)
    assert repr(lazy_list) == "LazyList([1, 2, 3])"


def test_exhaustion():
    """Test behavior after the generator is exhausted."""

    def gen():
        yield from range(3)

    lazy_list = LazyList(gen())
    _ = list(lazy_list)
    assert lazy_list._exhausted  # pylint: disable=protected-access
    try:
        _ = lazy_list[5]
    except IndexError:
        pass
    else:
        assert False, "Expected IndexError not raised"


def test_len():
    """Test the length of LazyList after generator exhaustion."""

    def gen():
        yield from range(4)

    lazy_list = LazyList(gen())
    assert len(lazy_list) == 4


def test_empty_generator():
    """Test LazyList with an empty generator."""

    def gen():
        if False:  # pylint: disable=using-constant-test
            yield

    lazy_list = LazyList(gen())
    assert len(lazy_list) == 0
    try:
        _ = lazy_list[0]
    except IndexError:
        pass
    else:
        assert False, "Expected IndexError not raised"
    assert not list(lazy_list)


def test_large_generator():
    """Test LazyList with a large generator."""

    def gen():
        for i in range(1_000_000):
            yield i + 1

    lazy_list = LazyList(gen())
    assert lazy_list[999] == 1000
    assert len(lazy_list._cache) < 1_000_000  # pylint: disable=protected-access


def test_iter():
    """Test LazyList iterable."""

    def gen_fib():
        fib_a, fib_b = 1, 1
        while fib_a < 10:
            yield fib_a
            fib_a, fib_b = fib_b, fib_b + fib_a

    lazy_list = LazyList(gen_fib())
    for lazy_result, expected_value in zip(lazy_list, [1, 1, 2, 3, 5, 8, 13]):
        assert lazy_result == expected_value
