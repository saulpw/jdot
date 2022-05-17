#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import sys
import json

import yaml

import jdot

j = jdot.JdotCoder()
out = []

for fn in sys.argv[1:]:
    contents = open(fn).read()
    if fn.endswith("yaml"):
        d = yaml.load(contents, yaml.Loader)
    elif fn.endswith("json"):
        d = json.loads(contents)
    elif fn.endswith("jdot"):
        d = j.decode(contents)

    if isinstance(d, list):
        out.extend(d)
    elif d:
        out.append(d)

print(j.encode(out, "pretty"))
