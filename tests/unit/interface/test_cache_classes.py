from functools import wraps
from itertools import product
from time import sleep, time
from typing import Any

import pytest

from pecapiku import CacheDict, SingleValueCache
from tests.conftest import get_cache_dir, set_cache_dir  # noqa


class TestObject:
    def __init__(self, foo: Any):
        self.foo = foo

    def sleep(self, time_: float) -> float:
        sleep(time_)
        return time_


class TestObjectWithCounter:
    def __init__(self, foo: Any):
        self.foo = foo
        self.counter = 0

    def sleep(self, time_: float) -> float:
        self.counter += 1
        sleep(time_)
        return time_


def sleep_(time_: float):
    sleep(time_)
    return time_


def timed(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        t1 = time()
        res = func(*args, **kwargs)
        t2 = time()
        t = t2 - t1
        return res, t

    return wrapper


@pytest.mark.parametrize('sleep_func', [sleep_, TestObject(1).sleep])
@pytest.mark.parametrize('cache_decorator, cache_kwargs',
                         [
                             *product([SingleValueCache(), SingleValueCache.decorate], [dict(file_path='some.pkl')]),
                             *product([CacheDict(), CacheDict.decorate], [{}]),
                         ]
                         )
@pytest.mark.parametrize('wrapper_syntax', ['definition', 'runtime'])
def test_decorators(sleep_func, cache_decorator, cache_kwargs, get_cache_dir, wrapper_syntax):
    if wrapper_syntax == 'definition':
        @timed
        @cache_decorator(**cache_kwargs)
        def cached_sleep(*args, **kwargs):
            return sleep_func(*args, **kwargs)
    elif wrapper_syntax == 'runtime':
        cached_sleep = cache_decorator(sleep_func, **cache_kwargs)
        cached_sleep = timed(cached_sleep)
    else:
        raise ValueError(f'Unexpected value: {wrapper_syntax}')

    plan = 0.1
    plan_return, fact = cached_sleep(plan)
    cache_files = set(get_cache_dir.iterdir())

    assert plan_return == plan
    assert fact > plan
    assert cache_files

    plan_return, fact = cached_sleep(plan)
    cache_files_2 = set(get_cache_dir.iterdir())

    assert plan_return == plan
    assert fact < plan
    assert cache_files == cache_files_2


@pytest.mark.parametrize('cache_decorator, cache_kwargs',
                         [
                             *product([CacheDict(), CacheDict.decorate], [{}]),
                         ]
                         )
def test_method_of_changing_object(cache_decorator, cache_kwargs, get_cache_dir):
    test_object = TestObjectWithCounter(1)
    test_object.sleep = cache_decorator(test_object.sleep, **cache_kwargs)
    test_object.sleep = timed(test_object.sleep)

    val_1, t_1 = test_object.sleep(0.1)
    val_2, t_2 = test_object.sleep(0.1)

    assert t_1 > 0.1
    assert t_2 > 0.1
    assert val_1 == val_2
    assert test_object.counter == 2
    assert set(get_cache_dir.iterdir())


def test_context_manager(get_cache_dir):
    key, val = 'key', 'val'
    with CacheDict() as c_d:
        c_d[key] = val

    with CacheDict() as c_d:
        val_other = c_d[key]
    assert val == val_other
    assert set(get_cache_dir.iterdir())
