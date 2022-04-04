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
            formatter = ' '.join
        return formatter(self.iterencode(obj))
