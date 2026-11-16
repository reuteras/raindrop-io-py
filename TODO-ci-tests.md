# TODO: Run the test suite in CI

Status: open (created 2026-11-16)

## Problem

No workflow runs `pytest`. CI only runs super-linter, mypy, OSV-Scanner and CodeQL.

Running the suite without `RAINDROP_TOKEN` set gives 5 passed and 2 errors:

```text
ERROR tests/api/test_collections.py::test_get_collections - KeyError: 'RAINDROP_TOKEN'
ERROR tests/api/test_collections.py::test_collection_create - KeyError: 'RAINDROP_TOKEN'
```

The cause is the `api` fixture in `tests/conftest.py`:

```python
@pytest.fixture
def api():
    """Fixture to return a valid API instance."""
    yield API(os.environ["RAINDROP_TOKEN"])
```

Those tests replay VCR cassettes from `tests/api/cassettes/`. The `Authorization` header is filtered out of the
recordings, so replaying them should not need a real token.

## Decision: no hard-coded token in the workflow

Do not put `RAINDROP_TOKEN` in the workflow file. Fix the tests so they pass without it.

## Suggested fix

1. In `tests/conftest.py`, fall back to a placeholder when the variable is unset, for example
   `os.environ.get("RAINDROP_TOKEN", "dummy")`, or reuse the existing `mock_api` fixture.
2. Make sure VCR replays cassettes and never hits the network in CI, for example with `record_mode="none"`
   when `CI` is set. Otherwise a missing cassette quietly turns into a live API call.
3. Add a `test` job to `.github/workflows/linter.yml` next to the `mypy` job:
   - `actions/checkout` and `astral-sh/setup-uv`, pinned to the same SHAs as the other jobs
   - `uv sync --locked --dev`
   - `uv run pytest`
4. Check that `pytest` is in the dev group with a range (not `==`) so Dependabot keeps it updated.

## Done when

- `uv run pytest` passes with `RAINDROP_TOKEN` unset.
- The new `test` job is green on `main` and runs on Dependabot PRs.
- This file is deleted.
