"""Put VEIM's contract within reach.

Every definition imports src.core.recipe_base, which is VEIM's. Inside a VEIM
checkout this repository is the definitions/ submodule and VEIM is the parent
directory; anywhere else, point VEIM_SRC at a VEIM checkout.
"""
import os
import sys

VEIM = os.environ.get("VEIM_SRC") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.isfile(os.path.join(VEIM, "src", "core", "recipe_base.py")):
    raise SystemExit(f"No VEIM checkout at {VEIM}: clone VEIM with --recurse-submodules "
                     "and work in its definitions/ directory, or set VEIM_SRC")
# Appended, not prepended: this repository's own tests package comes first.
sys.path.append(VEIM)
