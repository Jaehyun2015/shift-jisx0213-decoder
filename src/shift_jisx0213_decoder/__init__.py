"""Shift JISX0213 decoder package.

Exports the public API: decode, decode_one, and DecodeError.
"""

from .core import decode, decode_one, DecodeError

__all__ = ["decode", "decode_one", "DecodeError"]
