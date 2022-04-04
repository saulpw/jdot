#!/usr/bin/env python3

import sys
import json

from jsom import JsomCoder


def json2jsom(s):
    j = JsomCoder()
    d = json.loads(s)
    s = j.encode(d)
    return '\n'.join(line.rstrip() for line in s.splitlines())


class JsonDefaultEncoder(json.JSONEncoder):
    def default(self, obj):
        return str(obj)


def jsom2json(s):
    j = JsomCoder()
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
    jsomargs = []
    objs = []
    j = JsomCoder()

    while i < len(sys.argv):
        arg = sys.argv[i]
        i += 1

        out_json = True

        if arg in ['-d', '--in-jsom']:
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

        elif arg in ['-m', '--out-jsom']:  # encode
            out_json = False

        elif arg in ['--debug']:
            j.options['debug'] = True

        else:
            jsomargs.append(arg)

    if jsomargs:
        d = j.decode(' '.join(jsomargs))
        objs.extend(iterobjs(d))

    if objs:
        if out_json:
            print(json.dumps(objs, cls=JsonDefaultEncoder))
        else:
            print(j.encode(objs))


if __name__ == '__main__':
    main()
