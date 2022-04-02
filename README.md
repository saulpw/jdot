# JSOM: JSON minus Notation plus Macros

[![Test](https://github.com/saulpw/jsom/actions/workflows/main.yml/badge.svg)](https://github.com/saulpw/jsom/actions?query=workflow%3ATest)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/saulpw/jsom/blob/master/LICENSE.txt)

[Alternate possible names: NOSJ (Nicer Object Syntax for JSON), JSM]

## A human-readable, -writable, and -diffable format for reasonable JSON

Remove all the extraneous symbols from JSON, and it becomes a lot easier to read and write.  Add comments and macros and it's almost pleasant.  And the parser is easier to write too.  Some little ergonomics go a long way.

Conversion between reasonable JSON and JSOM is lossless.


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

The `jsom` script (installed as above) converts between JSON and JSOM.

As a quick win, you can easily construct JSON from JSOM on the command line, in many cases without even having to press the Shift key:

```
$ jsom '.fetch singles .query { .city portland .cats { .min 1 .max 6'

{"fetch": "singles", "query": {"city": "portland", "cats": {"min": 1, "max": 6}}}
```

(Note that the final closing braces may be omitted unless the `strict` option is set to true.)

Other options:
- `-d <filename.jsom>` to decode JSOM from a file (or `-` for stdin); sets output as JSON
- `-e <filename.json>` to encode JSON from a file (or `-` for stdin); sets output as JSOM
- `-m` to set output as JSOM
- `-n` to set output as JSON

These options can be used multiple times and mixed-and-matched.  For example:

```
jsom -d api-macros.jsom -e api-input.json > api-output.jsom
```

This will output the result from `api-macros.jsom` (which should not output anything, if it's only defining macros) and then output the result of `api-input.json` as JSOM, with macros substituted as it finds them.


## Python library

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
  - `#` begins a comment until end of line
  - `[]{}<>()` are reserved symbols and will not be part of any other token

## primitive types

- int (`42`)
- float (`2.71`)
- string (either `"hello"` or `'world'`)
   - escape quote/newline/backslash with backslash; embedded newlines allowed
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
     - after setting a value, the next `.key` will be inserted into the most recently opened dict
  - key must be reasonable: no spaces or symbols that have meaning in JSOM

## globals

The container at the bottom of the parsing stack is where created objects (if it's a list) or key-values (if it's a dict) are stored into.
A token like `@globals` will clear out the parsing stack and push the named global container onto it.  There are only a few globals defined:

## `@options`

Set values at various keys in `@options` to control aspects the JSOM parser.

  - `.debug` (default `false`): set to `true` for extra debug output.
  - `.strict` (default `false`): set to `true` to error on unknown token (otherwise implicit conversion to string)

For example:
```
@options .strict true
```

## `@macros`

Add items to `@macros` to create new macro definitions.
The key is the macro name, and the value is the template to be matched or filled.
The template is given using the same JSOM syntax, so JSOM output can be copied verbatim into a macro.

Variable values are designated like `?varname`.
Variables can match any type, including containers.

The entire macro must match completely in order to be emitted by `encode()`.
For a full dict, no keys can be missing and no extra keys may be present.

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

# BNF

```
id := [A-z_][A-z_0-9]*

string-literal := dquote string-char* dquote
                | squote string-char* squote

string-char := '\' esc-char
             | unicode-char  // including newlines

esc-char := '\'
          | 'n'
          | squote
          | dquote

bool-literal := 'true' | 'false'

Value := 'null'
      | bool-literal
      | string-literal
      | int-literal
      | float-literal
      | '[' InnerList ']'
      | '{' InnerDict '}'
      | '<' InnerDict '>'
      | List
      | Dict
      | PartialDict
      | Variable  // only useful within a macro
      | Macro

InnerList := Value*
InnerDict := KeyValue*

Key := '.' id
     | '.' string-literal
     | '.'                // matches any key

Variable := '?' id
          | '?'    // ignore contents

Macro := '(' id InnerList ')'
       | id     // instantiate macro without args

SectionName := '@' id  // can be 'options' or 'macros' or 'output'
         | '@'     // 'output'

Top := SectionName InnerDict
         | InnerList
         | InnerDict

Jsom := Top+
```

# Future ideas (not implemented yet)
  - multiple variables with the same `?varname` should match the same value, and should only be passed in the macro args once.
  - macro invocation with named arguments: `(foo .arg1 42 .arg2 "bar")`

# Copyright and License

Copyright 2022 Saul Pwanson

Licensed under the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0).
