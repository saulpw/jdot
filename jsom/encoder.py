from .jsom import InnerDict, deep_match, deep_del


class JsomEncoder:
    def __init__(self):
        self.revmacros = {}

    def restart(self):
        self.revmacros = {
            v: k
            for k, v in self.macros.items()
            if not isinstance(v, (dict, list))
        }

    def iterencode(self, obj, depth=0, parents=None):
        ''
        if parents is None:
            parents = []

        if isinstance(obj, dict):
            if not obj:
                yield '{}'
                return

            # emit first macro, if any match
            macro_invocations = []
            macros_remaining = list(self.macros.items())
            copied = False
            while macros_remaining:
                macroname, macro = macros_remaining[0]
                m = deep_match(obj, macro)
                if m is False:  # didn't match
                    macros_remaining.pop(0)
                    continue

                if isinstance(m, dict):  # matched with args
                    if m:
                        macro_invocation = ['(', macroname]
                        args = [self.iterencode(x, depth=depth+1) for x in m.values()]
                        macro_invocation.extend(x.strip() for y in args for x in y if x.strip())
                        macro_invocation.append(')')
                    else:
                        macro_invocation = [macroname]

                    macro_invocations.append(macro_invocation)

                    if isinstance(macro, InnerDict):
                        if not copied:
                            obj = obj.copy()
                            copied = True
                        deep_del(obj, macro)
                    else:
                        obj = {}

                    if not obj:
                        break

            # if no macro fully applied, emit rest of dictionary

            show_braces = (depth != 0) and (len(macro_invocations) + len(obj) > 1)

            if show_braces:
                yield '{'

            for innards in macro_invocations:
                yield from innards

            for k, v in obj.items():
                yield f'.{k}'
                yield from self.iterencode(v, depth=depth+1, parents=parents+[obj])

            if show_braces:
                yield '}'

        elif isinstance(obj, (list, tuple)):
            if not obj:
                yield '['
                yield ']'
                return

            if depth > 0:
                yield '['

            for v in obj:
                yield from self.iterencode(v, depth=depth+1, parents=parents+[obj])

            if depth > 0:
                yield ']'

        elif obj in self.revmacros:
            yield self.revmacros[obj]
        else:
            yield self.literal(obj)

    def literal(self, obj):
        if isinstance(obj, str):
            if not obj:
                return '""'

            delim = "'" if obj.count('"') > obj.count("'") else '"'

            r = ''
            for ch in obj:
                if ch in ['\\', delim]:
                    r += '\\'
                r += ch

            return delim + r + delim

        elif obj is True:
            return 'true'
        elif obj is False:
            return 'false'
        elif obj is None:
            return 'null'
        else:
            return f'{obj}'

    def encode_oneliner(self, obj):
        return self.encode(obj, formatter=' '.join)

    def encode(self, obj, formatter=None):
        if not formatter:
            formatter = self.format_better
        return formatter(self.iterencode(obj))

    def format_better(self, toks):
        chonks = list(chonker(toks))

        rules = [
            (+10, ' ', lambda a, b: a.toks[-1].startswith('.') and b.toks[0].startswith('.')),
            (+10, ' ', lambda a, b: a.toks[-1].startswith('.')),
            (+10, '', lambda a, b: b.toks[0] in '}]>)'),
            (+10, '', lambda a, b: a.toks[-1] in '{[<('),
            (+10, ' ', lambda a, b: len(str(a).strip()) + len(str(b).strip()) < self.options.get('maxwidth', 80) and a.end_level == b.start_level),
            (-10, '', lambda a, b: a.toks[-1] in '}]>)' and b.toks[0] not in '}]>)'),
        ]

        i = 0
        while i < len(chonks)-1:
            total = 0
            total_ws = []
            for rulenum, (amt, ws, f) in enumerate(rules):
                r = f(chonks[i], chonks[i+1])
                if r:
                    if amt == -10:  # absolutely not
                        total = amt
                        break
#                    print(f'rule #{rulenum} fired with "{chonks[i]}" and "{chonks[i+1]}"')
                    total += amt
                    total_ws.append(rulenum)

            if total >= 10:
                _, ws, _ = rules[total_ws[0]]
                if ws:
                    chonks[i].toks.append(ws)
                chonks[i].toks.extend(chonks[i+1].toks)
                chonks[i].end_level = chonks[i+1].end_level
                del chonks[i+1]
            else:
                i += 1

        return '\n'.join((x.start_level)*' '+str(x) for x in chonks)


def chonker(toks):
    level = 0
    for tok in toks:
        if tok in '[{<(':
            yield Chonk(tok, level=level)
            level += 1
        elif tok in ']}>)':
            level -= 1
            yield Chonk(tok, level=level)
        else:
            yield Chonk(tok, level=level)


class Chonk:
    def __init__(self, *toks, level=0):
        self.toks = list(toks)
        self.start_level = level
        self.end_level = level

    def __str__(self):
        return ''.join(self.toks)
