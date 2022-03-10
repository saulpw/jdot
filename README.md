# JSOM: JSON minus Notation plus Macros

[Alternate possible names: NOSJ (Nicer Object Syntax for JSON), JSM]

## A human-readable, -writable, and -diffable format for reasonable JSON

Remove all the extraneous symbols from JSON, and it becomes a lot easier to read and write.  Add comments and macros and it's almost pleasant.  And the parser is easier to write too.  Some little ergonomics go a long way.

Conversion between reasonable JSON and JSOM is lossless.

## Table of Contents

- Features
- Usage
- Install
- Format
  - Macros

## Features

- no extraneous characters
- barebones simple parser
- whitespace agnostic
- line comments
- convenient macros
- feels a bit like Lisp

## What does JSOM look like?

JSOM looks like this:

```
.objects {
   .names [ "nowhere" "here" "there" "everywhere" ]
   .points [
      { .xy { .x 0 .y 0 } }
      { .xy { .x 0 .y 4 } }
      { .xy { .x 4 .y 0 } }
      { .xy { .x 4 .y 4 } }
   ]
}
```

which translates to this JSON:


```
{
  "objects": {
    "names": [ "nowhere", "here", "there", "everywhere" ],
    "points": [
      { "xy": { "x": 0, "y": 0 } },
      { "xy": { "x": 0, "y": 4 } },
      { "xy": { "x": 4, "y": 0 } },
      { "xy": { "x": 4, "y": 4 } }
    ]
  }
}
```

Using a macro, it could look like this (and the resulting output would be the same as above):

```
@macros
.point { .points [{ .xy { .x ?x .y ?y } }] .names [ ?name ] }

@output
.objects {
    (point 0 0 "nowhere")
    (point 0 4 "here")
    (point 4 0 "there")
    (point 4 4 "everywhere")
}
```

# Install

jsom requires [Python 3.6](https://wsvincent.com/install-python/) or higher.

Once Python is set-up on your operating system, you can install jsom using pip:

```
pip3 install git+https://github.com/saulpw/jsom.git
```

or you can run the install script locally from your machine:

```
git clone https://github.com/saulpw/jsom.git
cd jsom
python3 setup.py install
```

# Usage

## CLI

The `jsom` command-line utility converts to and from JSOM:

```
$ jsom .a 3 .b foo   # decode JSOM in args to JSON
{ "a": 3, "b": "foo" }

$ echo '{ "a": 3, "b": "foo" }' | jsom  # encode JSON on stdin to JSOM
.a 3 .b "foo"

$ jsom -e foo.json   # encode: foo.json into JSOM on stdout; effectively json2jsom

$ jsom -d bar.jsom   # decode: bar.jsom into JSON on stdout; effectively jsom2json
```

## Library

The `jsom` Python library can also be used programmatically:

```
>>> from jsom import JsomCoder

>>> j = JsomCoder()

>>> j.encode(dict(a="foo", pi=3.14, c=[1,2,3,4]))
 .a "foo"
  .pi 3.14
  .c [1 2 3 4]

>>> j.decode('.a "foo" .pi 3.14 .c [1 2 3 4]')

{'a': 'foo', 'pi': 3.14, 'c': [1, 2, 3, 4]}
```

# format specification

## whitespace and comments

  - whitespace-separated tokens and quoted strings
  - any whitespace is fine; newlines always possible and never required
    -  no specific indentation is necessary
  - `;` begins a comment until end of line
  - `[]{}<>()` are reserved symbols and cannot be part of any other token

## primitive types

- int (`42`)
- float (`2.71`)
- string (`"hello"`)
- bool (`true` or `false`)
- `null`

### list

- `[` and `]` contain an list with values of any type (including dicts or other lists)
  - elements separated by whitespace

### dict

- `{` and `}` contain a dict hash
  - `{ .key "value" .key2 3.14 }` => `{ "key": "value", "key2": 3.14 }`
  - `{ .outer .inner { ... } }` => `{ "outer": { "inner": { ... } } }`
     - the outer key is automatically closed after the inner value finishes; `inner` is the only element in `outer`
    - string in double quotes, standard escape with `\\`
  - key must be reasonable: no spaces or leading symbols that have meaning in JSOM

## globals

The container at the bottom of the parsing stack is where created objects (if it's a list) or key-values (if it's a dict) are stored into.
A token like `@globals` will clear out the parsing stack and push the named global container onto it.  There are only a few globals defined:

## `@options`

Set values at various keys in `@options` to control aspects the JSOM parser.

  - `.debug` (default `false`): set to true for extra debug output.
  - `.indent` (default `""`): set to one or more spaces to pretty-print the output over multiple lines 

```
@options .debug true
@options .indent "  "
```

## `@macros`

Add items to `@macros` to create new macro definitions.
The key is the macro name, and the value is the template to be matched or filled.
The template is given using the same JSOM syntax, so JSOM output can be copied verbatim into a macro.

Variable values are designated like `?varname`.
Variables can match any type, including containers.

The entire macro must match completely in order to be emitted by `encode()`.
For a full dict, no keys can be missing and no extra keys may be present.

Future (not implemented yet):
  - Multiple variables with the same `?varname` should match the same value, and should only be passed in the macro args for the first instance.
  - `?` by itself (no varname) may check for presence only, and would not need to be passed in the macro args at all.
     - What value would be used when instantiated?  null?

### macro invocation

A macro can be invoked lisp-style with parens wrapping the macro name and its arguments (which themselves can be values or containers or other nested macros):

```
@macros .bounds { .min ?min .max ?max }
@output (bounds 5 20)
```
is decoded to:

```
{"min": 5, "max: 20}
```

A macro without arguments can be invoked without the wrapping parens:

```
@macros .default-bounds { .min 0 .max 1000 }
@output { .bounds default-bounds }
```

is decoded to:

```
{"bounds": {"min": 0, "max": 1000}}
```

### partial dict

A partial or inner macro, with its template enclosed in `<` and `>`, is like a dict, but applies its key/value pairs to the enclosing dict, instead of opening a new dict:

```
@macros .inner-bounds < .min ?min .max ?max >
@output { (inner-bounds 0 100) .val 50 }
```

is decoded to:

```
{ "min": 0, "max": 100, "val": 50 }
```
