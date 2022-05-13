from dataclasses import dataclass
from typing import Tuple, Iterator, Union

from .jdot import InnerDict, deep_update, Variable

COMMENT_CHAR = '#'

@dataclass
class Token:
    type: str
    string: str
    start: Tuple[int, int]
    end: Tuple[int, int]
    line: str

    def __str__(self):
        return f'{self.string} (line {self.start[0]}, col {self.start[1]})'


ESCAPE_CHARS = {'n': '\n', '\\': '\\', '\"': '\"'}

def parse_escaped_str(s:str, i:int=0, delim:str=''):
    string = ''
    while i < len(s):
        ch = s[i]
        i += 1

        if ch == delim:
            return string, i

        elif ch == '\\':
            string += ESCAPE_CHARS.get(s[i], s[i])  # next character, itself by default
            i += 1
        else:
            string += ch

    return string, i  # not finished


class DecodeException(Exception):
    pass


class JdotDecoder:
    def error(self, msg, **kwargs):
        t = self.toktuple
        errmsgs = [
            f'ERROR: {msg} at line {t.start[0]} (column {t.start[1]})',
            f'> {t.line.rstrip()}',
            '  ' + ' '*(t.start[1]-1) + '^',
        ]
        for k, v in kwargs.items():
            errmsgs.append(f'{k}={v}')
        raise DecodeException('\n'.join(errmsgs))

    def tokenize(self, s:Union[str, Iterator[str]]) -> Iterator[Token]:
        startchnum = 1
        tok = ''

        chnum = 1
        linenum = 0
        line = ''

        if isinstance(s, str):
            it = iter(x+'\n' for x in s.splitlines())
        else:
            it = iter(s)

        while True:
            if not line[chnum-1:]:
                linenum += 1
                chnum = 1
                try:
                    line = next(it)
                except StopIteration:
                    break

                self.debug(f'{linenum}: {line.strip()}')
                continue

            ch = line[chnum-1]
            chnum += 1

            if ch == COMMENT_CHAR:  # comment, ignore until end of line
#                yield Token('comment', line[chnum-1:], (linenum, startchnum), (linenum, chnum), line)
                chnum = len(line)+1
                continue

            if ch.isspace() or ch in '{}[]()<>':
                if tok:
                    yield Token('token', tok, (linenum, startchnum), (linenum, chnum), line)
                    tok = ''
                startchnum = chnum

            if ch.isspace():
                continue

            if ch in '"\'':
                startline = linenum

                while True:
                    bit, i = parse_escaped_str(line, i=chnum-1, delim=ch)
                    tok += bit
                    if i < len(line):  # string done before end of string
                        chnum = i+1
                        break
                    else:
                        linenum += 1
                        chnum = 1
                        try:
                            line = next(it)
                        except StopIteration:
                            self.error(f'unterminated string: {repr(tok)}')
                            break

                if tok[:1] == '.':
                    yield Token('key', tok, (startline, startchnum), (linenum, chnum), line)
                else:
                    yield Token('str', tok, (startline, startchnum), (linenum, chnum), line)

                tok = ''
                startchnum = chnum
                continue

            if ch in '{}[]()<>':
                yield Token(ch, ch, (linenum, chnum-1), (linenum, chnum), line)
            else:
                tok += ch

        if tok:
            yield Token(tok, tok, (linenum, chnum-1), (linenum, chnum), line)
            tok = ''

    def decode(self, s):
        return self.iterdecode(self.tokenize(s))

    def iterdecode(self, it):
        '*it* can be str or generator of Token.  Return list of parsed objects.'

        key = None
        ret = None  # root list to return
        stack = []  # path from root
        curr = None
        self.globals['output'] = None  # make available as '@output'

        while True:
            try:
                self.toktuple = next(it)
            except StopIteration:
                break

            out = None  # value to set at current key or append to list
            append_stack = False  # append curr to stack after setting key value
            tok = self.toktuple.string

            self.debug(stack, curr, self.toktuple)

            if self.toktuple.type == 'str':  # string literal
                out = tok

            elif tok[0] == '?':  # variable
                out = Variable(tok[1:])

            elif tok[0] == '@':  # global variable like '@options' and '@macros'
                name = tok[1:]
                if name not in self.globals:
                    self.error(f'no such global {name}')

                self.debug(f'global {tok}')
                curr = self.globals[name]
                stack = [curr]
                self.restart()
                continue

            elif tok in self.macros:  # bare macro, instantiate without args
                out = self.instantiate(self.macros[tok], [], tok)

            elif tok == '!':  # show debugging info
                print('macros', self.macros)
                print('options', self.options)
                print('stack', stack)
                continue


            elif tok[0] == '.':  # dict key
                if curr is None:
                    assert not self.globals['output']
                    ret = curr = self.globals['output'] = dict()
                    stack.append(curr)

                if isinstance(curr, list):
                    r = dict()     # open new dict by default
                    curr.append(r)  # append it to the list
                    curr = r        # and replace the list with it
                elif key is not None:  # two keys in a row: parent dict has only one element (us)
                    # change curr without pushing
                    r = dict()
                    curr[key] = r
                    curr = r

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

            elif tok == '}':  # close dict outer
                if not isinstance(curr, dict):
                    self.error('mismatched closing }')
                stack.pop()
                curr = stack[-1] if stack else None
                continue

            elif tok == ']':  # close list
                stack.pop()
                if not isinstance(curr, list) and not isinstance(stack[-1], list):
                    self.error('mismatched closing ]')
                curr = stack[-1] if stack else None
                continue

            elif tok == '>':  # close dict inner
                if not isinstance(curr, InnerDict):
                    self.error('mismatched closing >')
                stack.pop()
                curr = stack[-1] if stack else None
                continue

            elif tok == '(':  # open macro, instantiate with args
                name = next(it).string
                args = self.iterdecode(it)  # recurse
                if name not in self.macros:
                    self.error(f'no macro named "{name}"')

                out = self.instantiate(self.macros[name], args, name)  # mutates args
                if args:  # none should be left over
                    self.error(f'too many args given to "{name}" {args}: {self.macros[name]}')

            elif tok == ')':  # end macro arguments
                break  # exit recurse

            elif tok == 'true':
                out = True
            elif tok == 'false':
                out = False
            elif tok == 'null':
                out = None

            else:
                # try parsing as number
                try:
                    out = int(tok)
                except ValueError:
                    try:
                        out = float(tok)
                    except ValueError:
                        if self.options['strict']:
                            self.error(f"unknown token '{out}' (strict mode)")
                        out = tok  # pass it through as a string to be nice

            # add 'out' to the top object

            if curr is None:
                assert ret is None
                assert not stack
                assert not self.globals['output']
                ret = curr = self.globals['output'] = list()
                stack.append(curr)

            if isinstance(curr, dict):
                if key is None:
                    if isinstance(out, InnerDict):
                        deep_update(curr, out)
                    elif isinstance(out, dict):
                        deep_update(curr, out)
                        # leave old dict there, to be filled in with the 'new' dicts inners
                    else:
                        self.error(f'no key given for value {self.literal(out)}')
                else:
                    if key in curr:
                        oldval = curr[key]
                        if not isinstance(oldval, type(out)):
                            self.error(f'{key} has existing {type(oldval)} value')
                        if isinstance(out, dict):
                            deep_update(oldval, out)
                        elif isinstance(out, list):
                            oldval.append(out)
                        else:
                            curr[key] = out
                            curr = None
                    else:
                        curr[key] = out
                        curr = stack[-1] if stack else None
                    key = None

            elif isinstance(curr, list):
                curr.append(out)

            else:
                self.error(f'non-container type {type(curr)} is current')

            if append_stack:
                stack.append(out)
                curr = out

        return ret

    def instantiate(self, v, args, tmplname):
        ''
        def ignorable(obj):
            return isinstance(obj, Variable) and not obj.key

        if isinstance(v, InnerDict):
            return InnerDict({
                k: self.instantiate(x, args, tmplname)
                for k, x in v.items()
                if not ignorable(x)
            })
        elif isinstance(v, dict):
            return {
                k: self.instantiate(x, args, tmplname)
                for k, x in v.items()
                if not ignorable(x)
            }
        elif isinstance(v, list):
            return list(self.instantiate(x, args, tmplname)
                for x in v
                if not ignorable(x)
            )
        elif isinstance(v, Variable):
            assert not ignorable(v)
            if not args:
                self.error(f'missing arg "{v.key}" for template "{tmplname}"')
            return args.pop(0)
        else:
            return v
