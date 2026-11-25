# File: scripts/build_catalog.py
# Purpose: Validate data/sources.csv and generate the browsable Markdown
#          catalog pages in docs/ from it. The CSV is the single source of
#          truth. The Markdown pages are build output and are never edited
#          by hand.
# Created: 2026-11-25
#
# Usage:
#   python scripts/build_catalog.py           Validate the CSV and rewrite docs/.
#   python scripts/build_catalog.py --check   Validate the CSV and confirm docs/
#                                             is up to date. Writes nothing.
#
# Requires Python 3.9 or newer. Uses the standard library only.

from __future__ import annotations

import argparse
import csv
import datetime
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
SOURCES_CSV_PATH = REPOSITORY_ROOT / "data" / "sources.csv"
DOCS_DIRECTORY = REPOSITORY_ROOT / "docs"

# Creation date written into the header comment of every generated page.
# It is a constant, not today's date, so that rebuilding on a later day
# produces identical files and --check stays stable.
GENERATED_PAGES_CREATED_ON = "2026-11-25"

EXPECTED_COLUMNS = [
    "name",
    "field",
    "category",
    "description",
    "scale",
    "access",
    "license",
    "url",
    "status",
    "last_checked",
]

REQUIRED_COLUMNS = ["name", "field", "category", "description", "status"]

STATUS_LABELS = {
    "checked": "Checked",
    "partly-checked": "Partly checked",
    "not-checked": "Not checked",
}

# Each field becomes one page. The category order below is the reading order
# on that page: broad resources first, narrow or supporting ones last.
# A category that appears in the CSV but not here is still rendered, after
# the listed ones, in alphabetical order.
FIELD_PAGES = {
    "Linguistics": {
        "file_name": "linguistics.md",
        "title": "Linguistic lemma sources",
        "introduction": (
            "In linguistics a lemma is the dictionary form of a word. "
            "These sources list lemmas, map word forms to lemmas, or link "
            "lemmas across languages. The scope is English: every source "
            "is either English-only or multilingual with English included."
        ),
        "category_order": [
            "Multilingual lexical network",
            "Dictionary",
            "Wordnet and semantic lexicon",
            "Morphology and inflection",
            "Lemma and frequency list",
            "Lemmatizer tool",
            "Historical English",
            "Etymology",
            "Comparative word lists",
            "Terminology",
            "Standard and catalogue",
        ],
    },
    "Mathematics": {
        "file_name": "mathematics.md",
        "title": "Mathematical lemma sources",
        "introduction": (
            "In mathematics a lemma is a proven statement used as a step "
            "toward a larger result. These sources store lemmas and "
            "theorems, formally or informally, or help you search them."
        ),
        "category_order": [
            "Formal proof library",
            "Informal reference",
            "Object database",
            "Literature index",
            "Search engine",
            "Machine learning dataset",
        ],
    },
}


@dataclass(frozen=True)
class Source:
    """One row of data/sources.csv."""

    name: str
    field: str
    category: str
    description: str
    scale: str
    access: str
    license: str
    url: str
    status: str
    last_checked: str
    csv_line_number: int


def read_sources(csv_path: Path) -> tuple[list[Source], list[str]]:
    """Read the CSV and return its rows together with every validation error.

    All errors are collected instead of stopping at the first one, so a
    contributor can fix a batch of rows in a single pass.
    """
    validation_errors: list[str] = []
    sources: list[Source] = []

    if not csv_path.is_file():
        return [], [f"{csv_path} does not exist."]

    # utf-8-sig tolerates the byte order mark that spreadsheet programs add
    # when they save a CSV.
    with csv_path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames != EXPECTED_COLUMNS:
            return [], [
                "Unexpected header row. Expected columns, in order: "
                + ", ".join(EXPECTED_COLUMNS)
                + ". Found: "
                + ", ".join(reader.fieldnames or [])
            ]

        for row in reader:
            line_number = reader.line_num
            # A row with too many cells puts the extras under the None key.
            # A row with too few leaves None values.
            if None in row or any(value is None for value in row.values()):
                validation_errors.append(
                    f"Line {line_number}: wrong number of cells. "
                    f"Expected {len(EXPECTED_COLUMNS)}."
                )
                continue

            cleaned_row = {column: row[column].strip() for column in EXPECTED_COLUMNS}
            sources.append(Source(csv_line_number=line_number, **cleaned_row))

    validation_errors.extend(validate_sources(sources))
    return sources, validation_errors


def validate_sources(sources: list[Source]) -> list[str]:
    """Return a readable message for every rule a row breaks."""
    validation_errors: list[str] = []
    first_line_by_name: dict[str, int] = {}

    for source in sources:
        location = f"Line {source.csv_line_number} ({source.name or 'unnamed'})"

        for column in REQUIRED_COLUMNS:
            if not getattr(source, column):
                validation_errors.append(f"{location}: '{column}' is empty.")

        if source.field and source.field not in FIELD_PAGES:
            validation_errors.append(
                f"{location}: field '{source.field}' is not one of "
                + ", ".join(FIELD_PAGES)
                + "."
            )

        if source.status and source.status not in STATUS_LABELS:
            validation_errors.append(
                f"{location}: status '{source.status}' is not one of "
                + ", ".join(STATUS_LABELS)
                + "."
            )

        if source.url:
            parsed_url = urlparse(source.url)
            if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
                validation_errors.append(
                    f"{location}: url '{source.url}' is not a full http or https address."
                )

        # A row that claims to be checked must say when. A row that was never
        # checked must not carry a date, because the date would imply a check.
        if source.status in ("checked", "partly-checked"):
            if not is_iso_date(source.last_checked):
                validation_errors.append(
                    f"{location}: status '{source.status}' needs last_checked "
                    "as YYYY-MM-DD."
                )
        elif source.status == "not-checked" and source.last_checked:
            validation_errors.append(
                f"{location}: status 'not-checked' must leave last_checked empty."
            )

        # Names are compared without case so "WordNet" and "Wordnet" collide.
        normalized_name = source.name.casefold()
        if normalized_name in first_line_by_name:
            validation_errors.append(
                f"{location}: duplicate name. First used on line "
                f"{first_line_by_name[normalized_name]}."
            )
        elif normalized_name:
            first_line_by_name[normalized_name] = source.csv_line_number

    return validation_errors


def is_iso_date(text: str) -> bool:
    """Return True when text is a real calendar date written as YYYY-MM-DD."""
    try:
        datetime.date.fromisoformat(text)
    except ValueError:
        return False
    return len(text) == 10


def escape_table_cell(text: str) -> str:
    """Make text safe inside a Markdown table cell.

    A pipe would end the cell early, and a line break would end the row.
    """
    return text.replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def heading_anchor(heading_text: str) -> str:
    """Return the anchor GitHub generates for a heading.

    GitHub lowercases the heading, drops punctuation and turns each space
    into a hyphen. The category names in this catalog contain only letters
    and spaces, so this short rule matches GitHub exactly for them.
    """
    kept_characters = [
        character
        for character in heading_text.lower()
        if character.isalnum() or character in (" ", "-")
    ]
    return "".join(kept_characters).replace(" ", "-")


def ordered_categories(field_name: str, sources: list[Source]) -> list[str]:
    """Return the categories present for a field, in page reading order."""
    present_categories = {source.category for source in sources}
    configured_order = FIELD_PAGES[field_name]["category_order"]
    listed = [category for category in configured_order if category in present_categories]
    unlisted = sorted(present_categories - set(configured_order))
    return listed + unlisted


def render_source_row(source: Source) -> str:
    """Render one source as a Markdown table row."""
    escaped_name = escape_table_cell(source.name)
    name_cell = f"[{escaped_name}]({source.url})" if source.url else escaped_name
    cells = [
        name_cell,
        escape_table_cell(source.description),
        escape_table_cell(source.scale),
        escape_table_cell(source.access),
        escape_table_cell(source.license),
        STATUS_LABELS[source.status],
    ]
    return "| " + " | ".join(cells) + " |"


def render_field_page(field_name: str, sources: list[Source]) -> str:
    """Render the full Markdown page for one field."""
    page_settings = FIELD_PAGES[field_name]
    categories = ordered_categories(field_name, sources)

    lines = [
        f"<!-- File: docs/{page_settings['file_name']} -->",
        f"<!-- Purpose: Browsable list of {field_name.lower()} lemma sources, grouped by category. -->",
        "<!-- Generated by scripts/build_catalog.py from data/sources.csv. Do not edit by hand. -->",
        f"<!-- Created: {GENERATED_PAGES_CREATED_ON} -->",
        "",
        f"# {page_settings['title']}",
        "",
        page_settings["introduction"],
        "",
        f"{len(sources)} sources in {len(categories)} categories. "
        "The Status column says whether the details were confirmed against "
        "the source. See the [status key](README.md#status-key).",
        "",
        "## Categories",
        "",
    ]

    for category in categories:
        category_count = sum(1 for source in sources if source.category == category)
        lines.append(f"- [{category}](#{heading_anchor(category)}) ({category_count})")
    lines.append("")

    for category in categories:
        lines.extend(
            [
                f"## {category}",
                "",
                "| Source | What it holds | Scale | Access | License | Status |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )
        # Rows keep their CSV order inside a category. The CSV is ordered by
        # hand so that the most broadly useful sources come first.
        for source in sources:
            if source.category == category:
                lines.append(render_source_row(source))
        lines.extend(["", "[Back to categories](#categories)", ""])

    return "\n".join(lines).rstrip("\n") + "\n"


def render_index_page(sources: list[Source]) -> str:
    """Render docs/README.md: the entry point with counts and the status key."""
    status_counts = Counter(source.status for source in sources)

    lines = [
        "<!-- File: docs/README.md -->",
        "<!-- Purpose: Entry point to the generated catalog pages, with counts and the status key. -->",
        "<!-- Generated by scripts/build_catalog.py from data/sources.csv. Do not edit by hand. -->",
        f"<!-- Created: {GENERATED_PAGES_CREATED_ON} -->",
        "",
        "# Catalog",
        "",
        f"{len(sources)} sources in total.",
        "",
        "| Page | Sources | Categories |",
        "| --- | --- | --- |",
    ]

    for field_name, page_settings in FIELD_PAGES.items():
        field_sources = [source for source in sources if source.field == field_name]
        category_count = len({source.category for source in field_sources})
        lines.append(
            f"| [{page_settings['title']}]({page_settings['file_name']}) "
            f"| {len(field_sources)} | {category_count} |"
        )

    lines.extend(
        [
            "",
            "## Status key",
            "",
            "Every source has a status that says how far to trust its row.",
            "",
            "| Status | Meaning | Sources |",
            "| --- | --- | --- |",
            "| Checked | The scale figure or key facts were confirmed against "
            f"the source or a citable reference. | {status_counts['checked']} |",
            "| Partly checked | The source was confirmed to exist, but at least "
            f"one detail was not confirmed. | {status_counts['partly-checked']} |",
            "| Not checked | Recorded from prior knowledge. The link, license "
            f"and scale may be out of date. | {status_counts['not-checked']} |",
            "",
            "The date of each check is in the `last_checked` column of "
            "[data/sources.csv](../data/sources.csv).",
        ]
    )

    return "\n".join(lines) + "\n"


def build_pages(sources: list[Source]) -> dict[Path, str]:
    """Return every generated page as a mapping of file path to content."""
    pages: dict[Path, str] = {DOCS_DIRECTORY / "README.md": render_index_page(sources)}
    for field_name, page_settings in FIELD_PAGES.items():
        field_sources = [source for source in sources if source.field == field_name]
        pages[DOCS_DIRECTORY / page_settings["file_name"]] = render_field_page(
            field_name, field_sources
        )
    return pages


def main() -> int:
    argument_parser = argparse.ArgumentParser(
        description="Validate data/sources.csv and generate the Markdown catalog in docs/."
    )
    argument_parser.add_argument(
        "--check",
        action="store_true",
        help="Validate the CSV and confirm docs/ is up to date. Writes nothing.",
    )
    arguments = argument_parser.parse_args()

    sources, validation_errors = read_sources(SOURCES_CSV_PATH)
    if validation_errors:
        print(f"{len(validation_errors)} problem(s) in {SOURCES_CSV_PATH}:", file=sys.stderr)
        for validation_error in validation_errors:
            print(f"  {validation_error}", file=sys.stderr)
        return 1

    pages = build_pages(sources)

    if arguments.check:
        stale_pages = [
            page_path
            for page_path, expected_content in pages.items()
            if not page_path.is_file()
            or page_path.read_text(encoding="utf-8") != expected_content
        ]
        if stale_pages:
            print("These pages are out of date. Run the script without --check:", file=sys.stderr)
            for page_path in stale_pages:
                print(f"  {page_path.relative_to(REPOSITORY_ROOT)}", file=sys.stderr)
            return 1
        print(f"OK. {len(sources)} sources are valid and docs/ is up to date.")
        return 0

    DOCS_DIRECTORY.mkdir(parents=True, exist_ok=True)
    for page_path, page_content in pages.items():
        page_path.write_text(page_content, encoding="utf-8", newline="\n")
        print(f"Wrote {page_path.relative_to(REPOSITORY_ROOT)}")
    print(f"Done. {len(sources)} sources.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
