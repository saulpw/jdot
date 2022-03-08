import pytest

from jsom import JsomCoder


@pytest.mark.parametrize("s", [
    '.a 1 .b 2',
    '.k { .int 1 .float 3.14 .str "foo" .bt true .bf false .n null }',
    '.k .k2 { .a "a" .list [ 1 2 3 4 ] }',
    '.a .b .c .d [ [ 1 2 ] [ 3 4 ] ]',
    '[ 1 1.5 2.5 3.0 0.54 ]',
    '{ .i 1 .v "abc" } { .i 2 .v "def" }',
    # r'[ "a\"bc" ]',
])
def test_roundtrip(s):
    j = JsomCoder(indent='')
    d = j.decode(s)
    assert j.encode(d) == s, d
