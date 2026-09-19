"""Shared JSON reading for the CI checks.

The data files in this repo are a mix of UTF-8 and Windows-1251, so every read
tries UTF-8 first and falls back to cp1251 before declaring the file broken.
"""

import json

ENCODINGS = ("utf-8-sig", "cp1251")


def load_json(path):
    """Return (data, encoding) for path, or raise ValueError if it is not valid JSON."""
    with open(path, "rb") as fh:
        raw = fh.read()

    error = None
    for encoding in ENCODINGS:
        try:
            return json.loads(raw.decode(encoding)), encoding
        except (UnicodeDecodeError, ValueError) as exc:
            error = error or exc

    raise ValueError(error) from error
