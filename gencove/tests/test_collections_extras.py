"""Tests for collections_extras of Gencove CLI."""
from collections_extras import LazyList


def test_lazy_evaluation():
    """Test that the generator is evaluated lazily."""

    def gen():
        yield 1
        yield 2
        yield 3

    lazy_list = LazyList(gen())
    assert len(lazy_list._cache) == 0  # No values should be cached initially
    assert lazy_list[0] == 1  # Accessing index 0 should cache one value
    assert len(lazy_list._cache) == 1


def test_indexing():
    """Test indexing access."""

    def gen():
        yield from range(5)

    lazy_list = LazyList(gen())
    assert lazy_list[2] == 2  # Accessing index 2 should compute up to index 2
    assert lazy_list[4] == 4  # Accessing the last index of the generator
    try:
        _ = lazy_list[5]  # Accessing out of range should raise IndexError
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
    assert result == [0, 1, 2, 3, 4]  # Iterating should exhaust the generator
    assert len(lazy_list) == 5  # __len__ should reflect the total number of items


def test_caching():
    """Test that values are cached after access."""

    def gen():
        yield from range(3)

    lazy_list = LazyList(gen())
    _ = lazy_list[1]
    assert lazy_list._cache == [0, 1]  # Accessing index 1 should cache 0 and 1


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
    _ = list(lazy_list)  # Exhaust the generator
    assert repr(lazy_list) == "LazyList([1, 2, 3])"


def test_exhaustion():
    """Test behavior after the generator is exhausted."""

    def gen():
        yield from range(3)

    lazy_list = LazyList(gen())
    _ = list(lazy_list)  # Exhaust the generator
    assert lazy_list._exhausted
    try:
        _ = lazy_list[5]  # Accessing beyond available indices raises IndexError
    except IndexError:
        pass
    else:
        assert False, "Expected IndexError not raised"


def test_len():
    """Test the length of LazyList after generator exhaustion."""

    def gen():
        yield from range(4)

    lazy_list = LazyList(gen())
    assert len(lazy_list) == 4  # Should return the correct length after exhaustion


def test_empty_generator():
    """Test LazyList with an empty generator."""

    def gen():
        if False:  # Never yield anything
            yield

    lazy_list = LazyList(gen())
    assert len(lazy_list) == 0
    try:
        _ = lazy_list[0]  # Indexing should fail for an empty generator
    except IndexError:
        pass
    else:
        assert False, "Expected IndexError not raised"
    assert list(lazy_list) == []  # Iterating should return an empty list


def test_large_generator():
    """Test LazyList with a large generator."""

    def gen():
        for i in range(1_000_000):
            yield i

    lazy_list = LazyList(gen())
    assert lazy_list[999] == 1000  # Access a large index
    assert len(lazy_list._cache) < 1_000_000  # Ensure not all values are cached
