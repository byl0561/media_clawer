"""Generic fuzzy-matching kernel.

Every domain previously re-implemented the same O(n*m) "items in A with no
similar item in B" loop. That loop lives here once; each domain supplies its
own similarity predicate (the predicates genuinely differ — year tolerances
and title-normalisation rules are not the same for films, shows, albums and
books) built from the small text helpers below.
"""
import difflib
import re
from typing import Callable, List, Sequence, TypeVar

T = TypeVar("T")
C = TypeVar("C")

__all__ = [
    "find_missing",
    "strip_parentheses",
    "title_ratio",
    "best_title_ratio",
    "title_excluded",
    "drop_excluded",
]

_PAREN_PATTERNS = (
    re.compile(r"\([^)]*\)"),
    re.compile(r"（[^）]*）"),
)


def find_missing(
    targets: Sequence[T],
    compares: Sequence[C],
    is_similar: Callable[[T, C], bool],
) -> List[T]:
    """Return every target that has no similar counterpart in ``compares``."""
    return [t for t in targets if not any(is_similar(t, c) for c in compares)]


def strip_parentheses(text: str, *, ascii_only: bool = False) -> str:
    """Remove ``(...)`` (and, unless ``ascii_only``, ``（...）``) groups."""
    text = _PAREN_PATTERNS[0].sub("", text)
    if not ascii_only:
        text = _PAREN_PATTERNS[1].sub("", text)
    return text


def title_excluded(titles: Sequence[str], excludes: Sequence[str]) -> bool:
    """True iff any of ``titles`` should be ignored per the ``excludes`` list.

    Matching is substring-in-either-direction (case kept) so a user can write
    either the short main title (``银魂`` excludes ``银魂：完结篇``) or the full
    one (``中国少年儿童百科全书`` excludes a folder named ``中国少年儿童百科全书``).
    This is the same lenient rule the book crawler used before exclusions
    became configurable.
    """
    if not excludes:
        return False
    for raw in titles:
        title = (raw or "").strip()
        if not title:
            continue
        for ex in excludes:
            if ex and (ex in title or title in ex):
                return True
    return False


def drop_excluded(items: Sequence[T], excludes: Sequence[str]) -> List[T]:
    """Filter out every item whose ``get_titles()`` matches ``excludes``.

    A no-op (returns a plain list copy) when ``excludes`` is empty, so callers
    can pass it unconditionally.
    """
    if not excludes:
        return list(items)
    return [it for it in items if not title_excluded(it.get_titles(), excludes)]


def title_ratio(a: str, b: str) -> float:
    """Similarity ratio of two pre-normalised titles."""
    return difflib.SequenceMatcher(None, a, b).ratio()


def best_title_ratio(
    a_titles: Sequence[str],
    b_titles: Sequence[str],
    normalize: Callable[[str], str],
) -> float:
    """Highest pairwise ratio across the two title lists after ``normalize``."""
    best = 0.0
    for a in a_titles:
        na = normalize(a)
        for b in b_titles:
            best = max(best, title_ratio(na, normalize(b)))
    return best
