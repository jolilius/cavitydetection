---
name: Use uv for Python packages
description: Always use uv instead of pip/pip3/python -m pip when installing Python packages
type: feedback
originSessionId: a0b2c6d3-4b55-462f-95a9-aba9c3d57c13
---
Always use `uv` (not `pip`, `pip3`, or `python3 -m pip`) when installing Python packages.

**Why:** User has uv installed and prefers it as their Python package manager.

**How to apply:** Any time a Python package needs to be installed, use `uv pip install` or `uv add` as appropriate.
