from __future__ import annotations

from pathlib import Path
from typing import Iterable


def estimate_dataset_size(paths: Iterable[str]) -> int:
    total = 0
    for item in paths:
        try:
            total += Path(item).stat().st_size
        except FileNotFoundError:
            continue
    return total


def format_bytes(num_bytes: int) -> str:
    if num_bytes <= 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    idx = 0
    value = float(num_bytes)
    while value >= 1024 and idx < len(units) - 1:
        value /= 1024
        idx += 1
    return f"{value:.2f} {units[idx]}"
