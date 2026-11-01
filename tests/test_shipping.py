"""What has to hold for a release to work in the VEIMs already installed."""
import ast
import os
import sys

import pytest

from tools import build

PACKAGE_DIR = os.path.join(build.ROOT, build.PACKAGE)
CONSTANTS = build.package_constants()
VEIM = os.environ.get("VEIM_SRC") or os.path.dirname(build.ROOT)
# Third-party packages every VEIM ships, because VEIM itself uses them.
THIRD_PARTY = {"requests", "urllib3"}
# The contract, and the log. Only common.py reaches into VEIM.
CONTRACT = {"src.core", "src.core.recipe_base", "src.core.logger"}


def _modules():
    for full, name in build.members():
        if name.endswith(".py"):
            yield full, name


def _imports(path):
    with open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read(), path)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            yield node.module


@pytest.mark.parametrize("path,name", list(_modules()), ids=lambda v: v if "/" in str(v) else "")
def test_definitions_import_only_what_every_veim_bundles(path, name):
    """An installed VEIM holds only the modules it was built with: anything
    else makes the whole download fail to load for its users."""
    for module in _imports(path):
        top = module.split(".")[0]
        if module.startswith(build.PACKAGE) or top in THIRD_PARTY:
            continue
        if module in CONTRACT:
            assert name == f"{build.PACKAGE}/common.py", \
                f"{name} imports {module}: go through veim_definitions.common"
            continue
        assert module in CONSTANTS["STDLIB"], (
            f"{name} imports {module}, which is not in STDLIB: add it there and raise "
            "MIN_APP to the first VEIM that bundles it")


def test_the_stdlib_list_is_only_the_standard_library():
    for module in CONSTANTS["STDLIB"]:
        assert module.split(".")[0] in sys.stdlib_module_names, module


def test_a_release_unpacks_and_loads_in_veim(tmp_path):
    """The archive this repository publishes, through VEIM's own checks."""
    from src.core import definitions as veim

    manifest = build.build("2026.11.01.120000", str(tmp_path / "dist"))
    with open(tmp_path / "dist" / f"manifest-v{CONSTANTS['API']}.json", "rb") as handle:
        assert veim.parse_manifest(handle.read())["sha256"] == manifest["sha256"]
    with open(tmp_path / "dist" / "definitions.zip", "rb") as handle:
        veim.unpack(handle.read(), manifest["version"], str(tmp_path / "unpacked"))
    try:
        loaded = veim.import_definitions(str(tmp_path / "unpacked"), manifest["version"],
                                         veim.DOWNLOADED)
        assert loaded.registry.get_all_recipes()
    finally:
        veim._forget()
    assert CONSTANTS["API"] == veim.API


def test_the_archive_is_the_same_for_the_same_tree():
    """So a push that changes no definition publishes nothing new."""
    assert build.archive_bytes() == build.archive_bytes()


def test_every_entry_has_a_logo():
    """Shipped with VEIM, or here in veim_definitions/icons/ for an entry
    added since the oldest VEIM these definitions run in."""
    from veim_definitions.registry import registry
    shipped = os.path.join(VEIM, "src", "assets", "icons")
    ours = os.path.join(PACKAGE_DIR, "icons")
    for recipe in registry.get_all_recipes():
        assert any(os.path.isfile(os.path.join(d, f"{recipe.key}.png")) for d in (shipped, ours)), \
            f"{recipe.name} has no logo: add veim_definitions/icons/{recipe.key}.png"
