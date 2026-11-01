from typing import List, Dict, Optional
from veim_definitions.common import DistroRecipe
from veim_definitions.recipes.fedora import FedoraRecipe, FedoraAtomicRecipe, FedoraSpinsRecipe, FedoraLabsRecipe
from veim_definitions.recipes.ubuntu import UbuntuRecipe
from veim_definitions.recipes.mint import MintRecipe
from veim_definitions.recipes.debian import DebianRecipe
from veim_definitions.recipes.arch import ArchRecipe
from veim_definitions.recipes.rolling import ManjaroRecipe, EndeavourRecipe, OmarchyRecipe
from veim_definitions.recipes.security import KaliRecipe, ParrotRecipe, CaineRecipe
from veim_definitions.recipes.modern_desktop import PopOSRecipe, KDENeonRecipe, ZorinRecipe, LinuxLiteRecipe
from veim_definitions.recipes.rescue import (
    ClonezillaRecipe, GPartedRecipe, RescuezillaRecipe, ShredOSRecipe,
    NetbootRecipe, SystemRescueRecipe, MemtestRecipe, SuperGrub2Recipe, HrmpfRecipe)
from veim_definitions.recipes.lightweight import PuppyRecipe, TinyCoreRecipe, AlpineRecipe
from veim_definitions.recipes.gaming import BazziteRecipe, GarudaRecipe, CachyOSRecipe, NobaraRecipe, PikaOSRecipe
from veim_definitions.recipes.community_desktop import OpenSUSERecipe, NixOSRecipe, ElementaryRecipe, TuxedoRecipe, MageiaRecipe
from veim_definitions.recipes.specialized import ArtixRecipe, SparkyRecipe, TailsRecipe, FydeOSRecipe, HackerOSRecipe, AlmaLinuxRecipe
from veim_definitions.recipes.debian_family import (
    MXLinuxRecipe, AntiXRecipe, DevuanRecipe, Q4OSRecipe, GrmlRecipe)
from veim_definitions.recipes.independent import VoidRecipe, GentooRecipe, SlackwareRecipe
from veim_definitions.recipes.enterprise import (
    RockyLinuxRecipe, ProxmoxRecipe, QubesRecipe, FreeBSDRecipe, IPFireRecipe, OracleLinuxRecipe,
    TalosRecipe, CentOSStreamRecipe, XCPngRecipe, OpenEulerRecipe)

# Order is the order the filter chips appear in.
CATEGORY_ORDER = [
    "Beginner Friendly",
    "General Purpose",
    "Rolling Release",
    "Enthusiast",
    "Gaming & Performance",
    "Security & Privacy",
    "Server & Enterprise",
    "Rescue & Diagnostics",
    "Lightweight",
]

# Catalog entries that were split after inventories had been written with the
# old key: (key, flavor) as recorded -> the key that flavor lives under now.
MOVED_FLAVORS = {
    ("fedora", "cinnamon"): "fedora_spins",
    ("fedora", "xfce"): "fedora_spins",
    ("fedora", "budgie"): "fedora_spins",
}

# Every entry in the catalog, and the filter chip it appears under.
CATALOG = {
    UbuntuRecipe: "Beginner Friendly",
    MintRecipe: "Beginner Friendly",
    ZorinRecipe: "Beginner Friendly",
    PopOSRecipe: "Beginner Friendly",
    ElementaryRecipe: "Beginner Friendly",
    TuxedoRecipe: "Beginner Friendly",
    FydeOSRecipe: "Beginner Friendly",
    LinuxLiteRecipe: "Beginner Friendly",

    FedoraRecipe: "General Purpose",
    FedoraAtomicRecipe: "General Purpose",
    FedoraSpinsRecipe: "General Purpose",
    FedoraLabsRecipe: "General Purpose",
    DebianRecipe: "General Purpose",
    OpenSUSERecipe: "General Purpose",
    KDENeonRecipe: "General Purpose",
    MageiaRecipe: "General Purpose",
    MXLinuxRecipe: "General Purpose",

    ArchRecipe: "Rolling Release",
    ManjaroRecipe: "Rolling Release",
    EndeavourRecipe: "Rolling Release",
    ArtixRecipe: "Rolling Release",
    OmarchyRecipe: "Rolling Release",

    GentooRecipe: "Enthusiast",
    SlackwareRecipe: "Enthusiast",
    NixOSRecipe: "Enthusiast",
    DevuanRecipe: "Enthusiast",
    VoidRecipe: "Enthusiast",

    BazziteRecipe: "Gaming & Performance",
    CachyOSRecipe: "Gaming & Performance",
    GarudaRecipe: "Gaming & Performance",
    NobaraRecipe: "Gaming & Performance",
    PikaOSRecipe: "Gaming & Performance",

    KaliRecipe: "Security & Privacy",
    ParrotRecipe: "Security & Privacy",
    TailsRecipe: "Security & Privacy",
    QubesRecipe: "Security & Privacy",
    HackerOSRecipe: "Security & Privacy",
    CaineRecipe: "Security & Privacy",

    AlmaLinuxRecipe: "Server & Enterprise",
    RockyLinuxRecipe: "Server & Enterprise",
    ProxmoxRecipe: "Server & Enterprise",
    CentOSStreamRecipe: "Server & Enterprise",
    OracleLinuxRecipe: "Server & Enterprise",
    OpenEulerRecipe: "Server & Enterprise",
    FreeBSDRecipe: "Server & Enterprise",
    XCPngRecipe: "Server & Enterprise",
    TalosRecipe: "Server & Enterprise",
    IPFireRecipe: "Server & Enterprise",

    SystemRescueRecipe: "Rescue & Diagnostics",
    ClonezillaRecipe: "Rescue & Diagnostics",
    GPartedRecipe: "Rescue & Diagnostics",
    RescuezillaRecipe: "Rescue & Diagnostics",
    GrmlRecipe: "Rescue & Diagnostics",
    MemtestRecipe: "Rescue & Diagnostics",
    ShredOSRecipe: "Rescue & Diagnostics",
    NetbootRecipe: "Rescue & Diagnostics",
    SuperGrub2Recipe: "Rescue & Diagnostics",
    HrmpfRecipe: "Rescue & Diagnostics",

    AntiXRecipe: "Lightweight",
    PuppyRecipe: "Lightweight",
    TinyCoreRecipe: "Lightweight",
    AlpineRecipe: "Lightweight",
    SparkyRecipe: "Lightweight",
    Q4OSRecipe: "Lightweight",
}


class RecipeRegistry:
    def __init__(self):
        self._recipes: Dict[str, DistroRecipe] = {}
        for cls, category in CATALOG.items():
            recipe = cls()
            recipe.category = category
            self._recipes[recipe.key] = recipe

    def get_recipe(self, key: str) -> Optional[DistroRecipe]:
        return self._recipes.get(key)

    def get_all_recipes(self) -> List[DistroRecipe]:
        return list(self._recipes.values())

    def get_categories(self) -> List[str]:
        """"All" plus every category that currently has at least one entry."""
        present = {r.category for r in self._recipes.values()}
        return ["All"] + [c for c in CATEGORY_ORDER if c in present]

registry = RecipeRegistry()
