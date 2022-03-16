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

    def iterencode(self, obj, depth=0, indent='', parent=[]):
        ''
        if isinstance(obj, dict):
            if not obj:
                yield '{}'
                return

            # emit first macro, if any match
            innards = []
            macros_remaining = list(self.macros.items())
            while macros_remaining:
                macroname, macro = macros_remaining[0]
                m = deep_match(obj, macro)
                if m is False:  # didn't match
                    macros_remaining.pop(0)
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

            if depth > 0 and len(parent) != 1:
                yield '{'

            yield from innards

            for k, v in sorted(obj.items(), key=len):
                if indent and len(obj) > 1:
                    yield '\n' + depth*indent
                yield f'.{k}'
                yield from self.iterencode(v, depth=depth+1, indent=indent, parent=obj)

            if depth > 0 and len(parent) != 1:
                yield '}'

        elif isinstance(obj, list):
            if not obj:
                yield '[]'
                return

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

    def encode(self, *args):
        if len(args) == 1:
            args = args[0]
        else:
            args = list(args)
        return ' '.join(self.iterencode(args, indent=self.options['indent'], parent=[args])).strip()
