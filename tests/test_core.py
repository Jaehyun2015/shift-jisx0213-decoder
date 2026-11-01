import unittest

from shift_jisx0213_decoder import decode, decode_one, DecodeError


class TestDecodeOne(unittest.TestCase):
    def test_ascii(self):
        self.assertEqual(decode_one(b"A", 0), ("A", 1))

    def test_halfwidth_katakana(self):
        self.assertEqual(decode_one(b"\xA1", 0), ("\uFF61", 1))
        self.assertEqual(decode_one(b"\xDF", 0), ("\uFF9F", 1))

    def test_two_byte_standard(self):
        self.assertEqual(decode_one(b"\x81\x40", 0), ("\u3000", 2))
        self.assertEqual(decode_one(b"\x81\x41", 0), ("\u3001", 2))

    def test_two_byte_extension(self):
        self.assertEqual(decode_one(b"\x87\x40", 0), ("\u4E00", 2))
        self.assertEqual(decode_one(b"\x8F\x41", 0), ("\u4E05", 2))

    def test_offset(self):
        self.assertEqual(decode_one(b"X\x81\x40", 1), ("\u3000", 3))

    def test_unmapped_two_byte(self):
        with self.assertRaises(DecodeError):
            decode_one(b"\x81\x43", 0)

    def test_truncated(self):
        with self.assertRaises(DecodeError):
            decode_one(b"\x81", 0)

    def test_invalid_trail(self):
        with self.assertRaises(DecodeError):
            decode_one(b"\x81\x20", 0)

    def test_invalid_lead(self):
        with self.assertRaises(DecodeError):
            decode_one(b"\x80", 0)
        with self.assertRaises(DecodeError):
            decode_one(b"\xFD", 0)

    def test_end_of_input(self):
        with self.assertRaises(DecodeError):
            decode_one(b"", 0)


class TestDecode(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(decode(b""), "")

    def test_mixed(self):
        data = b"A\xA1\x81\x40\x87\x40"
        self.assertEqual(decode(data), "A\uFF61\u3000\u4E00")

    def test_accepts_bytearray(self):
        self.assertEqual(decode(bytearray(b"\x81\x40")), "\u3000")

    def test_rejects_str(self):
        with self.assertRaises(TypeError):
            decode("\u3000")

    def test_error_propagates(self):
        with self.assertRaises(DecodeError):
            decode(b"\x81\x20")


if __name__ == "__main__":
    unittest.main()
