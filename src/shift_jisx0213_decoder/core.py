"""Core decoder for Shift_JISX0213 byte sequences.

This module decodes Shift_JISX0213 (JIS X 0213) byte strings into Unicode
strings, distinguishing overlapping lead-byte ranges from standard Shift_JIS.

Shift_JISX0213 extends Shift_JIS with additional kanji in the lead-byte ranges
0x87-0x8F for two-byte characters. These ranges overlap with standard Shift_JIS
single-byte half-width katakana (0xA1-0xDF) and other two-byte leads. The decoder
uses the following rules:

- Bytes 0x00-0x7F: ASCII (single byte).
- Bytes 0xA1-0xDF: half-width katakana (single byte).
- Bytes 0x81-0x9F and 0xE0-0xFC: two-byte lead bytes (standard Shift_JIS plus
extensions).
- Bytes 0x87-0x8F: two-byte lead bytes for JIS X 0213 extensions, but only when
the following byte is a valid trail byte (0x40-0x7E or 0x80-0xFC). If the
trailing byte is not valid, the lead byte is treated as an invalid single byte.

Invalid sequences raise DecodeError. The decoder does not attempt to recover
from malformed input.

This implementation uses a fixed mapping table for the characters defined in
JIS X 0213. For brevity and to avoid external dependencies, the table covers a
representative subset of the standard; unmapped valid sequences raise
DecodeError with a message indicating the missing mapping.
"""

__all__ = ["decode", "decode_one", "DecodeError"]


class DecodeError(ValueError):
    """Raised when a byte sequence cannot be decoded."""


# Mapping from two-byte Shift_JISX0213 codes to Unicode characters.
# The table is intentionally small but includes entries for the overlapping
# lead-byte ranges 0x87-0x8F to demonstrate the distinction from Shift_JIS.
# Key is the two-byte code as an integer (lead << 8 | trail).
_TWO_BYTE_MAP = {
    # Standard Shift_JIS examples
    0x8140: "\u3000",  # ideographic space
    0x8141: "\u3001",  # ideographic comma
    0x8142: "\u3002",  # ideographic full stop
    0x8160: "\uFF5E",  # fullwidth tilde (JIS X 0208)
    0x8191: "\uFFE0",  # cent sign
    0x8192: "\uFFE1",  # pound sign
    0x81CA: "\uFFE2",  # not sign
    # JIS X 0213 extensions in 0x87-0x8F
    0x8740: "\u4E00",  # placeholder for a JIS X 0213 kanji
    0x8741: "\u4E01",
    0x8840: "\u4E02",
    0x8841: "\u4E03",
    0x8F40: "\u4E04",
    0x8F41: "\u4E05",
}

# Single-byte mappings for half-width katakana (0xA1-0xDF).
_HALFWIDTH_KATAKANA = {
    0xA1: "\uFF61",  # halfwidth ideographic full stop
    0xA2: "\uFF62",  # halfwidth opening corner bracket
    0xA3: "\uFF63",  # halfwidth closing corner bracket
    0xA4: "\uFF64",  # halfwidth ideographic comma
    0xA5: "\uFF65",  # halfwidth middle dot
    0xA6: "\uFF66",  # halfwidth katakana letter WO
    0xA7: "\uFF67",  # halfwidth katakana letter SMALL A
    0xA8: "\uFF68",  # halfwidth katakana letter SMALL I
    0xA9: "\uFF69",  # halfwidth katakana letter SMALL U
    0xAA: "\uFF6A",  # halfwidth katakana letter SMALL E
    0xAB: "\uFF6B",  # halfwidth katakana letter SMALL O
    0xAC: "\uFF6C",  # halfwidth katakana letter SMALL YA
    0xAD: "\uFF6D",  # halfwidth katakana letter SMALL YU
    0xAE: "\uFF6E",  # halfwidth katakana letter SMALL YO
    0xAF: "\uFF6F",  # halfwidth katakana letter SMALL TSU
    0xB0: "\uFF70",  # halfwidth katakana prolonged sound mark
    0xB1: "\uFF71",  # halfwidth katakana letter A
    0xB2: "\uFF72",  # halfwidth katakana letter I
    0xB3: "\uFF73",  # halfwidth katakana letter U
    0xB4: "\uFF74",  # halfwidth katakana letter E
    0xB5: "\uFF75",  # halfwidth katakana letter O
    0xB6: "\uFF76",  # halfwidth katakana letter KA
    0xB7: "\uFF77",  # halfwidth katakana letter KI
    0xB8: "\uFF78",  # halfwidth katakana letter KU
    0xB9: "\uFF79",  # halfwidth katakana letter KE
    0xBA: "\uFF7A",  # halfwidth katakana letter KO
    0xBB: "\uFF7B",  # halfwidth katakana letter SA
    0xBC: "\uFF7C",  # halfwidth katakana letter SHI
    0xBD: "\uFF7D",  # halfwidth katakana letter SU
    0xBE: "\uFF7E",  # halfwidth katakana letter SE
    0xBF: "\uFF7F",  # halfwidth katakana letter SO
    0xC0: "\uFF80",  # halfwidth katakana letter TA
    0xC1: "\uFF81",  # halfwidth katakana letter CHI
    0xC2: "\uFF82",  # halfwidth katakana letter TSU
    0xC3: "\uFF83",  # halfwidth katakana letter TE
    0xC4: "\uFF84",  # halfwidth katakana letter TO
    0xC5: "\uFF85",  # halfwidth katakana letter NA
    0xC6: "\uFF86",  # halfwidth katakana letter NI
    0xC7: "\uFF87",  # halfwidth katakana letter NU
    0xC8: "\uFF88",  # halfwidth katakana letter NE
    0xC9: "\uFF89",  # halfwidth katakana letter NO
    0xCA: "\uFF8A",  # halfwidth katakana letter HA
    0xCB: "\uFF8B",  # halfwidth katakana letter HI
    0xCC: "\uFF8C",  # halfwidth katakana letter FU
    0xCD: "\uFF8D",  # halfwidth katakana letter HE
    0xCE: "\uFF8E",  # halfwidth katakana letter HO
    0xCF: "\uFF8F",  # halfwidth katakana letter MA
    0xD0: "\uFF90",  # halfwidth katakana letter MI
    0xD1: "\uFF91",  # halfwidth katakana letter MU
    0xD2: "\uFF92",  # halfwidth katakana letter ME
    0xD3: "\uFF93",  # halfwidth katakana letter MO
    0xD4: "\uFF94",  # halfwidth katakana letter YA
    0xD5: "\uFF95",  # halfwidth katakana letter YU
    0xD6: "\uFF96",  # halfwidth katakana letter YO
    0xD7: "\uFF97",  # halfwidth katakana letter RA
    0xD8: "\uFF98",  # halfwidth katakana letter RI
    0xD9: "\uFF99",  # halfwidth katakana letter RU
    0xDA: "\uFF9A",  # halfwidth katakana letter RE
    0xDB: "\uFF9B",  # halfwidth katakana letter RO
    0xDC: "\uFF9C",  # halfwidth katakana letter WA
    0xDD: "\uFF9D",  # halfwidth katakana letter N
    0xDE: "\uFF9E",  # halfwidth katakana voiced sound mark
    0xDF: "\uFF9F",  # halfwidth katakana semi-voiced sound mark
}


def _is_valid_trail(byte):
    """Return True if byte is a valid second byte for a two-byte character."""
    return 0x40 <= byte <= 0x7E or 0x80 <= byte <= 0xFC


def decode_one(data, offset=0):
    """Decode a single character from data starting at offset.

    Returns a tuple (character, new_offset).

    Raises DecodeError if the bytes at offset do not form a valid character.
    """
    if offset >= len(data):
        raise DecodeError("unexpected end of input")
    b1 = data[offset]
    if b1 <= 0x7F:
        return chr(b1), offset + 1
    if 0xA1 <= b1 <= 0xDF:
        return _HALFWIDTH_KATAKANA[b1], offset + 1
    if 0x81 <= b1 <= 0x9F or 0xE0 <= b1 <= 0xFC:
        if offset + 1 >= len(data):
            raise DecodeError("truncated two-byte sequence")
        b2 = data[offset + 1]
        if not _is_valid_trail(b2):
            raise DecodeError(f"invalid trail byte 0x{b2:02X} after lead 0x{b1:02X}")
        code = (b1 << 8) | b2
        if code in _TWO_BYTE_MAP:
            return _TWO_BYTE_MAP[code], offset + 2
        raise DecodeError(f"unmapped two-byte code 0x{code:04X}")
    raise DecodeError(f"invalid lead byte 0x{b1:02X}")


def decode(data):
    """Decode a bytes-like object containing Shift_JISX0213 data.

    Returns the decoded string. Raises DecodeError on any invalid sequence.
    """
    if isinstance(data, str):
        raise TypeError("decode() expects a bytes-like object, not str")
    data = bytes(data)
    result = []
    offset = 0
    while offset < len(data):
        char, offset = decode_one(data, offset)
        result.append(char)
    return "".join(result)
