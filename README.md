# JDOT: a human-readable, -writable, and -diffable format for JSON

## JSON with minimal punctuation, plus Macros

[![Test](https://github.com/saulpw/jdot/actions/workflows/main.yml/badge.svg)](https://github.com/saulpw/jdot/actions?query=workflow%3ATest)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/saulpw/jdot/blob/master/LICENSE.txt)

Remove all the extraneous symbols from JSON, and it becomes a lot easier to read and write.  Add comments and macros and it's almost pleasant.  Some little ergonomics go a long way.

Conversion between reasonable JSON and JDOT is lossless.


## Features

- no extraneous characters
- barebones simple parser
- whitespace agnostic
- line comments
- convenient macros
- round-trippable
- feels a bit like Lisp

## What does JDOT look like?

JDOT looks like this:

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

jdot requires [Python 3.6](https://wsvincent.com/install-python/) or higher.

Once Python is set-up on your operating system, you can install jdot using pip:

```
pip3 install git+https://github.com/saulpw/jdot.git
```

or you can run the install script locally from your machine:

```
git clone https://github.com/saulpw/jdot.git
cd jdot
python3 setup.py install
```

# Usage

## CLI

The `jdot` script (installed as above) converts between JSON and jdot.

As a quick win, you can easily construct JSON from JDOT on the command line, in many cases without even having to press the Shift key:

```
$ jdot '.fetch singles .query { .city portland .cats { .min 1 .max 6'

{"fetch": "singles", "query": {"city": "portland", "cats": {"min": 1, "max": 6}}}
```

(Note that the final closing braces may be omitted unless the `strict` option is set to true.)

Other options:
- `-d <filename.jdot>` to decode JDOT from a file (or `-` for stdin); sets output as JSON
- `-e <filename.json>` to encode JSON from a file (or `-` for stdin); sets output as JDOT
- `-m` to set output as JDOT
- `-n` to set output as JSON

These options can be used multiple times and mixed-and-matched.  For example:

```
jdot -d api-macros.jdot -e api-input.json > api-output.jdot
```

This will output the result from `api-macros.jdot` (which should not output anything, if it's only defining macros) and then output the result of `api-input.json` as JDOT, with macros substituted as it finds them.


## Python library

The `jdot` Python library can also be used programmatically:

```
>>> from jdot import JdotCoder

>>> j = JdotCoder()

>>> j.encode(dict(a="foo", pi=3.14, c=[1,2,3,4]))
 .a "foo"
  .pi 3.14
  .c [1 2 3 4]

>>> j.decode('.a "foo" .pi 3.14 .c [1 2 3 4]')

{'a': 'foo', 'pi': 3.14, 'c': [1, 2, 3, 4]}
```

# Tutorial

This command from [`github-cli`]() uses the Github API to download the list of issues from a github repo in JSON format:

```
gh api repos/saulpw/visidata/issues > visidata-issues.json
```

Now you can browse this JSON using [jq](https://stedolan.github.io/jq/) or [VisiData](https://visidata.org) or just plain [cat](https://www.unix.com/man-page/posix/1posix/cat/):

```
[
  {
    "url": "https://api.github.com/repos/saulpw/visidata/issues/1328",
    "repository_url": "https://api.github.com/repos/saulpw/visidata",
    "labels_url": "https://api.github.com/repos/saulpw/visidata/issues/1328/labels{/name}",
    "comments_url": "https://api.github.com/repos/saulpw/visidata/issues/1328/comments",
    "events_url": "https://api.github.com/repos/saulpw/visidata/issues/1328/events",
    "html_url": "https://github.com/saulpw/visidata/issues/1328",
    "id": 1167366879,
    "node_id": "I_kwDOBEu2Gc5FlJrf",
    "number": 1328,
    "title": "[selection expansion]  Add ability to expand current selection by N rows ",
    "user": {
      "login": "frosencrantz",
      "id": 631242,
      "node_id": "MDQ6VXNlcjYzMTI0Mg==",
      "avatar_url": "https://avatars.githubusercontent.com/u/631242?v=4",
      "gravatar_id": "",
      "url": "https://api.github.com/users/frosencrantz",
      "html_url": "https://github.com/frosencrantz",
      ...
```

Convert to JDOT:

```
$ jdot -e visidata-issues.json > visidata-issues.jdot
```

```
{.url "https://api.github.com/repos/saulpw/visidata/issues/1328" .repository_url "https://api.github.com/repos/saulpw/visidata"
.labels_url "https://api.github.com/repos/saulpw/visidata/issues/1328/labels{/name}"
.comments_url "https://api.github.com/repos/saulpw/visidata/issues/1328/comments" .events_url "https://api.github.com/repos/saulpw/visidata/issues/1328/events"
.html_url "https://github.com/saulpw/visidata/issues/1328" .id 1167366879
.node_id "I_kwDOBEu2Gc5FlJrf" .number 1328 .title "[selection expansion]  Add ability to expand current selection by N rows "
.user {.login "frosencrantz" .id 631242 .node_id "MDQ6VXNlcjYzMTI0Mg=="
 .avatar_url "https://avatars.githubusercontent.com/u/631242?v=4" .gravatar_id ""
 .url "https://api.github.com/users/frosencrantz" .html_url "https://github.com/frosencrantz"
 ...
```

Now certain things in a bug report are important to capture, but much of the JSON are inlined objects with a lot of extra information that can be removed, and joined from another table if necessary.

To start, we can factor out the list of open issue id `.number` and `.title`.  We can make a `ghapi-macros.jdot` with this:

```
@macros
.issue { .number ?number .title ?title . ? }
```

This puts an `.issue` macro into the `macros` global dictionary, which matches any object with both `.number` and `.title` keys, captures the values of those keys, and discards the rest.
(`.` matches any key and `?` matches any value and discards it.)

Now feed this into `jdot` with `-d` to decode the JDOT macros file first:

```
$ jdot -d ghapi-macros.jdot -e visidata-issues.json > visidata-issues.jdot
```

```
(issue 1328
  "[selection expansion]  Add ability to expand current selection by N rows ")
(issue 1327
  "[selection expansion] Expand current selection with a comma command that expands all matching selection.")
(issue 1324 "Make it possible to 'just open' a gpkg [sqlite] ")
(issue 1319 "Input mysteriously stopped working")
```

And so this is the list of open issue ids and titles, which can be read or modified or reconstituted into skeleton JSON.

Now, the formatter defaults to a max width of 80 chars, so issues don't always fit on one line.
We can set the `maxwidth` option by adding this to `ghapi-macros.jdot`:

```
@options .maxwidth 240
```

Suppose we want to capture some additional information, like the `.user` field.  In this field, the only thing we care about is the `.login` value.
So let's make another macro.

This, however, won't do what we want:

```
.user { .user { .login ?user . ? } . ? }
```

This won't capture both the user login and the issue values, because whichever macro comes first will soak up all the other keyvalue, before the second macro gets a chance to capture them.
So if we want to capture both the issue and the user, we have to use an unenclosed object, wrapped inside `<` and `>`, and put this smaller-scoped macro before the `.issue` macro:

```
.user < .user { .login ?user . ? } >
```

The .user macro has an inner `. ?` wildcard (to discard the inlined denormalized user object), but does *not* have an outer wildcard, so that the rest of the object is available match the rest of the macros.

This outputs:

```
(issue 1328 "[selection expansion]  Add ability to expand current selection by N rows ")
{(user "frosencrantz")}
(issue 1327 "[selection expansion] Expand current selection with a comma command that expands all matching selection.")
{(user "frosencrantz")}
(issue 1324 "Make it possible to 'just open' a gpkg [sqlite] ")
{(user "rduivenvoorde")}
(issue 1319 "Input mysteriously stopped working")
{(user "anjakefala")}
```

Now, this does capture the information, but isn't structurally correct, and won't reconstitute the JSON accurately; there will be two objects (an issue object and a user object).

So if we want only one for each issue (with the user object nested inside), both the inner object in the user macro and the .issue macro also must also be defined using unenclosing brackets:

```
@macros
.user < .user < .login ?user . ? > >
.issue < .number ?number .title ?title . ? >
```

Now this gives:


```
{(user "frosencrantz")
 (issue 1328 "[selection expansion]  Add ability to expand current selection by N rows ")}
{(user "frosencrantz")
 (issue 1327 "[selection expansion] Expand current selection with a comma command that expands all matching selection.")}
{(user "rduivenvoorde")
 (issue 1324 "Make it possible to 'just open' a gpkg [sqlite] ")}
{(user "anjakefala")
 (issue 1319 "Input mysteriously stopped working")}
```

Now we can add some more macros to pull out other values of interest:

```
@macros
.user < .user < .login ?user . ? > >
.label < .labels [ { .name ?name . ? } ] >
.dates < .created_at ?created .modified_at ?modified .closed_at ?closed >
.crickets < .assignee null .comments 0 .reactions { .total_count 0 . ? } >
.comments-reactions < .comments ?num_comments .reactions { .total_count ?num_reactions . ? } >
.issue < .number ?number .title ?title . ? >
```

Which yields this:

```
{(user "frosencrantz")
 (label "wishlist")
 (comments-reactions 3 0)
 (issue 1328 "[selection expansion]  Add ability to expand current selection by N rows ")}
{(user "frosencrantz")
 (label "wishlist")
 crickets (issue 1327 "[selection expansion] Expand current selection with a comma command that expands all matching selection.")}
{(user "rduivenvoorde")
 (label "wishlist")
 (comments-reactions 1 0)
 (issue 1324 "Make it possible to 'just open' a gpkg [sqlite] ")}
{(user "anjakefala")
 (label "bug")
 (comments-reactions 0 0) (issue 1319 "Input mysteriously stopped working")}
```

Now, to reconstitute this into JSON (which will not have the discarded fields, of course):

```
$ jdot -d ghapi-macros.jdot -d visidata-issues.jdot
```

This uses the same macros file as was used to encode the original JDOT, and decodes the generated JDOT:

```
[
  {
    "user": { "login": "frosencrantz" },
    "labels": [ { "name": "wishlist" } ],
    "comments": 3,
    "reactions": { "total_count": 0 },
    "number": 1328,
    "title": "[selection expansion]  Add ability to expand current selection by N rows "
  },
  {
    "user": { "login": "frosencrantz" },
    "labels": [ { "name": "wishlist" } ],
    "assignee": null,
    "comments": 2,
    "reactions": { "total_count": 0 },
    "number": 1327,
    "title": "[selection expansion] Expand current selection with a comma command that expands all matching selection."
  },
  {
    "user": { "login": "rduivenvoorde" },
    "labels": [ { "name": "wishlist" } ],
    "comments": 1, "reactions": { "total_count": 0 },
    "number": 1324,
    "title": "Make it possible to 'just open' a gpkg [sqlite] "
  },
  {
    "user": { "login": "anjakefala" },
    "labels": [ { "name": "bug" } ],
    "comments": 0,
    "reactions": { "total_count": 0 },
    "number": 1319,
    "title": "Input mysteriously stopped working"
  },
```


# loose format specification

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
  - key must be reasonable: no spaces or symbols that have meaning in JDOT

## globals

The container at the bottom of the parsing stack is where created objects (if it's a list) or key-values (if it's a dict) are stored into.
A token like `@globals` will clear out the parsing stack and push the named global container onto it.  There are only a few globals defined:

## `@options`

Set values at various keys in `@options` to control aspects the JDOT parser.

  - `.debug` (default `false`): set to `true` for extra debug output.
  - `.strict` (default `false`): set to `true` to error on unknown token (otherwise implicit conversion to string)

For example:
```
@options .strict true
```

## `@macros`

Add items to `@macros` to create new macro definitions.
The key is the macro name, and the value is the template to be matched or filled.
The template is given using the same JDOT syntax, so JDOT output can be copied verbatim into a macro.

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
     | '.' string-literal  // keys with whitespaces or other delimiters
     | '.'                 // matches any key

Variable := '?' id
          | '?'    // ignore contents

Macro := '(' id InnerList ')'
       | id     // instantiate macro without args

SectionName := '@' id  // can be 'options' or 'macros' or 'output'
         | '@'     // 'output'

Top := SectionName InnerDict
         | InnerList
         | InnerDict

Jdot := Top+
```

# Future ideas (not implemented yet)
  - multiple variables with the same `?varname` should match the same value, and should only be passed in the macro args once.
  - macro invocation with named arguments: `(foo .arg1 42 .arg2 "bar")`

# Copyright and License

Copyright 2022 Saul Pwanson

Licensed under the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0).
