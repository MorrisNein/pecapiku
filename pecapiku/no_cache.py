from __future__ import annotations


class NoCache:
    def __bool__(self):
        return False

    def __eq__(self, other) -> bool:
        return isinstance(other, NoCache)

    def __repr__(self):
        return '<NoCache object>'
