import pytest

from jsom import JsomCoder


@pytest.mark.parametrize("s", [
    '.a 1 .b 2',
    '.k .int 1 .float 3.14 .str "foo" .bt true .bf false .n null',
    '.k .k2 .a "a" .list [ 1 2 3 4 ]',
    '.a .b .c .d [ [ 1 2 ] [ 3 4 ] ]',
    '1 1.5 2.5 3.0 0.54',
    '[ 1 1.5 2.5 3.0 0.54 ] [ 2 3 4 ]',
    '{ .i 1 .v "abc" } { .i 2 .v "def" }',
    '.str-number "4"',
    '.empty-string ""',
    '.embedded-opp-quote \'a"b\'',
    ".escape-quote 'a\"\"\\'b'",  # embedded doublequote will force single quote delimiter
    '.escape-backslash "a\\\\"',
    """.embedded-newline '
\\\\
\\'
" " "
\'"""
])
def test_roundtrip_jsom(s):
    j = JsomCoder()
    d = j.decode(s)
    assert s == j.encode(d), d


@pytest.mark.parametrize("d", [
    dict(a=dict(b={}), c={})
])
def test_roundtrip_dict(d):
    j = JsomCoder()
    r = j.encode(d)
    assert j.decode(r) == d


@pytest.mark.parametrize(("macros", "d", "out"), [
    ('@macros .test .a {.k ?v} .c {}', dict(a=dict(k=23), c={}), '( test 23 )'),
    ('@macros .test .a {.k ?v } .c {}', dict(a=dict(k=42, j=3), c={}), '.a { .k 42 .j 3 } .c {}'),
    ('@macros .test .a {.k ?v . ?} .c {}', dict(a=dict(k=42, j=3), c={}), '( test 42 )'),
    ('@macros .test .a [{.k ?v . ?}]', dict(a=[dict(k=42, j=3)]), '( test 42 )'),
    ('@macros .test <.a [{.k ?v}]>', dict(a=[dict(k=42), dict(k=23)]), '( test 42 ) ( test 23 )'),
])
def test_macro_encode(macros, d, out):
    j = JsomCoder()
    assert not j.decode(macros)
    r = j.encode(d)
    assert r == out


def test_macro():
    j = JsomCoder()
    d = j.decode('@macros .foo { .x 2 }')
    assert 'foo' in j.globals['macros'], j.globals['macros']


@pytest.mark.parametrize("s", [
    '# comment',
    ' # .a 3 .b 2 "',
])
def test_comments(s):
    j = JsomCoder()
    d = j.decode(s)
    assert not d


@pytest.mark.parametrize(("s", "out"), [
    ('@macros .foo .a ?a @output .outer ( foo 4 )', '.outer .a 4'),
])
def test_decode(s, out):
    j = JsomCoder()
    d = j.decode(s)
    assert out == JsomCoder().encode(d)  # un-macroed
    macrodefs = JsomCoder().encode(j.globals['macros'])
    assert ' '.join(['@macros', macrodefs, '@output', j.encode(d)]) == s  # re-macroed
