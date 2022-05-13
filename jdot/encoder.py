from .jdot import InnerDict, deep_match, deep_del, deep_len
from .formatter import JdotFormatter


class JdotEncoder:
    def __init__(self):
        self.revmacros = {}

    def restart(self):
        self.revmacros = {
            v: k
            for k, v in self.macros.items()
            if not isinstance(v, (dict, list))
        }

    def iterencode(self, obj, sort_key=lambda x: 0, depth=0, parents=None):
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
                        args = [self.iterencode(x, sort_key, depth=depth+1) for x in m.values()]
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

            show_braces = (depth != 0) and (len(macro_invocations) + len(obj) > 1)

            if show_braces:
                yield '{'

            for innards in macro_invocations:
                yield from innards

            for k, v in sorted(obj.items(), key=sort_key):
                if any(x in k for x in ' .{}<>[]()'):
                    k = self.literal(k)
                yield f'.{k}'
                yield from self.iterencode(v, sort_key, depth=depth+1, parents=parents+[obj])

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
                yield from self.iterencode(v, sort_key, depth=depth+1, parents=parents+[obj])

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

    def encode(self, obj, formatter=None, sort_key=None):
        """Encodes the given object as JDOT using the macros currently
        registered with this encoder.

        formatter can be set None to disable formatting, 'pretty' for
        pretty-printing, or to a function that takes an iterable of tokens and
        inserts whitespace between them to form a string, such as
        ' '.join (= None), an instance of JdotFormatter for pretty-printing
        (default options = 'pretty'), or a user-defined pretty-printing
        function.

        sort_key can be set to None (the default) to emit dict keys in Python's
        natural order, 'key' to order alphabetically by the keys, 'size' to
        order by the number of primitive values in the value, or any function
        taking a key-value pair to be passed to sorted()."""
        if formatter is None:
            formatter = ' '.join
        elif formatter == 'pretty':
            formatter = JdotFormatter()
        if sort_key is None:
            sort_key = lambda x: 0
        elif sort_key == 'key':
            sort_key = lambda x: x
        elif sort_key == 'size':
            sort_key = lambda x: deep_len(x[1])
        return formatter(self.iterencode(obj, sort_key))
