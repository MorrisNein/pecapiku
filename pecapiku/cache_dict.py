from __future__ import annotations

import logging
import os
from collections import defaultdict
from functools import partial, wraps
from inspect import getcallargs, ismethod, signature
from typing import Any, Callable, Generic, Hashable

from pecapiku.base_cache import BaseCache, DecoratedCallable, Decorator, omnimethod
from pecapiku.cache_access import COMP_CACHE_FILE_NAME, CacheAccess, _initialize_cache, _resolve_filepath, update_cache
from pecapiku.hash import get_hash
from pecapiku.no_cache import NoCache

logger = logging.getLogger(__file__)


class MyDefaultDict(defaultdict):
    """ A more consistent type of ``defaultdict`` that returns default value on ``get()``,
    unlike native ``defaultdict``.
    """

    def get(self, __key):
        return self.__getitem__(__key)

    def __repr__(self):
        return dict.__repr__(self)


def initialize_cache_dict(file_path: os.PathLike) -> MyDefaultDict:
    cache_dict = _initialize_cache(file_path)
    if isinstance(cache_dict, NoCache):
        logger.info('Creating a new cache dict...')
        cache_dict = MyDefaultDict(NoCache)
    elif not isinstance(cache_dict, MyDefaultDict):
        raise ValueError(f'File "{file_path}" contains value of type "{type(cache_dict)}", not MyDefaultDict.'
                         ' Rename or delete it beforehand.')
    return cache_dict


def parse_key(callable_or_code: Callable[[Any], Hashable] | str, func: Callable, *args, **kwargs) -> Hashable:
    if callable(callable_or_code):
        sign_params = signature(callable_or_code).parameters
    elif isinstance(callable_or_code, str):
        sign_params = callable_or_code
    else:
        raise ValueError(f'Inner key should be either string or callable, got {type(callable_or_code)}.')

    if 'args' in sign_params or 'kwargs' in sign_params:
        input_kwargs = dict(args=args, kwargs=kwargs)
    else:
        input_kwargs = getcallargs(func, *args, **kwargs)

    if callable(callable_or_code):
        key = callable_or_code(**input_kwargs)
    else:
        key = eval(callable_or_code, None, input_kwargs)
    return key


class CacheDict(BaseCache, Generic[DecoratedCallable]):
    """ Decorator/context manager for caching of evaluation results.
    Creates a "pickle" file at disk space on a specified path.

    If used as a context, provides a dictionary to put/read values in.
    To do so, use the syntax "with *instance*: ...".

    If used as a decorator, wraps a function and stores its execution results in s dictionary.
    To do so, use the method ``CacheDict.decorate()``.

    Args:

        file_path - a path to an existing or non-existent pickle file.
            If a relative path or a filename is given, puts it into the framework cache directory.

        access - cache access indicators. The string may include the following indicators:
            - ``r`` - read - grants access to read the cache file content
            - ``e`` - execute/evaluate - grants access to evaluate the decorated function (if such is present)
            - ``w`` - write - grants access to modify the cache file content

    Examples
    --------
    Example 1:

    >>> with CacheDict('example_cache_dict.pkl') as cache_dict:
    ...     x = np.array([[1, 2], [3, 4]])
    ...     x_T = cache_dict['x_T']  # Read the cache first
    ...     if isinstance(x_T, NoCache):  # If cache not found,
    ...         x_T = x.T    #   then execute the value
    ...     cache_dict['x_T'] = x_T  # Put the value in cache
    ...     print(cache_dict)
    ...
    {'x_T': array([[1, 3],
       [2, 4]])}

    Example 2:

    >>> import numpy as np
    >>> a = np.array([[1, 2], [3, 4]])
    >>> b = np.array([[5, 6], [7, 8]])
    >>> cached_mult = CacheDict.decorate(np.multiply,file_path='np_multiplication.pkl')  # Retrieve hashable representation of args.
    ...
    >>> cached_mult(a, b)
    array([[ 5, 12],
       [21, 32]])

    """

    @classmethod
    def _get_default_file_path(cls):
        return COMP_CACHE_FILE_NAME

    def __init__(self, file_path: os.PathLike | str | None = None, access: CacheAccess = 'rew'):
        super().__init__(file_path, access)
        self.cache_dict = None

    def __call__(self,
                 func: DecoratedCallable | None = None,
                 outer_key: Hashable | None = None,
                 inner_key: str | Callable[[Any], Hashable] | None = None) -> DecoratedCallable | Decorator:
        return self.decorate(func=func, outer_key=outer_key, inner_key=inner_key)

    def _get_cache_val(self, key: Hashable) -> Any:
        initialize_cache_dict(self.file_path)
        return self.cache_dict[key]

    def _put_cache_val(self, key: Hashable, value: Any) -> None:
        self.cache_dict[key] = value

    def _key_func(self, func, func_agrs, func_kwargs, inner_key, outer_key) -> Hashable:
        if outer_key is not None:
            key = outer_key
        elif inner_key is not None:
            key = parse_key(inner_key, func, *func_agrs, **func_kwargs)
        else:
            hash_objects = [func.__name__, func_agrs, func_kwargs]

            if ismethod(func):
                hash_objects.insert(0, func.__self__)

            key = get_hash(hash_objects)
        return key

    @classmethod
    def _decorate(cls,
                  func: DecoratedCallable | None = None,
                  file_path: os.PathLike | str | None = None,
                  access: CacheAccess = 'rew',
                  outer_key: Hashable | None = None,
                  inner_key: str | Callable[[Any], Hashable] | None = None) -> DecoratedCallable | Decorator:
        if outer_key is not None and inner_key is not None:
            raise ValueError('At most one of (outer key, inner key) can be specified.')

        file_path = _resolve_filepath(file_path)

        @wraps(func)
        def decorated(*args, **kwargs):
            instance = cls(file_path, access)
            with instance:
                val = instance._read_execute_write(func, func_args=args, func_kwargs=kwargs, access=access,
                                                   key_kwargs=dict(outer_key=outer_key, inner_key=inner_key))
            return val
        if func is None:
            decorator_return = partial(
                cls._decorate,
                file_path=file_path,
                access=access,
                outer_key=outer_key,
                inner_key=inner_key)
        else:
            decorator_return = decorated
        return decorator_return

    @omnimethod
    def decorate(self, func: DecoratedCallable | None = None,
                 file_path: os.PathLike | str | None = None,
                 access: CacheAccess | None = None,
                 outer_key: Hashable | None = None,
                 inner_key: str | Callable[[Any], Hashable] | None = None) -> DecoratedCallable | Decorator:
        """ Wraps a function and stores its execution results into a pickled cache dictionary.

        Examples:

        >>> import numpy as np
        >>> a = np.array([[1, 2], [3, 4]])
        >>> b = np.array([[5, 6], [7, 8]])
        >>> cached_mult = CacheDict.decorate(
        ...     np.multiply,
        ...     file_path='np_multiplication.pkl',
        ...     inner_key='tuple(map(lambda a: a.data.tobytes(), args))')
        ...
        >>> cached_mult(a, b)
        array([[ 5, 12],
           [21, 32]])

        >>> import time
        >>> def do_some_heavy_computing(how_heavy):
        ...     time.sleep(how_heavy)
        ...     return how_heavy ** 2
        ...
        >>> c_do_some_heavy_computing = CacheDict.decorate(
        ...     do_some_heavy_computing,
        ...     file_path='sheer_chaos.pkl',
        ...     inner_key='how_heavy')
        ...
        >>> for i in range(10):
        ...     c_do_some_heavy_computing(i)
        ...
        >>> with CacheDict('sheer_chaos.pkl') as cache:
        ...     print(cache)
        ...
        {0: 0, 1: 1, 2: 4, 3: 9, 4: 16, 5: 25, 6: 36, 7: 49, 8: 64, 9: 81}

        Params:

            func - a function to decorate.

            file_path - a path to an existing or non-existent pickle file.
                If a relative path or a filename is given, puts it into the framework cache directory.

            access - cache access indicators. The string may include the following indicators:
                - ``r`` - read - grants access to read the cache file content
                - ``e`` - execute/evaluate - grants access to evaluate the decorated function (if such is present)
                - ``w`` - write - grants access to modify the cache file content

            outer_key - a constant hashable key to store the function call's result.

            inner_key - a callable or a code expression that evaluates a hashable key to store
                the function call's result. To do so, use argument names that are used inside the function.
                Some functions do not support signatures and will throw an error.
                You may use "args" and "kwargs" in your expression instead.
        """
        if outer_key is not None and inner_key is not None:
            raise ValueError('At most one of (outer key, inner key) can be specified.')

        return super().decorate(
            func=func,
            file_path=file_path,
            access=access,
            outer_key=outer_key,
            inner_key=inner_key,
        )

    def __enter__(self) -> MyDefaultDict:
        if 'r' in self.access:
            self.file_path = _resolve_filepath(self.file_path)
            self.cache_dict = initialize_cache_dict(self.file_path)
        else:
            self.cache_dict = MyDefaultDict(NoCache)
        return self.cache_dict

    def __exit__(self, exc_type, exc_val, exc_tb):
        if 'w' in self.access:
            update_cache(self.cache_dict, self.file_path)
        self.cache_dict.clear()
        self.cache_dict = None

    def get(self, key: None | Hashable) -> NoCache | MyDefaultDict | Any:
        file_path = _resolve_filepath(self.file_path)
        cache_dict = _initialize_cache(file_path)
        if key is None:
            return cache_dict
        return cache_dict[key]
