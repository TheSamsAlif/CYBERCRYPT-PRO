"""
core package
============

Contains the three classical encryption layers plus the
multi-layer engine that combines them.

    alphabet.py      -> the shared 128-character alphabet
    caesar_cipher.py -> Layer 1 : Caesar Cipher
    vigenere_cipher.py -> Layer 2 : Vigenere Cipher
    random_layer.py  -> Layer 3 : Random XOR Layer
    engine.py        -> orchestrates encrypt / decrypt / key generation
"""
