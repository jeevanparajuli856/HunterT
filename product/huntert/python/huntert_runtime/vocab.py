"""Runtime vocabulary helpers for HunterT bundle inference."""

from __future__ import annotations


class RuntimeVocab:
    """A minimal replacement for the torchtext vocabulary interface used at inference."""

    def __init__(self, tokens: list[str], default_index: int = 0) -> None:
        self._tokens = list(tokens)
        self._stoi = {token: index for index, token in enumerate(self._tokens)}
        self._default_index = default_index

    def __len__(self) -> int:
        return len(self._tokens)

    def __getitem__(self, token: str) -> int:
        return self._stoi.get(token, self._default_index)

    def __contains__(self, token: str) -> bool:
        return token in self._stoi

    def get_itos(self) -> list[str]:
        return list(self._tokens)

    @property
    def stoi(self) -> dict[str, int]:
        return dict(self._stoi)
