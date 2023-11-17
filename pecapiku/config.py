from __future__ import annotations

import os
import tempfile
from pathlib import Path

DEFAULT_CACHE_DIR = Path(tempfile.gettempdir()) / 'pecapiku'


class Config:
    def __init__(self):
        self.cache_dir = DEFAULT_CACHE_DIR

    def set_cache_dir(self, cache_dir: str | os.PathLike):
        self.cache_dir = Path(cache_dir)

    def get_cache_dir(self) -> Path:
        return self.cache_dir


config = Config()
