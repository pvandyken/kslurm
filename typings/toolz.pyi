from typing import Iterable, TypeVar


T = TypeVar("T")
def concat(seqs: Iterable[Iterable[T]]) -> Iterable[T]:
    ...