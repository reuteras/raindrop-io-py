"""Test all the methods in the Raindrop Collection API."""

import datetime
import json
from unittest.mock import patch, Mock

import pytest

from raindropiopy import AccessLevel, Collection, View

COLLECTION = {
    "_id": 1000,
    "access": {"draggable": True, "for": 10000, "level": 4, "root": False},
    "author": True,
    "count": 0,
    "cover": ["https://www.aRandomCover.org"],
    "created": "2020-01-01T00:00:00Z",
    "creatorRef": {"_id": 10000, "full_name": "user name"},
    "expanded": False,
    "last_update": "2020-01-02T00:00:00Z",
    "public": False,
    "sort": 3000,
    "title": "aCollectionTitle",
    "user": {"$db": "", "$id": 10000, "$ref": "users"},
    "view": "list",
    # Note: NO parent attribute here as this is a root level collection.
}


def test_get_root_collections(mock_api) -> None:
    """Test that we can get the "root" collections."""
    with patch("requests_oauthlib.OAuth2Session.get") as patched_request:
        mock_response = Mock(headers={"X-RateLimit-Limit": "100"})
        mock_response.json.return_value = {"items": [COLLECTION]}
        patched_request.return_value = mock_response

        # Test
        collections = Collection.get_root_collections(mock_api)

        # Confirm
        assert collections
        assert len(collections) == 1
        collection = collections[0]

        assert collection.id == 1000
        assert collection.access.level == AccessLevel.owner
        assert collection.access.draggable is True
        assert collection.collaborators == []
        assert collection.color is None
        assert collection.count == 0
        assert collection.cover == ["https://www.aRandomCover.org"]
        assert collection.created == datetime.datetime(
            2020,
            1,
            1,
            0,
            0,
            0,
            tzinfo=datetime.timezone.utc,
        )
        assert collection.expanded is False
        assert collection.last_update == datetime.datetime(
            2020,
            1,
            2,
            0,
            0,
            0,
            tzinfo=datetime.timezone.utc,
        )
        assert collection.parent is None  # This IS the parent collection, thus, it has no parent itself!
        assert collection.public is False
        assert collection.sort == 3000
        assert collection.title == "aCollectionTitle"
        assert collection.user.id == 10000
        assert collection.view == View.list


def test_parent_dereferencing() -> None:
    """Test that we can correct 'de-reference' a parent."""
    base = {
        "_id": 1001,
        "access": {"draggable": True, "for": 10000, "level": 4, "root": False},
        "author": True,
        "count": 0,
        "cover": ["https://www.aRandomCover.org"],
        "created": "2020-01-01T00:00:00Z",
        "creatorRef": {"_id": 10000, "full_name": "user name"},
        "expanded": False,
        "last_update": "2020-01-02T00:00:00Z",
        "public": False,
        "sort": 3000,
        "title": "aSubCollectionTitle",
        "user": {"$db": "", "$id": 10000, "$ref": "users"},
        "view": "list",
    }

    # Test
    Collection(**base)

    base["parent"] = {"$db": "", "$id": 1000, "$ref": "collections"}
    Collection(**base)

    base["parent"] = 123456789
    Collection(**base)

    with pytest.raises(AttributeError):
        base["parent"] = ["123456789", "ABC"]
        Collection(**base)

    # Example of collection taken from raindropiocli's state capability.
    state_json = """{
        "id": 39866550,
        "title": "SubCollection",
        "user": {
            "id": 1006974,
            "ref": null
        },
        "access": {
            "level": 4,
            "draggable": true
        },
        "collaborators": [],
        "color": null,
        "count": 0,
        "cover": [],
        "created": "2023-12-11T23:59:19.578000+00:00",
        "expanded": true,
        "last_update": null,
        "parent": 26109558,
        "public": false,
        "sort": -1,
        "view": "list",
        "other": {
            "creatorRef": {
                "_id": 1006974,
                "name": "MadHun",
                "email": ""
            },
            "lastAction": "2023-12-11T23:59:19.578Z",
            "lastUpdate": "2023-12-11T23:59:19.578Z",
            "slug": "sub-collection",
            "author": true
        }
    }"""
    Collection(**json.loads(state_json))


# FIXME: Need to figure out how to mock better, as is, this test is meaningless.
def tst_create(mock_api) -> None:
    """Test that we can create a new collection.

    FIXME: Add test for trying to create a collection that's already there.
    """
    with patch("requests_oauthlib.OAuth2Session.request") as patched_request:
        mock_response = Mock(headers={"X-RateLimit-Limit": "100"})
        mock_response.json.return_value = {"item": COLLECTION}
        patched_request.return_value = mock_response

        # Test
        c = Collection.create(mock_api, title="abcdef")

        # Confirm
        assert c.id == 1000
