<!-- File: README.md -->
<!-- Purpose: Explain what this repository holds, how to use it and how to add to it. -->
<!-- Created: 2026-11-25 -->

# lemon

A catalog of databases, lexicons and tools for lemmas.

"Lemma" has two meanings, and this catalog covers both:

- **Linguistics:** the dictionary form of a word. *run* is the lemma of *runs*, *ran* and *running*.
- **Mathematics:** a proven statement used as a step toward a larger result.

No complete registry of lemma sources exists for either field. This catalog is broad, not exhaustive.

## Scope

- **Linguistic sources cover English.** A source belongs here if it is English-only or multilingual with English included. Old and Middle English count as English. Lexicons for a single other language are out of scope.
- **Mathematical sources have no language limit.**

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

Every row has been checked at least in part. A check covers the facts in the row, not every term of a license, so confirm the license on the source's own site before you depend on it. The current counts per status are in [docs/README.md](docs/README.md).

### How a row gets checked

- **Sources with a public repository:** the license file, the last commit date and any countable data were read from the repository itself.
- **Sources with a website:** the page at the row's address was read and compared with the row.
- **Sources whose site blocks automated readers:** the facts were taken from a search result or from the page as opened in a browser.

A row is `partly-checked` when the source exists but one detail, usually the license or the size, could not be confirmed this way.

## Layout

```
data/sources.csv           The catalog. Edit this file.
docs/README.md             Counts and status key. Generated.
docs/linguistics.md        Linguistic sources by category. Generated.
docs/mathematics.md        Mathematical sources by category. Generated.
scripts/build_catalog.py   Validates the CSV and generates docs/.
.github/workflows/check.yml  Runs the validation on every push.
LICENSE                    MIT license for the catalog and the script.
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
| `license` | No | License or terms. `Check site` or `Not stated` means it was not confirmed. |
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

4. Commit the CSV and the regenerated `docs/` pages together. The check that runs on every push fails if the pages were not rebuilt.

The script stops and lists every problem if a row is invalid: a missing required value, an unknown field or status, a malformed address, a missing check date or a duplicate name.

To confirm that everything is valid and up to date without writing files:

```
python scripts/build_catalog.py --check
```

The script needs Python 3.9 or newer and no extra packages.

## Known gaps

- Multilingual sources are listed for their English coverage only. Their quality for other languages was not assessed.
- Some rows are only partly checked, mostly because the source's site does not state a license on its home page.
- The Someya English lemma list has a confirmed address, but its size is not confirmed.
- Scale figures go out of date quickly. Each one names the version or date it applies to where that is known.

## License

The catalog, the generated pages and the script are released under the [MIT License](LICENSE). You may reuse them for any purpose if you keep the copyright notice.

This license covers the catalog only. Each source listed in it has its own license, shown in the License column.
