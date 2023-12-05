from pathlib import Path

import pytest

from pecapiku import config


def get_project_root():
    return Path(__file__).parents[1]


@pytest.fixture(scope='function', autouse=True)
def set_cache_dir():
    cache_dir = get_project_root() / 'tests' / '.proj_cache'
    config.set_cache_dir(cache_dir)
    yield
    [f.unlink() for f in cache_dir.glob("*") if f.is_file()]


@pytest.fixture(scope='function')
def get_cache_dir(set_cache_dir):
    cache_dir = config.get_cache_dir()
    return cache_dir
