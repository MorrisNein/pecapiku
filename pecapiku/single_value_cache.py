from __future__ import annotations

import os
from functools import partial, wraps
from typing import Any, Callable, Hashable, Type, TypeVar

from pecapiku.base_cache import BaseCache, DecoratedCallable, omnimethod
from pecapiku.cache_access import CacheAccess, _initialize_cache, _resolve_filepath, update_cache
from pecapiku.no_cache import NoCache


class SingleValueCache(BaseCache):
    """ Decorator for caching of evaluation results.
    Creates a "pickle" file at disk space on a specified path.
    Wraps a function and stores its execution result in the file.
    To apply, use the method ``SingleValueCache.decorate()`` or ``SingleValueCache(...)()``.

    Args:

        file_path - a path to an existing or non-existent pickle file.
            If a relative path or a filename is given, puts it into the framework cache directory.

        access - cache access indicators. The string may include the following indicators:
            - ``r`` - read - grants access to read the cache file content
            - ``e`` - execute/evaluate - grants access to evaluate the decorated function (if such is present)
            - ``w`` - write - grants access to modify the cache file content

    Example
    -------
    >>> import time
    >>> from timeit import timeit
    >>> def a_heavy_function():
    ...     time.sleep(1)
    ...
    ... @SingleValueCache('a_heavy_function.pkl')  # or @SingleValueCache.decorate(file_path='a_heavy_function.pkl')
    >>> def a_heavy_function_cached():
    ...     time.sleep(1)
    >>> print(timeit(a_heavy_function, number=10))  # 10.070
    >>> print(timeit(a_heavy_function_cached, number=10))  # 1.015
    """

    def __init__(self, file_path: os.PathLike | str | None = None, access: CacheAccess = 'rew'):
        super().__init__(file_path, access)
        self.cache_dict = None

    def __call__(self,
                 func: DecoratedCallable,
                 file_path: os.PathLike | str | None = None,
                 access: CacheAccess = 'rew') -> DecoratedCallable:
        return self.decorate(func, file_path, access)

    def get_cache_val(self, key: Hashable) -> Any:
        return _initialize_cache(self.file_path)

    def put_cache_val(self, key: Hashable, value: Any):
        return update_cache(value, self.file_path)

    def key_func(self, *args, **kwargs) -> Hashable:
        return 0

    @classmethod
    def _decorate(cls, func: DecoratedCallable,
                  file_path: os.PathLike | str | None = None,
                  access: CacheAccess = 'rew') -> DecoratedCallable:
        """ Wraps a function and stores its execution results into a pickle cache file.

        Example
        -------
        >>> import time
        >>> from timeit import timeit
        >>> def a_heavy_function():
        ...     time.sleep(1)
        ...     return 42
        ...
        >>> cached_func = SingleValueCache.decorate(a_heavy_function,'a_heavy_function.pkl')
        >>> print(timeit(a_heavy_function, number=10))  # 10.070
        >>> print(timeit(cached_func, number=10))  # 1.015

        Params:

            func - a function to decorate.

            file_path - a path to an existing or non-existent pickle file.
                If a relative path or a filename is given, puts it into the framework cache directory.

            access - cache access indicators. The string may include the following indicators:
                - ``r`` - read - grants access to read the cache file content
                - ``e`` - execute/evaluate - grants access to evaluate the decorated function
                - ``w`` - write - grants access to modify the cache file content
        """
        if file_path is None:
            raise ValueError(f'A "file_path" should be specified for "{cls.__name__}", got "None".')
        file_path = _resolve_filepath(file_path)

        @wraps(func)
        def decorated(*args, **kwargs):
            instance = cls(file_path, access)
            val = instance._read_execute_write(func, func_args=args, func_kwargs=kwargs, access=access)
            return val

        decorator_return = decorated
        if func is None:
            decorator_return = partial(cls.decorate, file_path=file_path, access=access)
        return decorator_return

    @staticmethod
    def get(file_path: os.PathLike | str) -> NoCache | Any:
        file_path = _resolve_filepath(file_path)
        return _initialize_cache(file_path)

    @omnimethod
    def decorate(self, func: DecoratedCallable, file_path: os.PathLike | str | None = None,
                 access: CacheAccess = 'rew', **kwargs) -> DecoratedCallable:
        """ Wraps a function and stores its execution results into a pickle cache file.

        Example
        --------
        >>> import time
        >>> from timeit import timeit
        >>> def a_heavy_function():
        ...     time.sleep(1)
        ...     return 42
        ...
        >>> cached_func = SingleValueCache.decorate(a_heavy_function,'a_heavy_function.pkl')
        >>> print(timeit(a_heavy_function, number=10))  # 10.070
        >>> print(timeit(cached_func, number=10))  # 1.015

        Params:

            func - a function to decorate.

            file_path - a path to an existing or non-existent pickle file.
                If a relative path or a filename is given, puts it into the framework cache directory.

            access - cache access indicators. The string may include the following indicators:
                - ``r`` - read - grants access to read the cache file content
                - ``e`` - execute/evaluate - grants access to evaluate the decorated function
                - ``w`` - write - grants access to modify the cache file content
        """
        return super().decorate(
            func=func,
            file_path=file_path,
            access=access
        )
