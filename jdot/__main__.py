#!/usr/bin/env python3

import sys
import json

from jdot import JdotCoder, JdotFormatter


def json2jdot(s):
    j = JdotCoder()
    d = json.loads(s)
    s = j.encode(d)
    return '\n'.join(line.rstrip() for line in s.splitlines())


class JsonDefaultEncoder(json.JSONEncoder):
    def default(self, obj):
        return str(obj)


def jdot2json(s):
    j = JdotCoder()
    d = j.decode(s)
    return json.dumps(d, cls=JsonDefaultEncoder)


def read_arg(fn):
    if fn == '-':
        return sys.stdin.read()
    return open(fn).read()


def iterobjs(d):
    if d is None:
        return
    elif isinstance(d, list):
        yield from d
    else:
        yield d


def main():
    i = 1
    jdotargs = []
    objs = []
    pretty_print = False
    format_options = {}
    json_indent = 4
    sort_key = None
    j = JdotCoder()

    out_json = True

    while i < len(sys.argv):
        arg = sys.argv[i]
        i += 1

        if arg in ['-d', '--in-jdot']:
            contents = read_arg(sys.argv[i])
            d = j.decode(contents)
            objs.extend(iterobjs(d))

            out_json = True
            i += 1

        elif arg in ['-e', '-n', '--in-json']:
            contents = read_arg(sys.argv[i])
            d = json.loads(contents)
            objs.extend(iterobjs(d))

            out_json = False
            i += 1

        elif arg in ['-j', '--out-json']:
            out_json = True

        elif arg in ['-m', '--out-jdot']:  # encode
            out_json = False

        elif arg in ['-p', '--pretty']:
            pretty_print = True

        elif arg in ['--indent']:
            json_indent = int(sys.argv[i])
            format_options['indent_str'] = ' '*json_indent
            i += 1

        elif arg in ['--indent-str']:
            format_options['indent_str'] = sys.argv[i]
            i += 1

        elif arg in ['--length-limit']:
            format_options['length_limit'] = int(sys.argv[i])
            i += 1

        elif arg in ['--value-limit']:
            format_options['value_limit'] = int(sys.argv[i])
            i += 1

        elif arg in ['--strip-spaces']:
            format_options['strip_spaces'] = sys.argv[i]
            i += 1

        elif arg in ['--close-on-same-line']:
            format_options['close_on_same_line'] = True

        elif arg in ['--dedent-last-value']:
            format_options['dedent_last_value'] = True

        elif arg in ['--order-by-key']:
            sort_key = 'key'

        elif arg in ['--order-by-size']:
            sort_key = 'size'

        elif arg in ['--debug']:
            j.options['debug'] = True

        else:
            jdotargs.append(arg)

    if jdotargs:
        d = j.decode(' '.join(jdotargs))
        objs.extend(iterobjs(d))

    if objs:
        if out_json:
            if pretty_print:
                indent = json_indent
            else:
                indent = None
            print(json.dumps(
                objs,
                cls=JsonDefaultEncoder,
                sort_keys=(sort_key == 'key'),
                indent=indent))
        else:
            if pretty_print:
                formatter = JdotFormatter(**format_options)
            else:
                formatter = None
            print(j.encode(objs, formatter, sort_key))


if __name__ == '__main__':
    main()
