from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from functools import partial, update_wrapper
from pathlib import Path
from typing import Any, Callable, Generic, Hashable, Type, TypeVar

from pecapiku.cache_access import COMP_CACHE_FILE_NAME, CacheAccess, _resolve_filepath
from pecapiku.no_cache import NoCache

logger = logging.getLogger(__file__)

DecoratedCallable = TypeVar("DecoratedCallable", bound=Callable[..., Any])


class omnimethod(Generic[DecoratedCallable]):
    def __init__(self, func: DecoratedCallable):
        self.func = func

    def __get__(self, instance, owner) -> DecoratedCallable:
        if instance is None:
            func = partial(self.func, owner)
        else:
            func = partial(self.func, instance)
        update_wrapper(func, self.func)
        return func


class BaseCache(ABC):
    def __init__(self, file_path: os.PathLike | str | None = None, access: CacheAccess = 'rew'):
        file_path = file_path or COMP_CACHE_FILE_NAME
        file_path = _resolve_filepath(file_path)
        self.file_path: Path = file_path
        self.access = access

    @abstractmethod
    def get_cache_val(self, key: Hashable) -> Any:
        raise NotImplementedError()

    @abstractmethod
    def put_cache_val(self, key: Hashable, value: Any):
        raise NotImplementedError()

    @abstractmethod
    def key_func(self, *args, **kwargs) -> Hashable:
        raise NotImplementedError()

    def _read_execute_write(self, func, func_args, func_kwargs, access, key_kwargs: dict | None = None) -> Any:
        key_kwargs = key_kwargs or {}
        if access == 'e':
            logger.info('Executing cache value, since no access to the cache is provided...')
            return func(*func_args, **func_kwargs)

        key = self.key_func(func, func_args, func_kwargs, **key_kwargs)

        was_read = False
        if 'r' in access:
            logger.info(f'Getting cache for the key "{key}"...')
            val = self.get_cache_val(key)
        else:
            val = NoCache()

        if not isinstance(val, NoCache):
            logger.info(f'Found the cache for the key "{key}": {val}...')
            was_read = True

        if isinstance(val, NoCache) and 'e' not in access:
            raise ValueError(
                f'No cache found for {func.__name__}({func_args, func_kwargs}) in "{self.file_path}", '
                f'but computation is not allowed (access="{access}").')

        if 'e' in access and not was_read:
            logger.info(f'Executing cache value for the key "{key}"...')
            val = func(*func_args, **func_kwargs)

        if 'w' in access and not was_read and not isinstance(val, NoCache):
            self.put_cache_val(key, val)
            logger.info(f'Writing cache for the key "{key}": {val}...')
        return val

    @classmethod
    @abstractmethod
    def _decorate(cls, func: DecoratedCallable, *args, **kwargs) -> DecoratedCallable:
        raise NotImplementedError()

    @omnimethod
    def decorate(self: BaseCache | Type[BaseCache],
                 func: DecoratedCallable,
                 file_path: os.PathLike | str | None = None,
                 access: CacheAccess | None = None, *args, **kwargs) -> DecoratedCallable:
        if not isinstance(self, BaseCache):
            file_path = file_path
            access = access
        else:
            file_path = file_path or self.file_path
            access = access or self.access
        return self._decorate(func, file_path, access, *args, **kwargs)
