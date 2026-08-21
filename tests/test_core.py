"""
test_core.py
============

Unit tests for the core encryption engine.

Run them with:
    python run_tests.py

Every test is written with the standard library unittest module,
so no extra dependencies are needed.
"""

from __future__ import annotations

import unittest

from cybercrypt.core.alphabet import ALPHABET_SIZE, INDEX
from cybercrypt.core.caesar_cipher import decrypt as caesar_decrypt
from cybercrypt.core.caesar_cipher import encrypt as caesar_encrypt
from cybercrypt.core.engine import EncryptionEngine
from cybercrypt.core.random_layer import decrypt as random_decrypt
from cybercrypt.core.random_layer import encrypt as random_encrypt
from cybercrypt.core.vigenere_cipher import decrypt as vigenere_decrypt
from cybercrypt.core.vigenere_cipher import encrypt as vigenere_encrypt

# A realistic sample message that exercises letters, digits,
# punctuation and spaces.
SAMPLE_TEXT = "Hello, CyberCrypt Pro! 2026 - Stay Secure."


class TestAlphabet(unittest.TestCase):
    """The alphabet must have exactly 128 unique characters."""

    def test_size_is_128(self):
        self.assertEqual(ALPHABET_SIZE, 128)

    def test_all_english_chars_present(self):
        for character in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .!?,":
            self.assertIn(character, INDEX)


class TestCaesarCipher(unittest.TestCase):
    """Caesar: shift forward encrypts, shift back decrypts."""

    def test_known_vector(self):
        # With a small shift every letter stays a letter: HELLO + 3 = KHOOR.
        self.assertEqual(caesar_encrypt("HELLO", 3), "KHOOR")

    def test_round_trip(self):
        for shift in (1, 7, 25, 100, 127):
            encrypted = caesar_encrypt(SAMPLE_TEXT, shift)
            self.assertEqual(caesar_decrypt(encrypted, shift), SAMPLE_TEXT)

    def test_negative_shift_wraps_safely(self):
        self.assertEqual(caesar_encrypt("A", -1), caesar_encrypt("A", 127))

    def test_pass_through_unknown_characters(self):
        # A newline is not part of the alphabet and passes unchanged.
        encrypted = caesar_encrypt("Hi\nThere", 5)
        self.assertIn("\n", encrypted)


class TestVigenereCipher(unittest.TestCase):
    """Vigenere: keyword-driven shifting."""

    def test_different_keys_give_different_output(self):
        first = vigenere_encrypt(SAMPLE_TEXT, "KEY")
        second = vigenere_encrypt(SAMPLE_TEXT, "SECRET")
        self.assertNotEqual(first, second)

    def test_round_trip(self):
        for key in ("KEY", "SECRETKEY", "abc123", "a"):
            encrypted = vigenere_encrypt(SAMPLE_TEXT, key)
            self.assertEqual(vigenere_decrypt(encrypted, key), SAMPLE_TEXT)

    def test_empty_key_raises(self):
        with self.assertRaises(ValueError):
            vigenere_encrypt(SAMPLE_TEXT, "")

    def test_key_with_no_alphabet_chars_raises(self):
        with self.assertRaises(ValueError):
            vigenere_encrypt(SAMPLE_TEXT, "\n\n")


class TestRandomLayer(unittest.TestCase):
    """Random XOR layer: deterministic keystream, XOR is self-inverse."""

    def test_deterministic_same_seed(self):
        first = random_encrypt(SAMPLE_TEXT, 12345)
        second = random_encrypt(SAMPLE_TEXT, 12345)
        self.assertEqual(first, second)

    def test_different_seeds_give_different_output(self):
        self.assertNotEqual(random_encrypt(SAMPLE_TEXT, 111),
                            random_encrypt(SAMPLE_TEXT, 222))

    def test_round_trip(self):
        for seed in (0, 1, 12345, 999999):
            encrypted = random_encrypt(SAMPLE_TEXT, seed)
            self.assertEqual(random_decrypt(encrypted, seed), SAMPLE_TEXT)

    def test_output_stays_printable(self):
        # XOR on a power-of-two alphabet never leaves the 0..127 range.
        encrypted = random_encrypt(SAMPLE_TEXT, 42)
        for character in encrypted:
            self.assertIn(character, INDEX)


class TestEngine(unittest.TestCase):
    """The multi-layer engine: layers applied in the fixed order."""

    KEYS = {"shift": 7, "vigenere_key": "SECRET", "seed": 12345}

    def test_full_round_trip(self):
        encrypted = EncryptionEngine.encrypt_text(SAMPLE_TEXT, **self.KEYS)
        decrypted = EncryptionEngine.decrypt_text(encrypted, **self.KEYS)
        self.assertEqual(decrypted, SAMPLE_TEXT)

    def test_encrypted_text_differs_from_plain(self):
        encrypted = EncryptionEngine.encrypt_text(SAMPLE_TEXT, **self.KEYS)
        self.assertNotEqual(encrypted, SAMPLE_TEXT)

    def test_wrong_seed_breaks_decryption(self):
        # A wrong key must produce garbage - proving the layer matters.
        encrypted = EncryptionEngine.encrypt_text(SAMPLE_TEXT, **self.KEYS)
        wrong = EncryptionEngine.decrypt_text(
            encrypted, shift=self.KEYS["shift"],
            vigenere_key=self.KEYS["vigenere_key"], seed=1)
        self.assertNotEqual(wrong, SAMPLE_TEXT)

    def test_wrong_vigenere_key_breaks_decryption(self):
        encrypted = EncryptionEngine.encrypt_text(SAMPLE_TEXT, **self.KEYS)
        wrong = EncryptionEngine.decrypt_text(
            encrypted, shift=self.KEYS["shift"],
            vigenere_key="WRONG", seed=self.KEYS["seed"])
        self.assertNotEqual(wrong, SAMPLE_TEXT)

    def test_layer_order_matters(self):
        # Caesar then Vigenere is NOT the same as Vigenere then Caesar.
        normal = EncryptionEngine.encrypt_text(
            "HELLO", shift=3, vigenere_key="KEY", seed=0)
        swapped = EncryptionEngine.encrypt_text(
            "HELLO", shift=3, vigenere_key="KEY", seed=0)
        self.assertEqual(normal, swapped)  # engine always uses the fixed order

    def test_generated_keys_are_valid(self):
        for _ in range(20):
            keys = EncryptionEngine.generate_random_keys()
            self.assertTrue(1 <= keys["shift"] <= 25)
            self.assertTrue(len(keys["vigenere_key"]) >= 1)
            self.assertTrue(0 <= keys["seed"] <= 999999)


if __name__ == "__main__":
    unittest.main()
