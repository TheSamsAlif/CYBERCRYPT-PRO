"""
alphabet.py
===========

Defines the shared 128-character alphabet used by all three layers.

WHY 128 characters (a power of two)?
    - Every ordinary text (letters, digits, punctuation, spaces) is covered.
    - All three ciphers work by moving an *index* inside the alphabet.
    - Because 128 is a power of two, a bitwise XOR of two indexes
      (0..127) always produces another valid index (0..127).
      This makes the Random XOR Layer perfectly reversible.
"""

from __future__ import annotations

# 95 printable ASCII characters: space (32) up to tilde (126).
# These cover every character a normal English message can contain.
PRINTABLE_ASCII: str = "".join(chr(code) for code in range(32, 127))

# 33 additional Latin-1 characters, added to reach exactly 128.
# They let the alphabet also handle accents such as e in "cafe".
LATIN_EXTRA: str = "ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßð"

# The final alphabet: exactly 128 characters.
ALPHABET: str = PRINTABLE_ASCII + LATIN_EXTRA

# How many characters the alphabet contains (always 128).
ALPHABET_SIZE: int = len(ALPHABET)

# Look-up table: character -> its index (0..127) inside ALPHABET.
# Used for fast mapping during encryption / decryption.
INDEX: dict = {character: index for index, character in enumerate(ALPHABET)}

# Safety check: if this assertion fails the whole design breaks.
assert ALPHABET_SIZE == 128, "Alphabet must contain exactly 128 characters"
assert len(set(ALPHABET)) == 128, "Alphabet must not contain duplicate characters"


def is_in_alphabet(character: str) -> bool:
    """Return True when a single character belongs to the alphabet."""
    return character in INDEX
