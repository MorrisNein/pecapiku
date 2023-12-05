from pecapiku import config
from tests.conftest import get_project_root, set_cache_dir  # noqa


def test_cache_dir():
    current_cache_dir = config.get_cache_dir()
    expected_cache_dir = get_project_root() / 'tests' / '.proj_cache'
    assert current_cache_dir == expected_cache_dir
