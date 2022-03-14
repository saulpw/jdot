#!/usr/bin/env python3

import sys
import json

from jsom import JsomCoder


def json2jsom(s):
    j = JsomCoder(indent=' ')
    d = json.loads(s)
    s = j.encode(d)
    return '\n'.join(line.rstrip() for line in s.splitlines())


class JsonDefaultEncoder(json.JSONEncoder):
    def default(self, obj):
        return str(obj)


def jsom2json(s):
    j = JsomCoder(indent=' ')
    d = j.decode(s)
    return json.dumps(d, cls=JsonDefaultEncoder)


def read_arg(fn):
    if fn == '-':
        return sys.stdin.read()
    return open(fn).read()


def main():
    i = 1
    jsomargs = []
    j = JsomCoder(indent=' ')
    while i < len(sys.argv):
        arg = sys.argv[i]
        i += 1

        if arg in ['-d', '--decode']:
            contents = read_arg(sys.argv[i])
            d = j.decode(contents)
            print(json.dumps(d, cls=JsonDefaultEncoder))
            i += 1
        elif arg in ['-e', '--encode']:
            contents = read_arg(sys.argv[i])
            d = json.loads(contents)
            s = j.encode(d)
            print('\n'.join(line.rstrip() for line in s.splitlines()))
            i += 1
        else:
            jsomargs.append(arg)

    if jsomargs:
        print(jsom2json(' '.join(jsomargs)))


if __name__ == '__main__':
    main()
