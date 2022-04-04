__all__ = ['JsomFormatter']


class JsomFormatter:
    def __init__(self, indent_str='  ', length_limit=80, value_limit=5):
        """
        Creates a JSOM formatter using the given configuration.
         - indent_str specifies which indentation character(s) to use.
         - length_limit specifies an approximate maximum number of characters
           that will be considered for emitting a group of tokens on a single
           line.
         - value_limit specifies the number of contained non-nested values
           that will be considered for emitting a group of tokens as a single
           line. Nested tokens will always only be inlined if there are no
           other values in the group.
        """
        self._indent_str = indent_str
        self._length_limit = length_limit
        self._value_limit = value_limit

    @staticmethod
    def _is_open(token):
        """Whether a token is some kind of open-parenthesis."""
        return isinstance(token, str) and token in set('({[<')

    @staticmethod
    def _is_close(token):
        """Whether a token is some kind of close-parenthesis."""
        return isinstance(token, str) and token in set(')}]>')

    @staticmethod
    def _is_key(token):
        """Whether a token is an object key."""
        return isinstance(token, str) and token.startswith('.')

    @staticmethod
    def _is_at(token):
        """Whether a token is an @ selection."""
        return isinstance(token, str) and token.startswith('@')

    @staticmethod
    def _is_spacing(token):
        """Whether a token is merely spacing."""
        return isinstance(token, str) and not token.strip()

    @staticmethod
    def _is_comment(token):
        """Whether a token is a comment."""
        return isinstance(token, str) and token.startswith('#')

    @staticmethod
    def _is_nested(token):
        """Whether a "token" is actually a list of tokens, used to aid
        formatting heuristics."""
        return not isinstance(token, str)

    @classmethod
    def _preprocess(cls, tokens) -> list:
        """
        Preprocess the given iterable of tokens:
         - Combine parenthesized groups of tokens into nested lists, such
           that open-paren tokens can only appear at the start of a list and
           close-parens can only appear at the end (unless they don't close
           anything that's currently open, in which case they're treated as a
           value token later on).
         - Remove any pre-existing whitespace (there probably won't be any if
           this is run on the output of the encoder).
        """
        root = []
        stack = [root]
        for token in tokens:

            # Strip whitespace.
            token = token.strip()
            if not token:
                continue

            # @ commands break out of everything, back to the root.
            if cls._is_at(token):
                del stack[1:]

            # Open-paren tokens create a new nested token list, starting with their
            # open-paren token and (unless interrupted by an @) ending with their
            # close-paren token.
            elif cls._is_open(token):
                sub_tokens = []
                stack[-1].append(sub_tokens)
                stack.append(sub_tokens)

            # Push the token to the current innermost list.
            stack[-1].append(token)

            # Close-paren tokens close the current list level.
            if cls._is_close(token) and len(stack) > 1:
                stack.pop()

        return root

    def _should_wrap(self, tokens: list) -> bool:
        """Whether the given list of nested tokens should be wrapped. This is
        a completely heuristic thing."""

        # Accumulate the approximate line length (not counting indentation)
        # we'd get if we don't wrap and the number of values in the token list.
        # When either reaches the limit, we decide to wrap.
        length = 0
        values = 0

        # Never wrap if there are no tokens.
        if not tokens:
            return False

        # Accumulate the length of the tokens before this one.
        for token in reversed(self._output):
            if '\n' in token:
                break
            length += len(token)

        # Accumulate length and value count of tokens
        for token in tokens:

            # Groups containing @ commands or comments must always be wrapped.
            if self._is_at(token) or self._is_comment(token):
                return True

            # Update value count. Nested groups increment the number of values
            # to the limit minus one, so a single nested group on its own is
            # okay, but combined with any amount of values it will be too long.
            if self._is_nested(token):
                values += self._value_limit - 1
            elif not self._is_key(token):
                values += 1
            if values >= self._value_limit:
                return True

            # Update approximate string length. This doesn't include nested
            # groups, but that's okay, because they will either always be
            # either the last token or we're wrapping anyway due to the value
            # count.
            if isinstance(token, str):
                length += len(token)
            length += 1
            if length >= self._length_limit:
                return True

        # Did not reach any of the limits, keep on single line.
        return False

    def _emit_newline(self, count=1):
        """Emit the given amount of newlines with the current indentation
        level. Overrides any previously emitted whitespace."""
        if self._output and self._is_spacing(self._output[-1]):
            self._output.pop()
        self._output.append(count*'\n' + self._indent*self._indent_str)

    def _emit_token(self, token):
        """Emit the given token, followed by the minimum amount of spacing
        needed to ensure that it won't combine with any other token that
        may be next. May change the whitespace between it and the previous
        token to make things look nicer."""

        # Handle non-nested tokens first.
        if not self._is_nested(token):
            self._output.append(token)
            self._output.append(' ')
            return
        tokens = token

        # Only the last token in a list can be a close.
        close_token = None
        if tokens and self._is_close(tokens[-1]):
            *tokens, close_token = tokens

        # Only the first token in a list can be an open.
        open_token = None
        if tokens and self._is_open(tokens[0]):
            open_token, *tokens = tokens

        # Determine whether we should wrap these tokens.
        wrap = self._should_wrap(tokens)

        # Emit open token, if any.
        if open_token is not None:
            self._emit_token(open_token)

        # Update indentation level.
        if wrap and open_token is not None:
            self._indent += 1

            # ( is used for macro invocations, where the first token is the
            # macro. It looks nicer if the macro name is on the same line.
            if tokens[0] != '(':
                self._emit_newline()

        # Handle nested tokens.
        in_comment = False
        for token in tokens:

            # Do a hard break all the way back to indentation level 0 before
            # any @ token.
            if self._is_at(token):
                self._indent = 0
                self._emit_newline(2)

            # Do a double newline before the first line comment in a sequence.
            if not in_comment and self._is_comment(token):
                self._emit_newline(2)

            # Emit the token.
            self._emit_token(token)

            # Always emit a newline after a line comment, since it's necessary
            # to terminate it.
            in_comment = self._is_comment(token)
            if in_comment:
                self._emit_newline()

            # Emit a newline after values if we're wrapping.
            if wrap and not self._is_key(token):
                self._emit_newline()

        # Update indentation level.
        if wrap and close_token is not None:
            if self._indent > 0:
                self._indent -= 1
            self._emit_newline()

        # Emit close token, if any.
        if close_token is not None:
            self._emit_token(close_token)

    def __call__(self, tokens) -> str:
        """Formats the given token stream."""
        self._output = []
        self._indent = 0
        self._emit_token(self._preprocess(tokens))
        self._indent = 0
        self._emit_newline()
        return ''.join(self._output)
