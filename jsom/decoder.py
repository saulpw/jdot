import collections

from .jsom import InnerDict, deep_update, Variable

COMMENT_CHAR = '#'
Token = collections.namedtuple('Token', 'type string start end line')


class DecodeException(Exception):
    pass


class JsomDecoder:
    def error(self, msg):
        t = self.toktuple
        errmsgs = [
            f'ERROR: {msg} at line {t.start[0]+1} (column {t.start[1]})',
            t.line
        ]
        raise DecodeException('\n'.join(errmsgs))

    def tokenize(self, s):
        ''
        escchars = {'n': '\n', '\\': '\\', '\"': '\"'}

        startchnum = 0
        tok = ''

        i = 0  # index into s
        chnum = 0
        linenum = 0
        line = ''

        while i < len(s):
            ch = s[i]
            i += 1
            if ch == '\n' or linenum == 0:
                linenum += 1
                chnum = 0
                eol = s.find('\n', i)
                if eol < 0:
                    eol = len(s)
                line = s[i:eol]
                self.debug(f'{linenum}: {line}')

            chnum += 1

            if ch == COMMENT_CHAR:  # comment, ignore until end of line
                i = eol
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
                startch = chnum
                string = ''
                delim = ch
                while i < len(s):
                    ch = s[i]
                    i += 1
                    if ch == delim:
                        yield Token('str', string, (startline, startch), (linenum, chnum), line)
                        break
                    elif ch == '\\':
                        string += escchars.get(s[i], s[i])
                        i += 1
                    elif ch == '\n':
                        string += ch
                        linenum += 1
                    else:
                        string += ch
                continue

            if ch in '{}[]()<>':
                yield Token(ch, ch, (linenum, chnum), (linenum, chnum+1), line)
            else:
                tok += ch

        if tok:
            yield Token(tok, tok, (linenum, chnum), (linenum, chnum+1), line)
            tok = ''

    def decode(self, s):
        objs = self.iterdecode(self.tokenize(s))
        return objs[0] if len(objs) == 1 else objs

    def iterdecode(self, it):
        '*it* can be str or generator of Token.  Return list of parsed objects.'

        key = None
        ret = []  # root list to return
        stack = [ret]  # path from root
        self.globals['output'] = ret  # make available as '@output'

        while True:
            try:
                self.toktuple = next(it)
            except StopIteration:
                break

            out = None
            append_stack = False
            tok = self.toktuple.string

            self.debug(tok, end=' ')

            if self.toktuple.type == 'str':  # string literal
                out = tok

            elif tok[0] == '?':  # variable
                out = Variable(tok[1:])

            elif tok[0] == '@':  # global variable like '@options' and '@macros'
                name = tok[1:]
                if name not in self.globals:
                    self.error(f'no such global {name}')

                self.debug(f'global {tok}')
                stack = [self.globals[name]]
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
                if isinstance(stack[-1], list):
                    r = dict()           # open new dict by default
                    stack[-1].append(r)  # append it to the list
                    stack[-1] = r        # and replace the list with it
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

            elif tok == '}':  # close dict outer
                r = stack.pop()
                if not isinstance(r, dict):
                    self.error('mismatched closing }')
                continue

            elif tok == ']':  # close list
                r = stack.pop()
                if not isinstance(r, list):
                    self.error('mismatched closing ]')
                continue

            elif tok == '>':  # close dict inner
                r = stack.pop()
                if not isinstance(r, InnerDict):
                    self.error('mismatched closing >')
                continue

            elif tok == '(':  # open macro, instantiate with args
                name = next(it).string
                args = self.iterdecode(it)  # recurse
                if name not in self.macros:
                    self.error(f'no macro named "{name}"')

                out = self.instantiate(self.macros[name], args, name)  # mutates args
                if args:  # none should be left over
                    self.error(f'too many args given to "{name}" {args}')

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

            if isinstance(stack[-1], dict):
                if key is None:
                    if isinstance(out, InnerDict):
                        deep_update(stack[-1], out)
                    elif isinstance(out, dict):
                        deep_update(stack[-1], out)
#                        # leave old dict there, to be filled in with the 'new' dicts inners
                    else:
                        self.error(f'no key given for value {self.literal(out)}')
                else:
                    if key in stack[-1]:
                        oldval = stack[-1][key]
                        if not isinstance(oldval, type(out)):
                            self.error(f'{key} has existing {type(oldval)} value')
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
                stack[-1].append(out)

            else:
                self.error('non-container on top-of-stack')

            if append_stack:
                stack.append(out)

        return ret

    def instantiate(self, v, args, tmplname):
        ''
        if isinstance(v, InnerDict):
            return InnerDict({k: self.instantiate(x, args, tmplname) for k, x in v.items()})
        elif isinstance(v, dict):
            return {k: self.instantiate(x, args, tmplname) for k, x in v.items()}
        elif isinstance(v, list):
            return list(self.instantiate(x, args, tmplname) for x in v)
        elif isinstance(v, Variable):
            if not args and v.key:
                self.error(f'missing arg "{v.key}" for template "{tmplname}"')
            return args.pop(0)
        else:
            return v
