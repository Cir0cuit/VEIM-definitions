# Contributing

This repository is VEIM's `definitions/` submodule. Work in a VEIM checkout,
where the tests find VEIM's contract in the parent directory:

```bash
git clone --recurse-submodules https://github.com/Cir0cuit/VEIM
cd VEIM/definitions
git checkout main && git pull   # the submodule starts detached, at VEIM's pin
pip install requests pytest

pytest                  # every recipe against fixture pages, no network
pytest -m network       # every edition against its live mirror
pytest -m network tests/test_recipes_live.py -k <key>   # one recipe
```

Anywhere else, point `VEIM_SRC` at a VEIM checkout. Recipes import
everything from `veim_definitions.common`, which is the only module that
reaches into VEIM; `src/core/recipe_base.py` there is the contract.

## Publishing

Push to `main`. CI runs the suite against the oldest VEIM these definitions
declare they run in (`MIN_APP` in `veim_definitions/__init__.py`) and against
VEIM's `main`, then builds the archive with `tools/build.py` and publishes it
as a release, unless no definition changed. Every VEIM 1.3.0 or later picks it
up at its next start. There is nothing to release in VEIM.

Two limits come from the VEIMs already installed:

- Import only the standard library modules in `STDLIB`
  (`veim_definitions/__init__.py`), plus `requests` and `urllib3`. An installed
  VEIM holds only what it was built with. `tests/test_shipping.py` enforces
  this.
- Use only what VEIM `MIN_APP` has in `src/core/recipe_base.py`. If a
  definition needs something newer - a new contract field, a module added to
  `STDLIB` - raise `MIN_APP` to the first VEIM that has it; older VEIMs then
  keep the definitions they have.
- A change to the contract itself raises `API` in both repositories, and
  `MIN_APP` here to the first VEIM speaking the new `API`, in the same commit.
  Releases then carry `manifest-v<API>.json` for the new `API` only: VEIMs on
  the old one keep the last definitions they downloaded, for good.

The very first release had to wait for VEIM 1.3.0, the first VEIM with this
contract: CI tests against VEIM's tag `v<MIN_APP>`, so a push before that tag
exists fails, and publishing then takes `gh workflow run CI --ref main`.

To roll a release back, push a revert. VEIM also treats the latest release as
the authority, so deleting a bad release makes clients set it aside, but a
revert leaves a record.

## Adding a distribution

Subclass `DistroRecipe`, set `key`, `name`, `description` and `FLAVORS` (a
list of `FlavorInfo(id, name)`) and implement `fetch_download_info()`, then add
the class to `CATALOG` in `veim_definitions/registry.py` with its category.

`veim_definitions/common.py` has what recipes share: `hrefs()` and `table_rows()`
read a page, `version_key()` sorts versions, and `github_latest()` and
`sourceforge_rss()` read those two release feeds. Use them rather than a local
copy.

`fetch_download_info()` must `raise ScrapeError(self.name, reason)` when it
cannot determine a current release. Never return a hardcoded URL as a fallback;
the suite checks for it. Supply `sha256` when the project publishes one.

The version it reports is the one the user sees on the row and the one a later
check is compared against, so it has to be the release itself, found fresh each
time:

- Read the release listing and take the newest by numeric sort — not the
  first link on the page, not a folder pinned in the source.
- Never report a label. "latest", "current" and "stable" are not versions,
  and a row carrying one can never be told it is out of date.
- On a network error, raise. Falling back to an older release that happened
  to be reachable reports a stale version as current, which is worse than
  no answer; "No current release" on the row is the honest outcome.
- If the image's filename does not carry the version (Bazzite, Talos), rename
  it on the way down so that it does.

Then add a rule to `veim_definitions/iso_identity.py` that reads that filename back
into the same key, flavor id and version — exact pattern, whole name. That is
what lets an ISO a user copied onto the drive be recognised and adopted, and
`pytest -m network` fails when a recipe's filename and its rule disagree.
Names that never change between releases get no rule on purpose.

Then prove it picks the newest: add a `Case` for it to the matching
`tests/test_freshness_<group>.py`. The harness in `tests/freshness.py` serves
your fixture pages through a strict session - a URL the fixture lacks fails the
test instead of answering 404 - and runs the recipe on every page reversed and
shuffled, and again with the newest release's pages timing out, where it must
raise rather than fall back. Its docstring lists what a fixture has to hold: an
older release with working pages, a pre-release numbered above the newest, and
a pair of versions that sort differently as text than as numbers. A recipe that
only reads a pointer the project publishes (a GitHub "latest" release, a fixed
`latest.iso`) goes in `EXEMPT` with the reason instead. `test_freshness_meta.py`
fails until every catalog entry is in one or the other.

Every entry needs a logo. VEIM ships its logos rather than fetching them, so
a new entry gets one two ways: here, for the VEIMs already installed, and in
VEIM, for its next release. In the VEIM checkout add an entry to `ICON_URLS` in
`src/core/icons.py`, run `python tools/fetch_icons.py` and commit the PNG it
writes to `src/assets/icons/`; copy that PNG to `veim_definitions/icons/` here
as well. `tests/test_shipping.py` fails while an entry has neither.

VEIM's README lists the catalog; regenerate it there with
`python tools/readme_catalog.py --write` when VEIM next moves its
`definitions` submodule forward.
