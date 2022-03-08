#!/usr/bin/env python3

import sys
import collections


Token = collections.namedtuple('Token', 'type string start end line')


class AttrDict(dict):
    'Augment a dict with more convenient .attr syntax.  not-present keys return None.'
    def __getattr__(self, k):
        try:
            v = self[k]
            if isinstance(v, dict) and not isinstance(v, AttrDict):
                v = AttrDict(v)
            return v
        except KeyError:
            if k.startswith("__"):
                raise AttributeError
            return None

    def __setattr__(self, k, v):
        self[k] = v

    def __dir__(self):
        return self.keys()


class Variable:
    def __init__(self, key):
        '''*key* is key in output dict.'''
        self.key = key

    def __repr__(self):
        return '?'+self.key


class InnerDict(dict):
    'instantiate only the inner keys and not the dict itself'
    def __repr__(self):
        r = JsomCoder().encode(self)
        return f'<{r}>'


def deep_update(a: dict, b: dict, type=lambda v: v):
    ''
    if not b: return a
    for k, vb in b.items():
        va = a.get(k, None)
        if isinstance(va, dict) and isinstance(vb, dict):
            deep_update(va, vb)
        elif isinstance(va, list):
            va.append(vb)
        else:
            a[k] = type(vb)
    return a


def deep_match(a, b):
    'Return dict of matches between a and b if a and b are dicts/lists and a and b are exact matches, or boolean equality otherwise.'
    if isinstance(b, Variable):  # Variables match anything
        return {b.key: a}

    elif isinstance(a, dict) and isinstance(b, dict):
        if not isinstance(b, InnerDict):
            if set(a.keys()) ^ set(b.keys()):
                return False
        ret = {}
        for k, v in b.items():
            if k not in a:  # all `k` in `b` must be in `a` to match
                return False
            m = deep_match(a[k], v)
            if m is False:  # values must match
                return False
            if isinstance(m, dict):
                deep_update(ret, m)

        return ret

    elif isinstance(a, list) and isinstance(b, list):
        ret = []
        for x in b:
            for y in a:
                m = deep_match(x, y)
                if m is False:  # each item in `b` must match at least one item in `a`
                    return False
                if isinstance(m, dict):
                    deep_update(ret, m, lambda v: [v])
        return ret

    return a == b


def deep_del(a: dict, b: dict):
    'deep remove contents of *b* from *a*.'
    for k, v in b.items():
        assert k in a, (a, k)
        if isinstance(v, dict):
            deep_del(a[k], v)
            if not a[k]:
                del a[k]
        else:
            del a[k]


class JsomCoder:
    def __init__(self, **kwargs):
        self.toktuple = None
        self.options = AttrDict(kwargs)
        self.globals = AttrDict(true=True, false=False, null=None,
                                macros={}, options=self.options)
        self._revmacros = None

    @property
    def revmacros(self):
        if self._revmacros is None:
            self._revmacros = {v:k for k,v in self.globals.macros.items() if not isinstance(v, (dict, list))}
        return self._revmacros

    def debug(self, *args):
        if self.options.debug:
            print(*args, file=sys.stderr)

    def error(self, msg):
        raise Exception(msg)

    def tokenize(self, s):
        ''
        startchnum = 0
        tok = ''
        for linenum, line in enumerate(s.splitlines()):
            self.debug(line)

            chnum = 0
            while chnum < len(line):
                ch = line[chnum]
                chnum += 1

                if ch == ';':  # comment, ignore until end of line
                    break

                if ch.isspace() or ch in '{}[]()<>"':
                    if tok:
                        yield Token('token', tok, (linenum, startchnum), (linenum, chnum), line)
                        tok = ''
                        startchnum = chnum

                if ch.isspace():
                    continue

                if ch == '"':
                    j = line.index('"', chnum)
                    yield Token('str', line[chnum:j], (linenum, chnum), (linenum, j-chnum), line)
                    chnum = j+1
                    continue

                if ch in '{}[]()<>':
                    yield Token(ch, ch, (linenum, chnum), (linenum, chnum+1), line)
                else:
                    tok += ch

        if tok:
            yield Token(tok, tok, (linenum, chnum), (linenum, chnum+1), line)

    def safe_decode(self, it, top=None):
        try:
            return self.decode(it, top=top)
        except Exception as e:
            t = self.toktuple
            print(f'ERROR: {type(e).__name__} {e} at line {t.start[0]+1} (column {t.start[1]})', file=sys.stderr)
            print(t.line, file=sys.stderr)
            raise

    def decode(self, it, top=None):
        '*it* can be str or generator of Token.  Return parsed object.'
        key = None
        stack = []  # path from root
        if top is not None:
            stack.append(top)

        if isinstance(it, str):
            it = self.tokenize(it)

        while True:
            try:
                self.toktuple = next(it)
            except StopIteration:
                break

            out = None
            append_stack = False
            tok = self.toktuple.string
            if tok[0] == '?':  # variable
                out = Variable(tok[1:])

            elif tok[0] == '.':  # dict key
                if not stack:  # create a toplevel object so outermost {} is not necessary
                    assert top is None
                    top = dict()
                    stack.append(top)

                if isinstance(stack[-1], list):
                    r = dict()
                    stack[-1].append(r)
                    stack[-1] = r
                elif key is not None:  # two keys in a row: parent dict has only one element (us)
                    r = dict()
                    old = stack.pop()
                    old[key] = r
                    stack.append(r)

                key = tok[1:]
                continue

            elif tok == '{':  # open dict outer
                out = dict()
                append_stack = True

            elif tok == '<':  # open dict inner
                out = InnerDict()
                append_stack = True

            elif tok == '[':  # open list
                out = list()
                append_stack = True

            elif tok in '}]>':  # close container
                stack.pop()
                continue

            elif tok == '(':  # open macro, instantiate with args
                name = next(it).string
                args = []
                self.decode(it, top=args)  # recurse
                if name not in self.globals.macros:
                    self.error(f'no macro named "{name}"')

                out = self.instantiate(self.globals.macros[name], args, name)  # mutates args
                if args:  # none should be left over
                    self.error(f'too many args given to "{name}" {args}')

            elif tok == ')':  # end macro arguments
                break  # exit recurse

            elif tok in self.globals:
                if not stack:
                    stack.append(self.globals[tok])
                else:
                    out = self.globals[tok]

            elif tok in self.globals.macros:  # bare macro, instantiate without args
                out = self.instantiate(self.globals.macros[tok], [], tok)

            else:
                # try parsing as number
                try:
                    out = int(tok)
                except ValueError:
                    try:
                        out = float(tok)
                    except ValueError:
                        out = tok  # pass it through and hope for the best

            # add 'out' to the top object

            if not stack:  # create a toplevel object (outermost [] is implied without a key)
                assert top is None
                top = list()
                stack.append(top)

            if isinstance(stack[-1], dict):
                if not key:
                    if isinstance(out, InnerDict):
                        stack[-1].update(out)
                    else:
                        self.error(f'no key given for {self.literal(out)})')
                else:
                    if key in stack[-1]:
                        oldval = stack[-1][key]
                        if not isinstance(oldval, type(out)):
                            self.error(f'{key} has existing value of {type(oldval)}')
                        if isinstance(out, dict):
                            deep_update(oldval, out)
                        elif isinstance(out, list):
                            oldval.append(out)
                        else:
                            stack[-1][key] = out
                    else:
                        stack[-1][key] = out
                    key = None

            elif isinstance(stack[-1], list):
                assert not isinstance(out, InnerDict)
                stack[-1].append(out)
            else:
                self.error('non-container on top-of-stack')

            if append_stack:
                stack.append(out)

        return top

    def instantiate(self, v, args, tmplname):
        ''
        if isinstance(v, InnerDict):
            return InnerDict({k: self.instantiate(x, args, tmplname) for k, x in v.items()})
        elif isinstance(v, dict):
            return {k: self.instantiate(x, args, tmplname) for k, x in v.items()}
        elif isinstance(v, list):
            return list(self.instantiate(x, args, tmplname) for x in v)
        elif isinstance(v, Variable):
            if not args:
                self.error(f'missing arg "{v.key}" for template "{tmplname}"')
            return args.pop(0)
        else:
            return v

    def iterencode(self, obj, depth=0, indent=''):
        ''
        if isinstance(obj, dict):
            # emit first macro, if any match
            innards = []
            for macroname, macro in self.globals.macros.items():
                m = deep_match(obj, macro)
                if m is False:  # didn't match
                    continue
                if isinstance(m, dict):  # matched with args
                    if m:
                        args = [self.iterencode(x) for x in m.values()]
                        args = list(x.strip() for y in args for x in y if x.strip())
                        args = ' '.join(args)
                        args = args.strip()
                        r = f'({macroname} {args})'
                        if isinstance(macro, InnerDict):
                            innards.append(r)
                        else:
                            yield r
                    else:
                        if isinstance(macro, InnerDict):
                            innards.append(macroname)
                        else:
                            yield macroname

                    if isinstance(macro, InnerDict):
                        deep_del(obj, macro)
                    else:
                        if innards:
                            yield '{'
                            yield from innards
                            yield '}'
                        return

            # if no macro fully applied, emit rest of dictionary

            # first see if it's a one element dict, and emit only the .key
            if not innards and len(obj) == 1:
                k, v = list(obj.items())[0]
                yield f'.{k}'  # without opening {
                yield from self.iterencode(v, depth=depth+1, indent=indent)
                return

            if depth > 0:
                yield '{'

            yield from innards

            for k, v in sorted(obj.items(), key=len):
                if indent and len(obj) > 1:
                    yield '\n' + depth*indent
                yield f'.{k}'
                yield from self.iterencode(v, depth=depth+1, indent=indent)
            if depth > 0:
                yield '}'

        elif isinstance(obj, list):
            if depth > 0:
                yield '['

            for v in obj:
                yield from self.iterencode(v, depth=depth+1, indent=indent)

            if depth > 0:
                yield ']'

            if indent:
                yield '\n' + depth*indent

        elif obj in self.revmacros:
            yield self.revmacros[obj]
        else:
            yield self.literal(obj)

    def literal(self, obj):
        if isinstance(obj, str):
            return f'"{obj}"'
        elif obj is True:
            return 'true'
        elif obj is False:
            return 'false'
        elif obj is None:
            return 'null'
        else:
            return f'{obj}'

    def encode(self, d):
        return ' '.join(self.iterencode(d, indent=self.options.indent)).strip()
