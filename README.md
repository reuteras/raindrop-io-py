# Raindrop-IO-py

[![version](https://img.shields.io/badge/python-3.10+-green)](https://www.python.org/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![license](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/PBorocz/raindrop-io-py/blob/trunk/LICENSE)

## Project Status

As of Spring 2024, I don't use RaindropIO anymore and thus will find it rather difficult to support this project. I'll keep up-to-date on CVE's of underlying packages for the foreseeable future but otherwise, FEEL FREE to fork and if you're interesting in taking ownership of the repo, feel free to contact me! (or open an issue)

Python wrapper for the API to the [Raindrop.io](https://raindrop.io) Bookmark Manager.

This fork is trimmed to the surface area used by [raindrop2rss](https://github.com/reuteras/raindrop2rss): searching and updating Raindrops, and getting/creating Collections.

## Background

I wanted to use an existing API for the Raindrop Bookmark Manager ([python-raindropio](https://github.com/atsuoishimoto/python-raindropio)) to perform some bulk operations through a simple command-line interface. However, the API was incomplete didn't seem actively supported anymore. Thus, this is a _fork_ and significant extension of [python-raindropio](https://github.com/atsuoishimoto/python-raindropio) (ht [Atsuo Ishimoto](https://github.com/atsuoishimoto)).

## Status

As the API layer is based on a fork of an existing package, it's reasonably stable.

## Requirements

Requires Python 3.10 or later (well, at least we're developing against 3.11.3).

## Install

```shell
[.venv] python -m pip install raindrop-io-py
```

## Setup

To use this package, you'll need two items:

- Somewhat obviously, your own account on [Raindrop](https://raindrop.io).

- However, to get API access to Raindrop, you'll need to create an `integration app` on [Raindrop](https://raindrop.io) site from which you can create API token(s).

To setup your `integration app`:

- Go to [<https://app.draindrop.api/settings/integrations>](https://app.raindrop.io/settings/integrations) and select `+ create new app`:

- Give it a descriptive name and then select the app you just created.

- Select `Create test token` and copy the token provided. Note that the basis for calling it a _test_ token is that it only gives you access to bookmarks within _your own account_.

- Save your token into your environment (we use python-dotenv so a simple .env/.envrc file containing your token should suffice), for example:

```shell
# If you use direnv or it's equivalent, place something like this in a .env file:
RAINDROP_TOKEN=01234567890-abcdefghf-aSample-API-Token-01234567890-abcdefghf

# Or for bash:
export RAINDROP_TOKEN=01234567890-abcdefghf-aSample-API-Token-01234567890-abcdefghf

# Or for fish:
set -gx RAINDROP_TOKEN 01234567890-abcdefghf-aSample-API-Token-01234567890-abcdefghf

# etc...
```

### API Examples

Here are a few examples of API usage.

#### Display All Root Collections and Unsorted Bookmarks

This example shows the intended usage of the API as a context-manager, from which any number of calls can be made:

```python
import os

from dotenv import load_dotenv

from raindropiopy import API, Collection, CollectionRef, Raindrop

load_dotenv()

with API(os.environ["RAINDROP_TOKEN"]) as api:

 print("Current Collections:")
 for collection in Collection.get_root_collections(api):
  print(collection.title)

 print("\nUnsorted Raindrop Bookmarks):")
 for item in Raindrop.search(api, collection=CollectionRef.Unsorted):
  print(item.title)
```

#### Create a New Raindrop Collection

```python
import os
import sys
from datetime import datetime
from getpass import getuser

from dotenv import load_dotenv

from raindropiopy import API, Collection

load_dotenv()

with API(os.environ["RAINDROP_TOKEN"]) as api:
 title = f"TEST Collection ({getuser()}@{datetime.now():%Y-%m-%dT%H:%M:%S})"
 print(f"Creating collection: '{title}'...", flush=True, end="")
 collection = Collection.create(api, title=title)
 print(f"Done, {collection.id=}.")
```

(after this has executed, go to your Raindrop.io environment (site or app) and you should see this collection available)

## Acknowledgments

[python-raindropio](https://github.com/atsuoishimoto/python-raindropio) from [Atsuo Ishimoto](https://github.com/atsuoishimoto).

## License

The project is licensed under the MIT License.

## Release History

See [CHANGELOG.md](CHANGELOG.md).
