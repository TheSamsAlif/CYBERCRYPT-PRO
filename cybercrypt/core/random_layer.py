"""
random_layer.py
===============

Layer 3 : Random XOR Layer

A pseudo-random One-Time-Pad style layer.

1. A seed number (chosen by the user, or auto-generated) starts a
   Linear Congruential Generator (LCG) - a tiny, deterministic
   pseudo-random number generator.
2. For every character of the text the LCG produces one "keystream
   byte" between 0 and 127.
3. The character index is XOR-ed with that keystream byte:
       new_index = index XOR keystream_byte

WHY XOR is perfect here:
    - XOR is its own inverse: (a XOR b) XOR b == a.
    - The LCG is deterministic: the same seed always produces the
      same keystream.
    Therefore encryption and decryption use the SAME code.
"""

from __future__ import annotations

from cybercrypt.core.alphabet import ALPHABET, ALPHABET_SIZE, INDEX


class LcgRandom:
    """
    A minimal deterministic pseudo-random number generator (LCG).

    It uses the well-known ANSI C constants, which makes the
    keystream easy to explain and perfectly reproducible.
    """

    def __init__(self, seed: int, multiplier: int = 1103515245,
                 increment: int = 12345, modulus: int = 2 ** 31):
        # First step already applied so that a seed of zero still
        # produces a non-zero, healthy keystream.
        self.multiplier = multiplier
        self.increment = increment
        self.modulus = modulus
        self.state = (int(seed) * multiplier + increment) % modulus

    def next_value(self) -> int:
        """
        Produce the next pseudo-random value (0 .. modulus-1).
        """
        self.state = (self.state * self.multiplier + self.increment) % self.modulus
        return self.state


def _apply(text: str, seed: int) -> str:
    """
    Apply the random XOR layer. Encryption and decryption are
    identical because XOR is its own inverse.

    Arguments:
        text : the input string to transform.
        seed : the numeric key of the layer.

    Returns:
        The transformed string.
    """
    generator = LcgRandom(seed)

    result: list = []
    for character in text:
        if character in INDEX:
            # 128 is a power of two, so the XOR result always stays
            # inside the valid index range (0..127). No wrap needed.
            keystream_byte = generator.next_value() % ALPHABET_SIZE
            new_index = INDEX[character] ^ keystream_byte
            result.append(ALPHABET[new_index])
        else:
            # Unknown characters pass through unchanged.
            result.append(character)
    return "".join(result)


def encrypt(plain_text: str, seed: int) -> str:
    """
    Encrypt text with the random XOR layer.

    Arguments:
        plain_text : the original message.
        seed       : the numeric seed that controls the keystream.

    Returns:
        The encrypted text.
    """
    return _apply(plain_text, seed)


def decrypt(cipher_text: str, seed: int) -> str:
    """
    Decrypt text encrypted with the random XOR layer.

    Because XOR is self-inverse, this is simply the same operation
    as encryption - the keystream produced by the same seed restores
    the original message.

    Arguments:
        cipher_text : the encrypted message.
        seed        : the same seed that was used for encryption.

    Returns:
        The original text.
    """
    return _apply(cipher_text, seed)
