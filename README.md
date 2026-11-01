# shift-jisx0213-decoder

Decodes Shift_JISX0213 byte sequences into Unicode strings, distinguishing the overlapping lead-byte ranges (0x87-0x8F) from standard Shift_JIS.

```python
from shift_jisx0213_decoder import decode, decode_one, DecodeError

# Decode a full byte string
text = decode(b"\x81\x40\x87\x40\xA1")
print(text)  # prints: \u3000\u4E00\uFF61

# Decode a single character at an offset
char, new_offset = decode_one(b"X\x81\x40", 1)
print(char, new_offset)  # prints: \u3000 3

try:
    decode(b"\x81\x20")
except DecodeError as e:
    print("Invalid sequence:", e)
```

## Why this library exists

Standard Shift_JIS and Shift_JISX0213 share lead-byte ranges 0x81-0x9F and 0xE0-0xFC, but Shift_JISX0213 also assigns two-byte characters to 0x87-0x8F. In standard Shift_JIS, 0x87-0x8F are not valid lead bytes (they are either undefined or part of single-byte half-width katakana). A naive decoder that treats 0x87-0x8F as single-byte half-width katakana will misinterpret Shift_JISX0213 text.

This library takes the interpretation that 0x87-0x8F are two-byte lead bytes only when followed by a valid trail byte (0x40-0x7E or 0x80-0xFC). If the trailing byte is not valid, the lead byte is treated as an invalid single byte and raises `DecodeError`. This one clear rule resolves the ambiguity without trying to support multiple historical encodings.

## Awkward edge

The mapping table is intentionally small and covers only a representative subset of JIS X 0213. Valid two-byte codes that are not in the table raise `DecodeError` with a message indicating the unmapped code. This is a deliberate trade-off: the library does not ship a full 10,000+ entry table, keeping the source compact and dependency-free. Users who need full coverage can extend `_TWO_BYTE_MAP` in `src/shift_jisx0213_decoder/core.py`.

## API

- `decode(data)`: Decode a bytes-like object and return a string. Raises `DecodeError` on invalid input.
- `decode_one(data, offset=0)`: Decode one character from `data` at `offset`, returning `(character, new_offset)`. Raises `DecodeError` on invalid input.
- `DecodeError`: Exception raised for all decoding errors.

All functions accept `bytes`, `bytearray`, or `memoryview` for `data`; `decode` rejects `str` with `TypeError`.
