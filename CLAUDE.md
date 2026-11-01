@CONTRIBUTING.md

- Run tests with `python -m pytest` from this directory; VEIM's contract is found in the parent VEIM checkout, or set `VEIM_SRC`.
- Check one recipe against its live mirror: `python -m pytest -m network tests/test_recipes_live.py -k <key>`.
- A push to `main` publishes to every VEIM user at their next start. Run the suite first.
