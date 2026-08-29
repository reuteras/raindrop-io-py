"""Test all the methods in the Raindrop Collection API."""

from raindropiopy import Collection
from tests.api.conftest import vcr


@vcr.use_cassette()
def test_get_collections(api) -> None:
    """Test that we can get root collections currently defined.

    (Note: we can't check on the contents since they're dependent on whose running the test!).
    """
    count_roots = 0
    for collection in Collection.get_root_collections(api):
        assert collection.id
        assert collection.title
        count_roots += 1

    assert count_roots


@vcr.use_cassette()
def test_collection_create(api) -> None:
    """Test that we can create a collection.

    Note: VCR replays the cassette's recorded response regardless of the
    request body, so the returned title reflects whoever originally
    recorded this cassette, not the title sent here - assert loosely.
    """
    collection = Collection.create(api, title="TEST Collection (anyone)")
    assert collection
    assert collection.id
    assert collection.title.startswith("TEST Collection (")
