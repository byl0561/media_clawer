"""Shared value objects.

``Rate`` was previously copy-pasted (identically) into all four ``models``
modules. It lives here once. The constructor stays positionally compatible
with the old ``Rate(score, votes, source)`` call sites.
"""
from dataclasses import dataclass

__all__ = ["Rate"]


@dataclass(frozen=True)
class Rate:
    score: float
    votes: int
    source: str
