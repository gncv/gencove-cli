"""Library functions in Gencove CLI."""

from collections import namedtuple


def namedtuple_dynamic(typename, field_names):
    """Returns a new subclass of tuple with named fields.

    Works like `collections.namedtuple` but allows objects to
    be instantiated with arbitrary `**kwargs`.

    >>> Point = namedtuple_dynamic('Point', ['x', 'y'])
    >>> a = Point(0.7, 0.9, **{"z": 2})
    >>> a
    Point(x=0.7, y=0.9, z=2)
    """

    def lazy(*args, **kwargs):
        valid_kwargs = {k: kwargs[k] for k in kwargs if str(k).isidentifier()}
        fields = list(map(str, field_names))
        new_fields = [str(k) for k in valid_kwargs if k not in fields]
        return namedtuple(typename, fields + new_fields)(
            *args, **valid_kwargs
        )

    # pylint: disable=too-few-public-methods
    class DynamicNamedTuple(namedtuple(typename, field_names)):
        """Dynamic named tuple implementation.

        Allows an object of this class to be instantiated with
        arbitrary `**kwargs`.
        """

        __slots__ = ()

        def __new__(cls, *args, **kwargs):
            return lazy(*args, **kwargs)

    return DynamicNamedTuple
