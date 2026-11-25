<!-- File: README.md -->
<!-- Purpose: Explain what this repository holds, how to use it and how to add to it. -->
<!-- Created: 2026-11-25 -->

# lemon

A catalog of databases, lexicons and tools for lemmas.

"Lemma" has two meanings, and this catalog covers both:

- **Linguistics:** the dictionary form of a word. *run* is the lemma of *runs*, *ran* and *running*.
- **Mathematics:** a proven statement used as a step toward a larger result.

No complete registry of lemma sources exists for either field. This catalog is broad, not exhaustive.

## Start here

| I want to | Go to |
| --- | --- |
| Browse linguistic sources | [docs/linguistics.md](docs/linguistics.md) |
| Browse mathematical sources | [docs/mathematics.md](docs/mathematics.md) |
| See counts and the status key | [docs/README.md](docs/README.md) |
| Filter, sort or load the data in code | [data/sources.csv](data/sources.csv) |
| Add or correct a source | [Add or correct a source](#add-or-correct-a-source) |

## How far to trust a row

Every source has a status.

| Status | Meaning |
| --- | --- |
| Checked | The scale figure or key facts were confirmed against the source or a citable reference. |
| Partly checked | The source was confirmed to exist, but at least one detail was not confirmed. |
| Not checked | Recorded from prior knowledge. The link, license and scale may be out of date. |

Most rows are not checked yet. Confirm the license on the source's own site before you depend on it. The current counts per status are in [docs/README.md](docs/README.md).

## Layout

```
data/sources.csv           The catalog. Edit this file.
docs/README.md             Counts and status key. Generated.
docs/linguistics.md        Linguistic sources by category. Generated.
docs/mathematics.md        Mathematical sources by category. Generated.
scripts/build_catalog.py   Validates the CSV and generates docs/.
```

`data/sources.csv` is the single source of truth. Everything in `docs/` is generated from it, so do not edit those pages by hand.

## The data

`data/sources.csv` is UTF-8 with one source per row. It has no comment header, because a comment line would break CSV readers.

| Column | Required | Content |
| --- | --- | --- |
| `name` | Yes | Name of the source. Must be unique. |
| `field` | Yes | `Linguistics` or `Mathematics`. |
| `category` | Yes | Group within the field, for example `Dictionary` or `Formal proof library`. |
| `description` | Yes | What the source holds, in one or two plain sentences. |
| `scale` | No | Size or coverage, with the version or date it applies to. |
| `access` | No | How to get the data: web, API, download, subscription. |
| `license` | No | License or terms. `Check site` means it was not confirmed. |
| `url` | No | Full `http` or `https` address. Empty when no address was confirmed. |
| `status` | Yes | `checked`, `partly-checked` or `not-checked`. |
| `last_checked` | With a check | Date of the check as `YYYY-MM-DD`. Empty for `not-checked`. |

Load it in Python:

```python
import csv

with open("data/sources.csv", encoding="utf-8", newline="") as csv_file:
    sources = list(csv.DictReader(csv_file))

checked_formal_libraries = [
    source["name"]
    for source in sources
    if source["category"] == "Formal proof library" and source["status"] == "checked"
]
```

## Add or correct a source

1. Edit `data/sources.csv`. Put a new row next to related sources in the same category. Rows keep their CSV order on the generated pages.
2. Set `status` honestly. Use `checked` only when you confirmed the facts against the source, and fill in `last_checked`.
3. Rebuild the pages:

   ```
   python scripts/build_catalog.py
   ```

4. Commit the CSV and the regenerated `docs/` pages together.

The script stops and lists every problem if a row is invalid: a missing required value, an unknown field or status, a malformed address, a missing check date or a duplicate name.

To confirm that everything is valid and up to date without writing files:

```
python scripts/build_catalog.py --check
```

The script needs Python 3.9 or newer and no extra packages.

## Known gaps

- Coverage of single-language lexicons is uneven. European languages are better covered than African, Southeast Asian and Indigenous American languages.
- One row, the BNC-based English lemma list, has no located source.
- Scale figures go out of date quickly. Each one names the version or date it applies to where that is known.
