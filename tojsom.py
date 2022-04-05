#!/usr/bin/env python3

import sys
import json

import yaml

import jsom

j = jsom.JsomCoder()
out = []

for fn in sys.argv[1:]:
    contents = open(fn).read()
    if fn.endswith('yaml'):
        d = yaml.load(contents, yaml.Loader)
    elif fn.endswith('json'):
        d = json.loads(contents)
    elif fn.endswith('jsom'):
        d = j.decode(contents)

    if isinstance(d, list):
        out.extend(d)
    elif d:
        out.append(d)

print(j.encode(out, 'pretty'))
