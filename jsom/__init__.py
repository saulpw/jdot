import sys


from .jsom import deep_match
from .encoder import JsomEncoder
from .decoder import JsomDecoder
from .formatter import JsomFormatter


class JsomCoder(JsomEncoder, JsomDecoder):
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

    def encode(self, obj, formatter=None):
        if not formatter:
            formatter = JsomFormatter()
        return formatter(self.iterencode(obj))


JsomEncoderDecoder = JsomCoder


__all__ = [
    "JsomEncoderDecoder",
    "JsomDecoder",
    "JsomEncoder",
    "JsomCoder",
    "deep_match",
]
