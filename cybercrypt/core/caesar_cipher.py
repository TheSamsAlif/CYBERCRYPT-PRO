"""
caesar_cipher.py
================

Layer 1 : Caesar Cipher

The oldest known substitution cipher. Every character is shifted
forward by a fixed number of positions in the alphabet.

    Encryption : index  = (index + shift) mod 128
    Decryption : index  = (index - shift) mod 128

Characters that do not belong to the alphabet (e.g. a newline)
pass through the cipher unchanged.
"""

from __future__ import annotations

from cybercrypt.core.alphabet import ALPHABET, ALPHABET_SIZE, INDEX


def _apply(text: str, shift: int) -> str:
    """
    Core shift operation used by both directions.

    Arguments:
        text  : the input string to transform.
        shift : signed offset (positive = encrypt, negative = decrypt).

    Returns:
        The transformed string.
    """
    result: list = []
    for character in text:
        if character in INDEX:
            # Move the index inside the alphabet, wrapping around.
            new_index = (INDEX[character] + shift) % ALPHABET_SIZE
            result.append(ALPHABET[new_index])
        else:
            # Unknown characters (e.g. newline) pass through unchanged.
            result.append(character)
    return "".join(result)


def encrypt(plain_text: str, shift: int) -> str:
    """
    Encrypt text with the Caesar cipher.

    Arguments:
        plain_text : the original message.
        shift      : how many positions to shift forward (any integer).

    Returns:
        The encrypted text.
    """
    return _apply(plain_text, shift % ALPHABET_SIZE)


def decrypt(cipher_text: str, shift: int) -> str:
    """
    Decrypt text that was encrypted with the Caesar cipher.

    Shifting backwards is the exact reverse of shifting forwards.

    Arguments:
        cipher_text : the encrypted message.
        shift       : the same shift that was used for encryption.

    Returns:
        The original text.
    """
    return _apply(cipher_text, -(shift % ALPHABET_SIZE))
