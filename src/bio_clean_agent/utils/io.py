"""Lightweight I/O helpers for resilient dataset loading."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Optional


def detect_delimiter(sample: str, fallback: str = ",") -> str:
    """Infer a delimiter using csv.Sniffer; fall back gracefully.

    Parameters
    ----------
    sample: str
        Small portion of the file content for inference.
    fallback: str
        Default delimiter when detection fails.
    """

    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=[",", "\t", ";", "|"])
        return dialect.delimiter
    except (csv.Error, TypeError):
        return fallback


def read_text_header(path: str | Path, lines: int = 5) -> str:
    """Read a small header chunk from *path* for delimiter inference."""

    try:
        with Path(path).open("r", encoding="utf-8", errors="ignore") as handle:
            return "".join([handle.readline() for _ in range(lines)])
    except FileNotFoundError:
        return ""


def normalise_paths(paths: Iterable[str | Path]) -> list[str]:
    """Return normalised string versions of the provided *paths*."""

    return [str(Path(item).expanduser().resolve()) for item in paths]
