# VEIM definitions

The recipes [VEIM](https://github.com/Cir0cuit/VEIM) uses to find each
distribution's current release, the catalog they make up, and the rules that
recognise their images by filename.

They live apart from VEIM so that a scraper a mirror has broken can be fixed
without a VEIM release. Every push to `main` that passes the tests is
published as a [release](https://github.com/Cir0cuit/VEIM-definitions/releases)
of this repository. VEIM 1.3.0 and later ask for the latest one at every
start, download it when it is newer than what they have (about 60 KB), check
it against the SHA-256 in its manifest, and use it from then on. Each VEIM
also ships a copy of the definitions it was built with, which it falls back on
offline or when a download cannot be used.

See [CONTRIBUTING.md](CONTRIBUTING.md) to fix or add a recipe.

## What a release holds

| Asset | Contents |
|---|---|
| `manifest-v1.json` | `api` (the contract version, VEIM's `src/core/recipe_base.py`), `version` (publish time, UTC, `YYYY.MM.DD.HHMMSS`), `sha256` of the archive, `min_app` (the oldest VEIM it runs in) |
| `definitions.zip` | `veim_definitions/`: Python source and PNG logos, nothing else |

VEIM refuses a manifest for another `api`, a release that needs a newer VEIM,
an archive that does not match its checksum or holds anything but source and
logos, and definitions that fail to import - and keeps what it had.

## Security

Definitions are code VEIM runs, so a release is as trustworthy as this
repository: VEIM downloads only from this repository's GitHub releases over
verified HTTPS, and only what the manifest's checksum matches. There is no
separate signature. Whoever can push to `main` here can ship code to every VEIM
at its next start - treat write access accordingly.

## License

MIT, as VEIM.
