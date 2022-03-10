# JSOM: JSON minus Notation plus Macros

[Alternate possible names: NOSJ (Nicer Object Syntax for JSON), JSM]

## A human-readable, -writable, and -diffable format for reasonable JSON

Remove all the extraneous symbols from JSON, and it becomes a lot easier to read and write.  Add comments and macros and it's almost pleasant.  And the parser is easier to write too.  Some little ergonomics go a long way.

Conversion between reasonable JSON and JSOM is lossless.

### Features

- no extraneous characters
- barebones simple parser
- whitespace agnostic
- line comments with `;`
- convenient macros
- feels a bit like Lisp

## The JSOM Format

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
  - `#` begins a comment until end of line
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

### macros

```
macros .default-bounds { .min 0 .max 1000 }
macros .bounds { .min ?min .max ?max }
macros .inner-bounds < .min ?min .max ?max >
```

`macros` is a "global" which pushes the macros dictionary.
Keys in this dictionary are macro names, and the values are the macro templates.
Variable values are designated with `?varname`.

The macro definition and template are given using the same JSOM syntax.
Output from JSON converted to JSOM can be copied verbatim into a macro.

#### macro parameters

Macro parameters can be given in the definition with `?name` (name is optional; parameters are positional).

```
.row {
  .options { .max ?max }
  .point ?p
}
```

Variables can match any type, including containers.

The entire macro must match completely in order to be emitted by `encode()`.
No keys can be missing and no extra keys may be present.

### macro invocation

A macro can be invoked lisp-style with parens wrapping the macro name and its arguments (which themselves can be values or containers or other nested macros):

```
(bounds 5 20)
```

A macro without arguments can be invoked without the wrapping parens:

```
default-bounds
```

A partial or inner macro, with its template enclosed in `<` and `>`, is like a dict, but applies its key/value pairs to the enclosing dict, instead of opening a new dict:

```
{ (inner-bounds 0 100) .val 50 }
```

is decoded to:

```
{ "min": 0, "max": 100, "val": 50 }
```


#### partial macros

With this macro:

```
.macro.std < .min 0 .max 10000 >
```

Any dict can include `bigsize` in its definition, and it will acquire the `min` and `max` key/values itself (without creating an inner wrapping dict).

### outer structure

If parsing begins with a `.key` then a dict is returned.  Otherwise, it begins with a value, and a list is returned.
