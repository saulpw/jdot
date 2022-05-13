import pytest

from jdot import JdotCoder

@pytest.mark.parametrize(("s", "out"), [
    ('.a { .b .c 3 .d 4 }', dict(a=dict(b=dict(c=3), d=4))),
    ('.a .b {} .c {}', dict(a=dict(b=dict()), c={})),
    ('{ .a .b {} .c {} }', [dict(a=dict(b=dict()), c={})]),
    ('{.f 1 } { .g 2 }', [dict(f=1), dict(g=2)]),
])
def test_decode(s, out):
    j = JdotCoder()
    d = j.decode(s)
    assert d == out


@pytest.mark.parametrize("s", [
    '.a 1 .b 2',
    '.k .int 1 .float 3.14 .str "foo" .bt true .bf false .n null',
    '.k .k2 .a "a" .list [ 1 2 3 4 ]',
    '.a .b .c .d [ [ 1 2 ] [ 3 4 ] ]',
    '1 1.5 2.5 3.0 0.54',
    '[ 1 1.5 2.5 3.0 0.54 ] [ 2 3 4 ]',
    '{ .i 1 .v "abc" } { .i 2 .v "def" }',
    '.a [ .f 1 .g 2 ]',
    '.str-number "4"',
    '."quoted key" 4',
    '.empty-string ""',
    '.embedded-opp-quote \'a"b\'',
    ".escape-quote 'a\"\"\\'b'",  # embedded doublequote will force single quote delimiter
    '.escape-backslash "a\\\\"',
    r""".embedded-newline '
\\
\'
" " "
'"""
])
def test_roundtrip_jdot(s):
    j = JdotCoder()
    d = j.decode(s)
    assert s == j.encode_oneliner(d)


@pytest.mark.parametrize(("obj", "enc"), [
    (dict(a=dict(b={}), c={}), '.a .b {} .c {}'),
    ({"f": 1, "g": 2}, '.f 1 .g 2'),  # a) must be the case
    ([{"f": 1, "g": 2}, {"f": 3, "g": 4}], '{ .f 1 .g 2 } { .f 3 .g 4 }'), # b) makes sense
    ([{"f": 1, "g": 2}], '{ .f 1 .g 2 }'),  # c) follows from above
])
def test_roundtrip_dict(obj, enc):
    j = JdotCoder()
    r = j.encode_oneliner(obj)
    assert r == enc
    assert j.decode(r) == obj, r


@pytest.mark.parametrize(("macros", "d", "out"), [
    ('@macros .test { .a {.k ?v} .c {} }', dict(a=dict(k=23), c={}), '( test 23 )'),
    ('@macros .test { .a {.k ?v } .c {} }', dict(a=dict(k=42, j=3), c={}), '.a { .k 42 .j 3 } .c {}'),
    ('@macros .test { .a {.k ?v . ?} .c {} }', dict(a=dict(k=42, j=3), c={}), '( test 42 )'),
    ('@macros .test { .a [{.k ?v . ?}] }', dict(a=[dict(k=42, j=3)]), '( test 42 )'),
    ('@macros .test <.a [{.k ?v}]>', dict(a=[dict(k=42), dict(k=23)]), '( test 42 ) ( test 23 )'),
    ('@macros .test <.a "b">', dict(x=dict(a='b', c='d')), '.x { test .c "d" }'),
    ('@macros .a_b <.a "b"> .c_d .c "d"', dict(x=dict(a='b', c='d')), '.x { a_b c_d }'),
    ('@macros .asc < .a [ { .k ?v .dir "ASC"} ] > .desc < .a [ { .k ?v .dir "DESC"} ] >', dict(a=[dict(k=1, dir="DESC"), dict(k=2, dir="ASC")]), '( asc 2 ) ( desc 1 )'),
])
def test_macro_encode(macros, d, out):
    j = JdotCoder()
    assert not j.decode(macros)
    r = j.encode_oneliner(d)
    assert r == out, j.globals['macros']


def test_macro():
    j = JdotCoder()
    d = j.decode('@macros .foo { .x 2 }')
    assert 'foo' in j.globals['macros'], j.globals['macros']


@pytest.mark.parametrize("s", [
    '# comment',
    ' # .a 3 .b 2 "',
])
def test_comments(s):
    j = JdotCoder()
    d = j.decode(s)
    assert not d


@pytest.mark.parametrize(("s", "out"), [
    ('@macros .foo .a ?a @output .outer ( foo 4 )', '.outer .a 4'),
])
def test_decode_reencode(s, out):
    j = JdotCoder()
    d = j.decode(s)
    assert out == JdotCoder().encode_oneliner(d)  # un-macroed
    macrodefs = JdotCoder().encode_oneliner(j.globals['macros'])
    assert ' '.join(['@macros', macrodefs, '@output', j.encode_oneliner(d)]) == s  # re-macroed
