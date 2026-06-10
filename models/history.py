"""
models/history.py
-----------------
Undo/redo stack as JSON snapshots of the Lattice state.
"""

from __future__ import annotations
from typing import Optional


class LatticeHistory:
    """
    Linear undo/redo stack.
    _stack[_index] is the current state.
    Branching edits truncate the redo stack.
    """

    MAX_DEPTH = 50

    def __init__(self):
        self._stack: list[dict] = []
        self._index: int = -1

    def push(self, state: dict):
        """
        Record a new state.  Discards any redo history beyond current index.
        Trims to MAX_DEPTH.
        """
        # Truncate redo branch
        if self._index < len(self._stack) - 1:
            self._stack = self._stack[: self._index + 1]

        self._stack.append(state)
        self._index = len(self._stack) - 1

        # Trim oldest
        if len(self._stack) > self.MAX_DEPTH:
            trim = len(self._stack) - self.MAX_DEPTH
            self._stack = self._stack[trim:]
            self._index = len(self._stack) - 1

    def undo(self) -> Optional[dict]:
        """Move back one step. Returns state to restore, or None."""
        if not self.can_undo():
            return None
        self._index -= 1
        return self._stack[self._index]

    def redo(self) -> Optional[dict]:
        """Move forward one step. Returns state to restore, or None."""
        if not self.can_redo():
            return None
        self._index += 1
        return self._stack[self._index]

    def can_undo(self) -> bool:
        return self._index > 0

    def can_redo(self) -> bool:
        return self._index < len(self._stack) - 1

    def clear(self):
        self._stack.clear()
        self._index = -1

    @property
    def depth(self) -> int:
        return len(self._stack)
