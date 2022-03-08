# JSOM: JSON minus Notation plus Macros

[
Alternate names for consideration:
 - NOSJ: Nicer Object Syntax for JSON
 - JSM
]

## A human-readable, -writable, and diffable format for reasonable JSON

Remove all the extraneous symbols from JSON, and it becomes a lot easier to read and write.  Add comments and macros and it's almost pleasant.  And the parser is easier to write too.  Some little ergonomics go a long way.

Conversion between JSOM and reasonable JSON is lossless.


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

With macros, it could look like this:

```
macros.point < .points [{ .xy { .x ?x .y ?y } }] .names [ ?name ] >

.objects {
    (point 0 0 "nowhere")
    (point 0 4 "here")
    (point 4 0 "there")
    (point 4 4 "everywhere")
}
```


# CLI Usage

The `jsom` command-line utility converts to and from JSOM:

```
$ jsom .a 3 .b foo   # decode args to JSON
{ "a": 3, "b": "foo" }

$ echo '{ "a": 3, "b": "foo" }' | jsom  # encode stdin to JSON
.a 3 .b "foo"

$ jsom -e foo.json   # encode foo.json into JSOM on stdout; effectively json2jsom

$ jsom -d bar.jsom   # decode bar.jsom into JSON on stdout; effectively jsom2json
```

# Loose specification

### whitespace and comments

  - whitespace is not necessary between symbols
  - where whitespace delimits tokens, any whitespace is fine; newlines or specific indentation is not necessary
  - `;` begins a comment until end of line
  - `[]{}<>()` are reserved symbols and cannot be part of any other token

### basic types

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

### macro invokation
- `(macro-name arg1 arg2 ...)` invokes a macro with given args
- `macro-name` (no parens) invokes a macro without args


### macro definition
- defined in their own file; pass filename to `-m` option
- macros are simply elements in the toplevel dict, with the key as the macro name:

#### whole macros

With this macro defined in a macros file:

```
.foo {
    .bar 15
    .baz [ "a" "b" ]
}
```

`foo` in any JSOM file will emit a copy of this dict with keys "bar" and "baz".

#### variable elements

Macro parameters can be given in the definition with `?name` (name is optional; parameters are positional).

```
.row {
  .options { .max ?max }
  .point ?p
}
```

`(row 42 { .lat 72.82398 .long 122.91287 })`` will emit `{ "options": { "max": 42 }, "point": { "lat": 72.82398: "long": 122.91287 } }`

Variables can match any type, including containers.

A whole macro must match completely in order to be emitted by the json2jsom converter.
No keys can be missing and no extra keys may be present.

#### partial macros

With this macro:

```
.macro.std < .min 0 .max 10000 >
```

Any dict can include `bigsize` in its definition, and it will acquire the `min` and `max` key/values itself (without creating an inner wrapping dict).

### outer structure

If parsing begins with a `.key` then a dict is returned.  Otherwise, it begins with a value, and a list is returned.
