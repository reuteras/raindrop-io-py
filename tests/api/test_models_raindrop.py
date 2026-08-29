"""Test all the core methods of the Raindrop API."""

from unittest.mock import patch

from raindropiopy import API, Raindrop

raindrop = {
    "_id": 2000,
    # "collection": -1,
    "collection": {"$db": "", "$id": -1, "$ref": "collections"},
    "cover": "",
    "created": "2020-01-01T00:00:00.000Z",
    "creatorRef": 3000,
    "domain": "www.example.com",
    "excerpt": "excerpt text",
    "important": False,
    "lastUpdate": "2020-01-01T01:01:01Z",
    "link": "https://www.example.com/",
    "media": [],
    "pleaseParse": {"weight": 1},
    "sort": 3333333,
    "tags": ["abc", "def"],
    "title": "title",
    "type": "link",
    "user": {"$id": 3000, "$user": "users"},
}


def test_search() -> None:
    """Test search method."""
    api = API("dummy")
    with patch("raindropiopy.api.OAuth2Session.request") as m:
        m.return_value.json.return_value = {"items": [raindrop]}
        found = Raindrop._search_paged(api)
        assert found[0].id == 2000


def test_update() -> None:
    """Test ability to update an existing Raindrop."""
    api = API("dummy")
    with patch("raindropiopy.api.OAuth2Session.request") as m:
        m.return_value.json.return_value = {"item": raindrop}
        item = Raindrop.update(api, id=2000, link="https://example.com")
        assert item.id == 2000
