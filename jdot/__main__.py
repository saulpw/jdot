#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import sys
import json
import argparse

from jdot import JdotCoder, JdotFormatter


def json2jdot(s):
    j = JdotCoder()
    d = json.loads(s)
    s = j.encode(d)
    return "\n".join(line.rstrip() for line in s.splitlines())


class JsonDefaultEncoder(json.JSONEncoder):
    def default(self, obj):
        return str(obj)


def jdot2json(s):
    j = JdotCoder()
    d = j.decode(s)
    return json.dumps(d, cls=JsonDefaultEncoder)


def read_arg(fn):
    if fn == "-":
        return sys.stdin.read()
    return open(fn).read()


def iterobjs(d):
    if d is None:
        return
    elif isinstance(d, list):
        yield from d
    else:
        yield d


def argparser():

    parser = argparse.ArgumentParser(description="jdot")
    inputs = parser.add_argument_group("Inputs")
    inputs.add_argument("-d", "--in-jdot", dest="in_jdot", type=str, required=False, action='append', nargs='?')
    inputs.add_argument(
        "-e", "-n", "--in-json", dest="in_json", type=str, required=False, action='append', nargs='?'
    )
    out_format = parser.add_mutually_exclusive_group(required=False)
    out_format.add_argument(
        "-j",
        "--out-json",
        dest="out_json",
        action="store_true",
        default=True,
        required=False,
    )
    out_format.add_argument(
        "-m", "--out-jdot", dest="out_json", action="store_false", required=False
    )
    parser.add_argument("--debug", action="store_true", default=False, required=False)
    format_options = parser.add_argument_group("Format options")
    format_options.add_argument(
        "-p",
        "--pretty",
        dest="pretty_print",
        action="store_true",
        default=False,
        required=False,
    )
    format_options.add_argument(
        "--indent",
        type=int,
        default=4,
        required=False,
        help="number of spaces to indent in output (defaults to 4)",
    )
    format_options.add_argument(
        "--indent-str",
        type=str,
        required=False,
        help="specify which indentation character(s) to use.",
    )
    format_options.add_argument(
        "--length-limit",
        type=int,
        required=False,
        help="""
        specify an approximate maximum number of characters that will be considered
        for emitting a group of tokens on a single line.
        """,
    )
    format_options.add_argument(
        "--value-limit",
        type=int,
        required=False,
        help="""
        specify the number of contained non-nested values that will be considered
        for emitting a group of tokens on a single line.
        """,
    )
    format_options.add_argument(
        "--strip-spaces",
        type=str,
        required=False,
        help="""
        strip_spaces specifies for which parenthesis types the space
        immediately after the open paran or immediately before the close
        paren will be stripped. For example, specifying strip_spaces='[]'
        will emit lists as [1 2 3] instead of [ 1 2 3 ].
    """,
    )
    format_options.add_argument(
        "--close-on-same-line",
        action="store_true",
        required=False,
        help="""
        place closing paren for multiline groups after the last enclosed value and
        not on a newline
        """,
    )
    format_options.add_argument(
        "--dedent-last-value",
        action="store_true",
        required=False,
        help="""
        whenever both the current group and the last inner group are wrapped, the
        latter is not indented.  This works best when used in conjunction with dict
        entries sorted by increasing size.
    """,
    )
    ordering = format_options.add_mutually_exclusive_group(required=False)
    ordering.add_argument("--order-by-key", action="store_true", required=False)
    ordering.add_argument("--order-by-size", action="store_true", required=False)

    return parser


def main():
    jdotargs = []
    objs = []
    format_options = {}
    sort_key = None
    j = JdotCoder()

    argv = sys.argv[1:]
    args, jdotargs = argparser().parse_known_args(argv)

    if args.in_jdot:
        for f_jdot in args.in_jdot:
            d = j.decode(read_arg(f_jdot))
            objs.extend(iterobjs(d))
            args.out_json = True
    if args.in_json:
        for f_json in args.in_json:
            d = json.loads(read_arg(f_json))
            objs.extend(iterobjs(d))
            args.out_json = False

    format_options["indent_str"] = " " * args.indent
    if args.indent_str:
        format_options["indent_str"] = args.indent_str
    format_options["length_limit"] = args.length_limit
    format_options["value_limit"] = args.value_limit
    format_options["strip_spaces"] = args.strip_spaces
    format_options["close_on_same_line"] = args.close_on_same_line
    format_options["dedent_last_value"] = args.dedent_last_value
    if args.order_by_key:
        sort_key = "key"
    elif args.order_by_size:
        sort_key = "size"

    if args.debug:

        j.options["debug"] = True

    if jdotargs:
        d = j.decode(" ".join(jdotargs))
        objs.extend(iterobjs(d))

    if objs:
        if args.out_json:
            if args.pretty_print:
                indent = args.indent
            else:
                indent = None
            print(
                json.dumps(
                    objs,
                    cls=JsonDefaultEncoder,
                    sort_keys=(sort_key == "key"),
                    indent=indent,
                )
            )
        else:
            if args.pretty_print:
                formatter = JdotFormatter(**format_options)
            else:
                formatter = None
            print(j.encode(objs, formatter, sort_key))


if __name__ == "__main__":
    main()
