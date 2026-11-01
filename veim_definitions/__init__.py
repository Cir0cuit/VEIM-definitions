"""VEIM's definitions: the recipes that find each distribution's current
release, the catalog they make up, and the rules that recognise their images
by filename.

VEIM downloads these from this repository's releases at every start, so a
recipe fixed here reaches users without a VEIM release. API is the version of
VEIM's contract (src/core/recipe_base.py) this code is written against; VEIM
refuses definitions whose API is not its own.
"""
API = 1

# The oldest VEIM these definitions run in. Raised when a definition starts
# using something only a newer VEIM has; that VEIM and older keep what they
# have. The CI tests every change against this release of VEIM as well as main.
MIN_APP = "1.3.0"

# The standard library a definition may import, besides requests and urllib3.
# An installed VEIM holds only the modules it was built with, and builds since
# 1.3.0 bundle exactly these: one missing from a user's VEIM makes the whole
# download unusable for them. Append only, and raise MIN_APP to the first VEIM
# that bundles the addition.
STDLIB = (
    "abc", "base64", "calendar", "collections", "dataclasses", "datetime",
    "email.utils", "enum", "fnmatch", "functools", "hashlib", "html",
    "html.parser", "itertools", "json", "math", "operator", "posixpath", "re",
    "string", "textwrap", "time", "typing", "urllib.parse",
    "xml.etree.ElementTree",
)
