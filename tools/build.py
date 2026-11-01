"""Build what a definitions release publishes.

    python tools/build.py <version> <out-dir> [--after <previous-version>]

Writes <out-dir>/definitions.zip, holding veim_definitions/ as it is in the
working tree (source and logos only), and <out-dir>/manifest-v<API>.json,
which VEIM reads at every start. The version is the publish time in UTC,
YYYY.MM.DD.HHMMSS; with --after, a version not newer than the previous
release is refused, because VEIM would never take it.

The archive is the same bytes for the same tree, so a push that changes no
definition publishes nothing new.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGE = "veim_definitions"
VERSION = re.compile(r"\d{4}\.\d{2}\.\d{2}\.\d{6}")
FIXED_TIME = (2020, 1, 1, 0, 0, 0)


def package_constants() -> dict:
    """API, MIN_APP and STDLIB, read without importing the package (which
    would need VEIM)."""
    namespace: dict = {}
    with open(os.path.join(ROOT, PACKAGE, "__init__.py"), encoding="utf-8") as handle:
        exec(compile(handle.read(), "__init__.py", "exec"), namespace)
    return namespace


def members():
    """(path on disk, name in the archive) of every file that ships."""
    found = []
    for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, PACKAGE)):
        dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
        for name in filenames:
            if name.endswith((".py", ".png")):
                full = os.path.join(dirpath, name)
                found.append((full, os.path.relpath(full, ROOT).replace(os.sep, "/")))
    return sorted(found, key=lambda m: m[1])


def archive_bytes() -> bytes:
    import io
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as bundle:
        for full, name in members():
            info = zipfile.ZipInfo(name, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            with open(full, "rb") as handle:
                # Line endings as committed, whatever the checkout did to them.
                data = handle.read().replace(b"\r\n", b"\n") if name.endswith(".py") else handle.read()
            bundle.writestr(info, data)
    return buf.getvalue()


def version_key(version: str) -> tuple:
    return tuple(int(n) for n in re.findall(r"\d+", version))


def build(version: str, out: str, after: str = "") -> dict:
    if not VERSION.fullmatch(version):
        raise SystemExit(f"version {version!r} is not YYYY.MM.DD.HHMMSS")
    if after and version_key(version) <= version_key(after):
        raise SystemExit(f"version {version} is not newer than the last release, {after}")
    constants = package_constants()
    archive = archive_bytes()
    manifest = {"api": constants["API"], "version": version,
                "sha256": hashlib.sha256(archive).hexdigest(), "min_app": constants["MIN_APP"]}
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "definitions.zip"), "wb") as handle:
        handle.write(archive)
    with open(os.path.join(out, f"manifest-v{constants['API']}.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("version")
    parser.add_argument("out")
    parser.add_argument("--after", default="")
    args = parser.parse_args(argv)
    print(json.dumps(build(args.version, args.out, args.after)))


if __name__ == "__main__":
    sys.exit(main())
