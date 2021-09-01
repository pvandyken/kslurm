def first(seq):
    """ The first element in a sequence

    >>> first('ABC')
    'A'
    """
    return next(iter(seq))

def second(seq):
    """ The second element in a sequence

    >>> second('ABC')
    'B'
    """
    seq = iter(seq)
    next(seq)
    return next(seq)


def count(seq):
    """ Count the number of items in seq

    Like the builtin ``len`` but works on lazy sequences.

    Not to be confused with ``itertools.count``

    See also:
        len
    """
    if hasattr(seq, '__len__'):
        return len(seq)
    return sum(1 for i in seq)