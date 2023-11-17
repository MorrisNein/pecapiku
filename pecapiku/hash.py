from __future__ import annotations

import json
from typing import Sequence


def get_hash(objects: Sequence[object]) -> str:
    return _json_dumps(tuple(objects))


def _json_dumps(obj: object) -> str:
    return json.dumps(
        obj,
        default=_json_default,
        # force formatting-related options to known values
        ensure_ascii=False,
        sort_keys=True,
        indent=None,
        separators=(',', ':'),
    )


def _json_default(obj: object):
    obj_class = obj.__class__
    class_path = '.'.join((obj_class.__module__, obj_class.__name__))
    vars_dict = vars(obj) if hasattr(obj, '__dict__') else {}
    return _json_dumps(dict(__class_path__=class_path, **vars_dict))
