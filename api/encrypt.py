import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask, request, jsonify
from flask_cors import CORS
from cybercrypt.core import caesar_cipher, vigenere_cipher, random_layer

app = Flask(__name__)
CORS(app)


@app.route("/", methods=["POST"])
@app.route("/api/encrypt", methods=["POST"])
def encrypt():
    try:
        data = request.json or {}
        text = data.get("text", "")
        shift = int(data.get("shift", 0))
        key = data.get("key", "")
        seed = int(data.get("seed", 0))

        if not text:
            return jsonify({"error": "Empty input text"}), 400
        if not key:
            return jsonify({"error": "Empty Vigenere key"}), 400

        c_out = caesar_cipher.encrypt(text, shift)
        v_out = vigenere_cipher.encrypt(c_out, key)
        x_out = random_layer.encrypt(v_out, seed)

        return jsonify({
            "caesar": c_out,
            "vigenere": v_out,
            "xor": x_out,
            "result": x_out,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
