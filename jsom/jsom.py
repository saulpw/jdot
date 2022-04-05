#!/usr/bin/env python3


class Variable:
    def __init__(self, key=''):
        '''*key* is key in output dict, if specified (otherwise matches anything, and is not saved).'''
        self.key = key

    def __repr__(self):
        return '?'+self.key


class InnerDict(dict):
    'instantiate only the inner keys and not the dict itself'
    pass


def deep_update(a: dict, b: dict, type=lambda v: v):
    ''
    if not b:
        return a

    for k, vb in b.items():
        va = a.get(k, None)
        if isinstance(va, dict) and isinstance(vb, dict):
            deep_update(va, vb)
        elif isinstance(va, list):
            va.append(vb)
        else:
            a[k] = type(vb)
    return a


def deep_match(a, b):
    'Return dict of matches between a and b if a and b are dicts/lists and a and b are exact matches, or boolean equality otherwise.'
    if isinstance(b, Variable):  # Variables match anything
        if b.key == '?':  # match but don't return value
            return {}
        return {b.key: a}

    elif isinstance(a, dict) and isinstance(b, dict):
        if not isinstance(b, InnerDict):
            keydiffs = set(a.keys()) ^ set(b.keys())
            if keydiffs and '' not in keydiffs:
                return False
        ret = {}
        for k, v in b.items():
            if not k:
                continue
            if k not in a:  # all `k` in `b` must be in `a` to match
                return False
            m = deep_match(a[k], v)
            if m is False:  # values must match
                return False
            if isinstance(m, dict):
                deep_update(ret, m)

        return ret

    elif isinstance(a, list) and isinstance(b, list):
        ret = False
        for x in b:
            for y in a:
                m = deep_match(y, x)
                if m is False:  # each item in `b` must match at least one item in `a`
                    continue
                if isinstance(m, dict):
                    if ret is False:
                        ret = {}
                    deep_update(ret, m)  # , lambda v: [v])
                    break
        return ret

    return a == b


def deep_del(a: dict, b: dict):
    'deep remove contents of *b* from *a*.'
    for k, v in b.items():
        if not k:
            a.clear()
            return

        assert k in a, (a, k)
        if isinstance(a[k], dict):
            if isinstance(v, Variable):
                del a[k]  # remove entire matched entry
                continue

            assert isinstance(v, dict), v
            deep_del(a[k], v)
            if not a[k]:  # remove empty dicts
                del a[k]

        elif isinstance(a[k], list):
            if isinstance(v, Variable):
                del a[k]
                continue

            assert isinstance(v, list), v
            for needle in v:
                for i, item in enumerate(a[k]):
                    if deep_match(item, needle) is not False:
                        deep_del(item, needle)
                        del a[k][i]
                        if not a[k]:
                            del a[k]
                        break
        else:
            del a[k]


def deep_len(x):
    'returns the amount of primitive values in a nested structure.'
    if isinstance(x, dict):
        return sum(map(deep_len, x.values()))
    elif isinstance(x, list):
        return sum(map(deep_len, x))
    return 1
