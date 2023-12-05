from typing import Any

import pytest

from pecapiku.hash import get_hash


def test_hash_order():
    assert get_hash([1, 2, 3]) != get_hash([3, 2, 1])


class TestObject:
    def __init__(self, foo: Any):
        self.foo = foo


class OtherTestObject:
    def __init__(self, foo: Any):
        self.foo = foo


@pytest.mark.parametrize('test_obj_1, test_obj_2, test_obj_3',
                         [
                             [{1, 2}, {2, 1}, {1, 2, 3}],
                             [dict(a=1, b=2), dict(b=2, a=1), dict(a=2, b=1)],
                             [TestObject(1), TestObject(1), TestObject(2)],
                             [TestObject(1), TestObject(1), OtherTestObject(1)],
                             [TestObject(1), TestObject(1), TestObject('1')],
                             [TestObject(None), TestObject(None), TestObject('None')],
                         ])
def test_hash_invariants(test_obj_1, test_obj_2, test_obj_3):
    hash_1 = get_hash([test_obj_1])
    hash_2 = get_hash([test_obj_2])
    hash_3 = get_hash([test_obj_3])
    assert hash_1 == hash_2 != hash_3
