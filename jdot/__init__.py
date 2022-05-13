import sys


from .jdot import deep_match
from .encoder import JdotEncoder
from .decoder import JdotDecoder
from .formatter import JdotFormatter


class JdotCoder(JdotEncoder, JdotDecoder):
    def __init__(self, **kwargs):
        super().__init__()
        self.toktuple = None
        self.options = dict(debug=False, strict=False)
        self.options.update(kwargs)
        self.macros = dict()
        self.globals = dict(macros=self.macros, options=self.options)

    def debug(self, *args, **kwargs):
        if self.options['debug']:
            print(*args, file=sys.stderr, **kwargs)


JdotEncoderDecoder = JdotCoder


__all__ = [
    "JdotEncoderDecoder",
    "JdotDecoder",
    "JdotEncoder",
    "JdotCoder",
    "JdotFormatter",
    "deep_match",
]
