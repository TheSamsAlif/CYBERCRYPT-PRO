"""
vigenere_cipher.py
==================

Layer 2 : Vigenere Cipher

An improvement over Caesar: instead of one fixed shift, every
character is shifted by a *different* amount, controlled by a
repeating keyword.

    Encryption : index = (index + key_index[i]) mod 128
    Decryption : index = (index - key_index[i]) mod 128

The keyword is used letter by letter and repeats cyclically.
Characters outside the alphabet pass through without consuming
a key position.
"""

from __future__ import annotations

from cybercrypt.core.alphabet import ALPHABET, ALPHABET_SIZE, INDEX


def _normalize_key(key: str) -> list:
    """
    Validate the keyword and keep only characters of the alphabet.

    Arguments:
        key : the raw keyword typed by the user.

    Returns:
        A list of alphabet characters forming the usable key.

    Raises:
        ValueError : if the key is empty or contains no usable characters.
    """
    if key is None or not str(key).strip():
        raise ValueError("Vigenere key must not be empty.")

    usable: list = [character for character in str(key) if character in INDEX]
    if not usable:
        raise ValueError("Vigenere key must contain letters or numbers.")
    return usable


def _apply(text: str, key: list, direction: int) -> str:
    """
    Core Vigenere operation shared by encrypt and decrypt.

    Arguments:
        text      : the input string to transform.
        key       : the normalized keyword (list of alphabet chars).
        direction : +1 for encryption, -1 for decryption.

    Returns:
        The transformed string.
    """
    result: list = []
    key_position: int = 0

    for character in text:
        if character in INDEX:
            # Shift by the current key character, then move to the next one.
            key_index = INDEX[key[key_position % len(key)]]
            new_index = (INDEX[character] + direction * key_index) % ALPHABET_SIZE
            result.append(ALPHABET[new_index])
            key_position += 1
        else:
            # Unknown characters pass through without using a key letter.
            result.append(character)
    return "".join(result)


def encrypt(plain_text: str, key: str) -> str:
    """
    Encrypt text with the Vigenere cipher.

    Arguments:
        plain_text : the original message.
        key        : the repeating keyword.

    Returns:
        The encrypted text.
    """
    return _apply(plain_text, _normalize_key(key), direction=+1)


def decrypt(cipher_text: str, key: str) -> str:
    """
    Decrypt text that was encrypted with the Vigenere cipher.

    Arguments:
        cipher_text : the encrypted message.
        key         : the same keyword that was used for encryption.

    Returns:
        The original text.
    """
    return _apply(cipher_text, _normalize_key(key), direction=-1)
