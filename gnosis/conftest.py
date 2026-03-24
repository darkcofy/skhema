"""Conftest for gnosis tests — ensure gnosis/scripts is on sys.path first."""
import sys
import os

# Insert gnosis directory at the front of sys.path so 'scripts' resolves
# to gnosis/scripts rather than skhema/scripts (both are named 'scripts').
gnosis_root = os.path.dirname(os.path.abspath(__file__))
if gnosis_root not in sys.path:
    sys.path.insert(0, gnosis_root)
