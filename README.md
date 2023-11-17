# Pecapiku - a persistent cache pickling utility

Provides a syntax for storing and retrieving the results of a computation on disk using `pickle` library.

> ***Important note!*** The purpose of the utility is not to speed up calculations or to save memory. As the size
of a cache file increases, the access time will raise.
> 
> The main purpose is to restart a heavy computational script if something broke in the middle and there is no way to debug it
beforehand.

The two main classes are `CacheDict`, `SingleValueCache`.

## `CacheDict`

`CacheDict` can be used as a context manager or as a decorator over a function.

### Context manager

The context manager (`with CacheDict() as cache_dict: ...`) provides access to a dictionary from which values can be
retrieved or written. The cache file will be updated once upon exiting the context.

### Decorator

The `CacheDict.decorate()` wraps a function to store its evaluation results in a pickled dictionary. The function
arguments or provided constant keys may be used as keys to the dictionary. The values are the function outputs. The
cache file is updated once every evaluation of the function.

## `SingleValueCache`

The `SingleValueCache.decorate()` acts similar to `CacheDict.decorate()`, but it stores a single value in a file per
decorated function.

## Cache File Management

As plain as a day:

    >>> from pecapiku import config
    >>> config.get_cache_dir()  # Look at the default cache dir
    # The result is OS-specific
    >>> config.set_cache_dir(...)  # Change it to a more preferable directory

All cache files will be created inside this directory, if a filename or a relative cache path is provided.
If an absolute path is provided, a pickle file will appear at the path.

## Cache Access Management

To manage cache access, there's a parameter `access` shared between different methods.
It equals to a string that may include the following indicators:

- ``r`` - read - grants access to read a cache file content
- ``e`` - execute/evaluate - grants access to evaluate a decorated function (if such is present)
- ``w`` - write - grants access to modify a cache file content

The `CacheDict` context manager follows these steps:

1. If read access is given, try to read the cache dict from a file.
2. Provide the cache dict as a context.
3. If write access is given, update the cache file.

The `.decorate()` cache decorators follow these steps:

1. If read access is given, try to read the cache from a file (and per key for `CacheDict`).
2. If execution access is given and cache not found at the previous step, evaluate the function.
3. If write access is given and the function was evaluated at the previous step, update the cache file.

## Hashable Key Management

To store a function evaluation, the method `CacheDict.decorate()` needs a key.

There are 3 ways of getting a key:

1. If no keys provided, it automatically calculates the key using the following information:
    - a function name
    - positional and keyword arguments
    - object fields, if this function is a method
2. `inner_key` may be provided in a form of string code expression or a callable.
This expression or callable must return a hashable result that may be used as a dictionary key.
It may use inner function arguments by their corresponding names.
Or it may use `args` and `kwargs` - as the only option for any precompiled non-Python function.
3. `outer_key` is a hashable constant to access a value in a `CacheDict`.

 ## Examples

 Example 1. CacheDict as a context manager.

    >>> import numpy as np
    >>> from pecapiku import CacheDict
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

 Example 2. CacheDict as a decorator.

    >>> import numpy as np
    >>> from pecapiku import CacheDict
    >>> a = np.array([[1, 2], [3, 4]])
    >>> b = np.array([[5, 6], [7, 8]])
    >>> cached_mult = CacheDict.decorate(
    ...     np.multiply,  # Select a function to cache.
    ...     file_path='np_multiplication.pkl',  # Select path to a pickle file.
    ...     inner_key='tuple(map(lambda a: a.data.tobytes(), args))')  # Retrieve hashable representation of args.
    ...
    >>> cached_mult(a, b)
    array([[ 5, 12],
       [21, 32]])

Example 3. SingleValueCache as a decorator.

     >>> import time
     >>> from timeit import timeit
     >>> from pecapiku import SingleValueCache
     >>> def a_heavy_function():
     ...     time.sleep(1)
     ...     return 42
     ...
     >>> cached_func = SingleValueCache.decorate(a_heavy_function, 'a_heavy_function.pkl')
     >>> print(timeit(a_heavy_function, number=10))  # 10.070
     >>> print(timeit(cached_func, number=10))  # 1.015

## Installation

`pip install git+https://github.com/MorrisNein/pecapiku`

