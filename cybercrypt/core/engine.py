"""
engine.py
=========

The multi-layer encryption engine. This is the heart of the
application: it applies the three layers in a fixed, documented
order and provides key generation.

ENCRYPTION ORDER (fixed):
    Plain Text
        -> 1. Caesar Cipher     (shift number)
        -> 2. Vigenere Cipher   (keyword)
        -> 3. Random XOR Layer  (numeric seed)
        -> Encrypted Text

DECRYPTION ORDER (exact reverse):
    Encrypted Text
        -> 3. Random XOR Layer  (same seed)
        -> 2. Vigenere Cipher   (same keyword)
        -> 1. Caesar Cipher     (same shift)
        -> Plain Text
"""

from __future__ import annotations

import random
import string

from cybercrypt.core import caesar_cipher, random_layer, vigenere_cipher


class EncryptionEngine:
    """
    Stateless multi-layer encryption engine.

    Every method is static and pure: same inputs, same outputs.
    This makes the engine trivial to test and explain.
    """

    # ------------------------------------------------------------------ #
    # Encryption                                                          #
    # ------------------------------------------------------------------ #

    @staticmethod
    def encrypt_text(plain_text: str, shift: int, vigenere_key: str, seed: int) -> str:
        """
        Apply the three layers in order: Caesar -> Vigenere -> Random.

        Arguments:
            plain_text   : the original message.
            shift        : Caesar shift (integer).
            vigenere_key : Vigenere keyword.
            seed         : numeric seed for the random XOR layer.

        Returns:
            The fully encrypted text.
        """
        layer_one = caesar_cipher.encrypt(plain_text, shift)          # layer 1
        layer_two = vigenere_cipher.encrypt(layer_one, vigenere_key)  # layer 2
        layer_three = random_layer.encrypt(layer_two, seed)           # layer 3
        return layer_three

    # ------------------------------------------------------------------ #
    # Decryption                                                          #
    # ------------------------------------------------------------------ #

    @staticmethod
    def decrypt_text(cipher_text: str, shift: int, vigenere_key: str, seed: int) -> str:
        """
        Remove the three layers in reverse order: Random -> Vigenere -> Caesar.

        Arguments:
            cipher_text  : the encrypted message.
            shift        : the same Caesar shift used for encryption.
            vigenere_key : the same keyword used for encryption.
            seed         : the same seed used for encryption.

        Returns:
            The recovered original text.
        """
        layer_three = random_layer.decrypt(cipher_text, seed)         # reverse layer 3
        layer_two = vigenere_cipher.decrypt(layer_three, vigenere_key)  # reverse layer 2
        layer_one = caesar_cipher.decrypt(layer_two, shift)           # reverse layer 1
        return layer_one

    # ------------------------------------------------------------------ #
    # Key generation                                                      #
    # ------------------------------------------------------------------ #

    @staticmethod
    def generate_random_keys() -> dict:
        """
        Create a fresh, random set of keys with one click.

        Returns:
            A dictionary: {"shift": int, "vigenere_key": str, "seed": int}
        """
        shift = random.randint(1, 25)
        vigenere_key = "".join(random.choices(string.ascii_uppercase, k=8))
        seed = random.randint(0, 999999)
        return {"shift": shift, "vigenere_key": vigenere_key, "seed": seed}
