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
      | List
      | Dict
      | PartialDict
      | Variable
      | Macro

Key := '.' id
     | '.' string-literal
     | '.'                // matches any key

KeyValue := Key Value
          | Key '='? KeyValue

Variable := '?' id
          | '?'    // ignore contents

List := '[' InnerList ']'
Dict := '{' InnerDict '}'
PartialDict := '<' InnerDict '>'

InnerList := Value*
InnerDict := KeyValue*

Macro := '(' id InnerList ')'
       | id     // instantiate macro without args

SectionName := '@' id  // can be 'options' or 'macros'
         | '@'     // 'output'

Top := SectionName InnerDict
         | InnerList
         | InnerDict

Jsom := Top+
