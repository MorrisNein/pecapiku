from __future__ import annotations

import logging
import os
import pickle
from pathlib import Path
from typing import Any, Literal

from pecapiku.config import config
from pecapiku.no_cache import NoCache

CacheAccess = Literal['r', 're', 'ew', 'rew', 'e']

logger = logging.getLogger(__file__)

COMP_CACHE_FILE_NAME = '_comp_cache.pkl'


def _resolve_filepath(file_path: os.PathLike | str) -> Path:
    if isinstance(file_path, str):
        file_path = Path(file_path)
    if not file_path.is_absolute():
        file_path = config.get_cache_dir() / file_path
    return file_path


def _initialize_cache(file_path: os.PathLike) -> NoCache | Any:
    try:
        logger.info(f'Loading cache file "{file_path}"...')
        with open(file_path, 'rb') as f:
            result = pickle.load(f)
    except FileNotFoundError:
        logger.info(f'File "{file_path}" not found.')
        result = NoCache()
    return result


def update_cache(cache: Any, file_path: Path):
    logger.info(f'Writing cache file "{file_path}"...')
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'wb') as f:
        pickle.dump(cache, f)
