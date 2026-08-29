"""All data classes to interact with Raindrops API.

Raindrop.IO has a small set of core data entities (e.g. Raindrops aka bookmarks, Collections, Tags etc.). We
deliver the services provided by Raindrop.IO as a set of class-based methods on these various data entities.

For example, to search for raindrops, use Raindrop.search(...); a collection would be Collection.create(...) etc.

"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    NonNegativeInt,
    PositiveInt,
    field_validator,
    model_validator,
)

from .api import T_API  # ie. for typing only...

__all__ = [
    "Access",
    "AccessLevel",
    "Collection",
    "CollectionRef",
    "Raindrop",
    "RaindropType",
    "UserRef",
    "View",
]

# Base URL for Raindrop IO's API
URL = "https://api.raindrop.io/rest/v1/{path}"


################################################################################
# Utility methods
################################################################################
def _collect_other_attributes(cls, v):
    """Gather all non-recognised/unofficial non-empty attribute values into a single one."""
    skip_attrs = "_id"  # We don't need to store alias attributes again (pydantic will take care of)
    v["other"] = dict()
    for attr, value in v.items():
        if value and attr not in cls.model_fields and attr not in skip_attrs:
            v["other"][attr] = value
    return v


def _resolve_parent_reference(parent_reference: dict | int | None) -> int | None:
    """Convert a Raindrop.IO parent reference dict to just the respective ID of the parent collection.

    For a child collection that has a parent, the reference to the parent received from Raindrop.IO is:

    {"$id": 12345678, "$ref": 'collections'}.

    We don't need the $ref part (at least I don't believe so), so simply pull the $id key.
    """
    if parent_reference is None:
        return None
    elif isinstance(parent_reference, int):
        return parent_reference
    return parent_reference.get("$id")


################################################################################
# Enumerated types
################################################################################
class AccessLevel(enum.IntEnum):
    """Map the Access levels defined by Raindrop's API."""

    readonly = 1
    collaborator_read = 2
    collaborator_write = 3
    owner = 4


class CacheStatus(enum.Enum):
    """Represents the various states the cache of a Raindrop might be in."""

    ready = "ready"
    retry = "retry"
    failed = "failed"
    invalid_origin = "invalid-origin"
    invalid_timeout = "invalid-timeout"
    invalid_size = "invalid-size"


class View(enum.Enum):
    """Map the names of the views for Raindrop's API."""

    list = "list"
    simple = "simple"
    grid = "grid"
    masonry = "masonry"


class RaindropType(enum.Enum):
    """Map the types of Raindrop bookmarks possible (ie. what type of content they hold)."""

    link = "link"
    article = "article"
    image = "image"
    video = "video"
    document = "document"
    audio = "audio"


################################################################################
# Base Models
################################################################################
class CollectionRef(BaseModel):
    """Represents a **reference** to a Raindrop Collection (essentially a TypeVar of id: int).

    Note: We also instantiate three particular ``CollectionRefs`` associated with **System** Collections:
        *All*, *Trash* and *Unsorted*.

        System Collections always exist and can be explicitly used to query anywhere you'd use a Collection ID.

    """

    id: int | None = Field(None, alias="$id")


# We define the 3 "system" collections in the Raindrop environment:
CollectionRef.All = CollectionRef(
    **{"$id": 0},
)  # Note: "all" here does NOT include Trash.
CollectionRef.Trash = CollectionRef(**{"$id": -99})
CollectionRef.Unsorted = CollectionRef(**{"$id": -1})


class UserRef(BaseModel):
    """Represents a **reference** to `User` object."""

    id: int | None = Field(None, alias="$id")
    ref: str | None = Field(None, alias="$user")


class Access(BaseModel):
    """Represents Access control level of a `Collection`."""

    level: AccessLevel
    draggable: bool


class Collection(BaseModel):
    """Represents a Raindrop `Collection`, ie. a group of Raindrop Bookmarks.

    Attributes:
        id: The id of the collection (required)
        title: The name of the collection.
        user: The user who created the collection.
        access: Describes current Access levels to the collection (eg. ReadOnly, OwnerOnly etc.).
        collaborators: Populated with list of collaborating users iff collection is shared.
        color: Primary color of the collection cover.
        count: Count of Raindrops in the collection.
        cover: URL of the collection's cover.
        created: When the collection was created.
        expanded: Whether the collection's sub-collection are expanded (on the interface)
        last_update: When the collection was last updated.
        parent: Parent ID of this is a sub-collection.
        public: Are contents of this collection available to non-authenticated users?
        sort: The order of the collection. Defines the position of the collection against
          all other collections at the same level in the tree (only used for sub-collections?)
        view: Current view style of the collection, e.g. list, simple, grid etc.
        other: All other attributes received from Raindrop's API (see Warning below)

    Warning:
        Attributes in `other` are *NOT* OFFICIALLY SUPPORTED...use at your own risk!
    """

    id: int | None = Field(None, alias="_id")
    title: str
    user: UserRef

    access: Access | None = None
    collaborators: list[Any] | None = Field(default_factory=list)
    color: str | None = None
    count: NonNegativeInt
    cover: list[str] | None = Field(default_factory=list)
    created: datetime | None = None
    expanded: bool = False
    last_update: datetime | None = None
    parent: int | None = None  # Id of parent collection (if any)
    public: bool | None = None
    sort: int | None = None
    view: View | None = None

    # Per API Doc: "Our API response could contain other fields, not described above.
    # It's unsafe to use them in your integration! They could be removed or renamed at any time."
    other: dict[str, Any] = {}

    # Used to convert parent reference's of sub-collections to simply id's of the respective parent collection.
    @field_validator("parent", mode="before")
    @classmethod
    def _extract_parent_id(cls, v):
        """Convert parent reference to parent ID."""
        return _resolve_parent_reference(v)

    @model_validator(mode="before")
    @classmethod
    def _validator(cls, v):
        """Gather all non-recognised/unofficial attributes into a single attribute."""
        return _collect_other_attributes(cls, v)

    @classmethod
    def get_root_collections(cls, api: T_API) -> list[Collection]:
        """Get **root** Raindrop collections.

        Args:
            api: API Handle to use for the request.

        Returns:
            The (potentially empty) list of non-system, **top-level** Collections associated with the API's user.
        """
        ret = api.get(URL.format(path="collections"))
        items = ret.json()["items"]
        return [cls(**item) for item in items]

    @classmethod
    def create(
        cls,
        api: T_API,
        title: str,
        cover: list[str] | None = None,
        expanded: bool | None = None,
        parent: int | None = None,
        public: bool | None = None,
        sort: int | None = None,
        view: View | None = None,
    ) -> Collection:
        """Create a new Raindrop collection.

        Args:
            api: Required: API Handle to use for the request.

            cover: Optional, URL of collection's cover (as a list but only the first entry is used).

            expanded: Optional, flag for whether or not any of the collection's sub-collections are expanded.

            parent: Optional, Id of the collection's **parent** you want to create nested collections.

            public: Optional, flag for whether or not the collection should be publically available.

            sort: Optional, sort order for Raindrops created in this collection.

            title: Required: Title of the collection to be created.

            view: Optional, View associated with the default view to display Raindrops in this collection.

        Returns:
            ``Collection`` instance created.
        """
        args: dict[str, Any] = {}
        if cover is not None:
            args["cover"] = cover
        if expanded is not None:
            args["expanded"] = cover
        if parent is not None:
            args["parent"] = parent
        if public is not None:
            args["public"] = public
        if sort is not None:
            args["sort"] = sort
        if title is not None:
            args["title"] = title
        if view is not None:
            args["view"] = view

        url = URL.format(path="collection")
        item = api.post(url, json=args).json()["item"]
        return cls(**item)

    @classmethod
    def get_or_create(cls, api: T_API, title: str) -> Collection:
        """Get a Raindrop collection based on it's **title**, if it doesn't exist, create it.

        Args:
            api: API Handle to use for the request.

            title: Title of the collection.

        Returns:
            Collection with the specified collection title if it already exists or newly created
              collection if it doesn't.
        """
        for collection in Collection.get_root_collections(api):
            if title.casefold() == collection.title.casefold():
                return collection

        # Doesn't exist, create it!
        return Collection.create(api, title=title)


class File(BaseModel):
    """Represents the attributes associated with a file within a document-based Raindrop."""

    name: str
    size: PositiveInt
    type: str


class Cache(BaseModel):
    """Represents the cache information of Raindrop."""

    # Per issue #5, we can't rely on Raindrop to always return a non-zero value for `size`, thus
    # instead of `PositiveInt`, we use `int`.
    status: CacheStatus
    size: int | None = None
    created: datetime | None = None


class Raindrop(BaseModel):
    """Core class of a Raindrop bookmark 'item'.

    A Raindrop/bookmark can be of two major types:

    - A **link-based** one, ie. a standard "bookmark" that points to a specific URL (in the link attribute).

    - A **file-based** one, into which a file (of the approved type) is uploaded and stored on the
      Raindrop service (details of which are in the file attribute).

    Attributes:
        id: The id of the Raindrop.
        collection: Collection (or CollectionRef) this Raindrop currently resides in.
        cover: The URL of the Raindrop's cover.
        created: The creation datetime of the Raindrop.
        domain: Hostname of a link, ie. if a Raindrop has link: `https://www.google.com?search=SomeThing`,
          domain is `www.google.com`.
        excerpt: Description associated with this Raindrop (maximum length: 10k!)
        last_update: When this Raindrop was last updated.
        link: For a link-based Raindrop, the full URL.
        media: Covers list.
        tags: A list of Tags associated with the Raindrop.
        title: The title of the Raindrop (maximum length: 1k).
        type: The type of the Raindrop, e.g. *link*, *document* (I haven't tested other types)
        user: The user who created the Raindrop.
        broken: True of the link associated with the Raindrop is not reachable anymore.
        cache: Details of the permanent cache associated with the Raindrop.
        file: Details of the file associated with a **file** based Raindrop.
        important: True if this Raindrop is marked as a **Favorite**.
        other: All other attributes received from Raindrop's API.

    Warning:
        Attributes in `other` are NOT OFFICIALLY SUPPORTED!.
    """

    # "Main" fields (per https://developer.raindrop.io/v1/raindrops)
    id: int | None = Field(None, alias="_id")
    collection: Collection | CollectionRef = CollectionRef.Unsorted
    cover: str | None = None
    created: datetime | None = None
    domain: str | None = None
    excerpt: str | None = None  # aka 'Description' on the Raindrop UI.
    file: File | None = None
    last_update: datetime | None = Field(None, alias="lastUpdate")
    link: HttpUrl | None = None
    media: list[dict[str, Any]] | None = None
    tags: list[str] | None = None
    title: str | None = None
    type: RaindropType | None = None
    user: UserRef | None = None

    # "Other" fields:
    broken: bool | None = None
    cache: Cache | None = None
    important: bool | None = None  # aka marked as Favorite.

    # Per API Doc: "Our API response could contain other fields, not described above.
    # It's unsafe to use them in your integration! They could be removed or renamed at any time."
    other: dict[str, Any] = {}

    @model_validator(mode="before")
    @classmethod
    def _validator(cls, v):
        """Gather all non-recognised/unofficial attributes into a single attribute."""
        return _collect_other_attributes(cls, v)

    @classmethod
    def update(
        cls,
        api: T_API,
        id: int,
        collection: (Collection | CollectionRef, int) | None = None,
        cover: str | None = None,
        excerpt: str | None = None,
        important: bool | None = None,
        link: str | None = None,
        media: list[dict[str, Any]] | None = None,
        order: int | None = None,
        please_parse: bool | None = False,
        tags: list[str] | None = None,
        title: str | None = None,
    ) -> Raindrop:
        """Update an existing Raindrop bookmark, setting any of the attribute values provided.

        Args:
            api: API Handle to use for the request.

            id: Required id of Raindrop to be updated.

            collection: Optional, Collection (or CollectionRef) to move this Raindrop "into". If not specified,
                Raindrop will remain in the same collection as it was.

            cover: Optional, new URL to set as the Raindrop's "cover".

            excerpt: Optional, new long description for the Raindrop. Maximum length is 10,000 characters.

            important: Optional, Flag to indicate if this Raindrop should be considered important nee a favorite.

            link: Required, New URL to associate with this Raindrop.

            media: Optional, Updated list of media dictionaries (consult RaindropIO's API for somewhat more information.

            order: Optional, Change order of Raindrop in respective collection.

            please_parse: Optional, Flag that asks API to automatically parse metadata in the background
                (not exactly sure which this implies, message me if you know! ;-)

            tags: Optional, New list of tags to associate with this Raindrop.

            title: Optional, New title for this Raindrop.

        Returns:
            ``Raindrop`` instance that was updated.
        """
        # Setup the args that will be passed to the underlying Raindrop API
        args: dict[str, Any] = {}

        if please_parse:
            args["please_parse"] = {}

        for attr in [
            "cover",
            "excerpt",
            "important",
            "link",
            "media",
            "order",
            "tags",
            "title",
        ]:
            if (value := locals().get(attr)) is not None:
                args[attr] = value

        if collection is not None:
            # <collection> arg could be **either** an actual collection
            # or simply an int collection "id" already, handle either:
            if isinstance(collection, Collection | CollectionRef):
                args["collection"] = collection.id
            else:
                args["collection"] = collection

        url = URL.format(path=f"raindrop/{id}")
        item = api.put(url, json=args).json()["item"]
        return cls(**item)

    @classmethod
    def _search_paged(
        cls,
        api: T_API,
        collection: CollectionRef = CollectionRef.All,
        search: str | None = None,
        page: int = 0,
        perpage: int = 50,
    ) -> list[Raindrop]:
        """Lower-level search for bookmarks on a "paged" basis.

        Raindrop's search API works on a "paged" basis. This method implements the underlying
        search reflecting paging (while the primary ``search`` method below hides it
        completely).
        """
        params = {"perpage": perpage, "page": page}
        if search:
            params["search"] = search
        url = URL.format(path=f"raindrops/{collection.id}")
        results = api.get(url, params=params).json()
        return [cls(**item) for item in results["items"]]

    @classmethod
    def search(
        cls,
        api: T_API,
        collection: Collection | CollectionRef = CollectionRef.All,
        search: str | None = None,
    ) -> list[Raindrop]:
        """Search for Raindrops.

        Args:
            api: API Handle to use for the request.

            collection: Optional, ``Collection`` (or ``CollectionRef``) to search over.
                Defaults to ``CollectionRef.All``.

            search: Optional, search string to search Raindrops for (see
                `Raindrop.io Search Help <https://help.raindrop.io/using-search#operators>`_ for more information.

        Returns:
            A (potentially empty) list of Raindrops that match the search criteria provided.
        """
        page = 0
        results = list()
        while raindrops := Raindrop._search_paged(
            api,
            collection,
            page=page,
            search=search,
        ):
            results.extend(raindrops)
            page += 1
        return results
