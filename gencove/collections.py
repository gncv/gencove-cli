from typing import Generator, Generic, List, TypeVar


T = TypeVar("T")


class LazyList(Generic[T]):
    def __init__(self, generator: Generator[T, None, None]):
        self._generator: Generator[T, None, None] = generator
        self._cache: List[T] = []
        self._exhausted: bool = False

    def __getitem__(self, index: int) -> T:
        while not self._exhausted and len(self._cache) <= index:
            try:
                self._cache.append(next(self._generator))
            except StopIteration:
                self._exhausted = True

        if index < len(self._cache):
            return self._cache[index]
        else:
            raise IndexError("LazyList index out of range")

    def __iter__(self):
        for value in self._cache:
            yield value

        while not self._exhausted:
            try:
                value = next(self._generator)
                self._cache.append(value)
                yield value
            except StopIteration:
                self._exhausted = True

    def __len__(self) -> int:
        if not self._exhausted:
            self._cache.extend(self._generator)
            self._exhausted = True
        return len(self._cache)

    def __repr__(self) -> str:
        if self._exhausted:
            return f"LazyList({self._cache})"
        return f"LazyList({self._cache} + [...])" if self._cache else "LazyList([...])"
