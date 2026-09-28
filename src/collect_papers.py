import csv
import os
import re
from datetime import date, timedelta

import requests
import yaml
from dotenv import load_dotenv

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

OPENALEX_URL = "https://api.openalex.org/works"

INPUT_CONFIG = "config/interests.yaml"
OUTPUT_FILE = "data/candidate_papers.csv"
DAYS_TO_SEARCH = 7

end_date = date.today()

start_date = end_date - timedelta(
    days=DAYS_TO_SEARCH
)

# ---------------------------------------------------------
# Load API key
# ---------------------------------------------------------

load_dotenv()

api_key = os.getenv("OPENALEX_API_KEY")

if api_key is None:
    raise ValueError(
        "OPENALEX_API_KEY was not found. "
        "Check that it exists in your .env file."
    )


# ---------------------------------------------------------
# Load research interests
# ---------------------------------------------------------

with open(INPUT_CONFIG, "r", encoding="utf-8") as file:
    interests = yaml.safe_load(file)

watch_terms = interests["watch_terms"]


# ---------------------------------------------------------
# OpenAlex search
# ---------------------------------------------------------

def search_openalex(search_term):
    """
    Search OpenAlex for papers matching a search term.

    Currently retrieves papers published between {start_date} and {end_date}.
    """
    date_filter = (
    f"from_publication_date:{start_date},"
    f"to_publication_date:{end_date}"
    )
    params = {
        "search": search_term,
        "filter": date_filter,
        "per_page": 10,
        "api_key": api_key,
    }

    response = requests.get(
        OPENALEX_URL,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    return data["results"]


# ---------------------------------------------------------
# Metadata extraction functions
# ---------------------------------------------------------

def get_authors(paper):
    """
    Extract author names from an OpenAlex paper record.
    """

    authors = []

    for authorship in paper.get("authorships", []):
        author = authorship.get("author", {})
        name = author.get("display_name")

        if name:
            authors.append(name)

    return "; ".join(authors)


def get_source(paper):
    """
    Extract the primary source or journal name.
    """

    primary_location = paper.get("primary_location")

    if not primary_location:
        return None

    source = primary_location.get("source")

    if not source:
        return None

    return source.get("display_name")


def reconstruct_abstract(paper):
    """
    Convert the OpenAlex abstract inverted index into
    normal readable text.
    """

    inverted_index = paper.get("abstract_inverted_index")

    if not inverted_index:
        return None

    words = []

    for word, positions in inverted_index.items():
        for position in positions:
            words.append((position, word))

    words.sort()

    abstract = " ".join(
        word for position, word in words
    )

    return abstract


# ---------------------------------------------------------
# Deduplication functions
# ---------------------------------------------------------

def normalise_title(title):
    """
    Create a standardised version of a title for comparison.

    This:
    - converts text to lowercase
    - removes punctuation
    - replaces repeated whitespace with a single space
    - removes leading/trailing whitespace
    """

    if not title:
        return ""

    title = title.lower()

    # Replace punctuation with spaces
    title = re.sub(r"[^\w\s]", " ", title)

    # Replace multiple spaces with one space
    title = re.sub(r"\s+", " ", title)

    return title.strip()


def choose_preferred_paper(existing_paper, new_paper):
    """
    Given two records with the same normalised title,
    choose the most recently published version.

    Publication dates are in YYYY-MM-DD format, which
    allows them to be compared directly as strings.
    """

    existing_date = (
        existing_paper.get("publication_date") or ""
    )

    new_date = (
        new_paper.get("publication_date") or ""
    )

    if new_date > existing_date:
        return new_paper

    return existing_paper


def deduplicate_by_title(papers):
    """
    Collapse papers that have the same normalised title.

    When multiple records have the same title:
    - retain the most recently published record
    - combine all search terms that retrieved the records
    """

    papers_by_title = {}

    for paper in papers:

        title = paper.get("title", "")
        normalised_title = normalise_title(title)

        # If there is somehow no usable title, use the
        # OpenAlex ID instead so unrelated blank titles
        # are not merged together.
        if not normalised_title:
            normalised_title = paper.get("id", "")

        if normalised_title not in papers_by_title:
            papers_by_title[normalised_title] = paper
            continue

        existing_paper = papers_by_title[normalised_title]

        # Preserve all search terms associated with either
        # version of the paper.
        all_matched_terms = set(
            existing_paper.get("matched_terms", [])
        )

        all_matched_terms.update(
            paper.get("matched_terms", [])
        )

        # Decide which bibliographic record to retain.
        preferred_paper = choose_preferred_paper(
            existing_paper,
            paper,
        )

        preferred_paper["matched_terms"] = sorted(
            all_matched_terms
        )

        papers_by_title[normalised_title] = preferred_paper

    return list(papers_by_title.values())


# ---------------------------------------------------------
# Collect papers
# ---------------------------------------------------------
print(
    f"Searching publications from "
    f"{start_date} to {end_date}"
)

print()

unique_papers = {}


for term in watch_terms:

    print(f"Searching: {term}")

    papers = search_openalex(term)

    print(f"Found {len(papers)} papers")

    for paper in papers:

        openalex_id = paper.get("id")

        if not openalex_id:
            continue

        # First level of deduplication:
        # identical OpenAlex records returned by
        # multiple searches.
        if openalex_id not in unique_papers:

            paper["matched_terms"] = []

            unique_papers[openalex_id] = paper

        unique_papers[openalex_id][
            "matched_terms"
        ].append(term)


# Convert dictionary back into a list.
papers = list(unique_papers.values())


print()
print(
    f"Unique OpenAlex records: {len(papers)}"
)


# ---------------------------------------------------------
# Second deduplication pass
# ---------------------------------------------------------

number_before_title_deduplication = len(papers)

papers = deduplicate_by_title(papers)

number_after_title_deduplication = len(papers)

duplicates_removed = (
    number_before_title_deduplication
    - number_after_title_deduplication
)


print(
    f"Unique works after title deduplication: "
    f"{number_after_title_deduplication}"
)

print(
    f"Duplicate/version records removed: "
    f"{duplicates_removed}"
)


# ---------------------------------------------------------
# Convert OpenAlex records into clean paper records
# ---------------------------------------------------------

clean_papers = []


for paper in papers:

    clean_paper = {
        "openalex_id": paper.get("id"),
        "title": paper.get("title"),
        "publication_date": paper.get(
            "publication_date"
        ),
        "doi": paper.get("doi"),
        "authors": get_authors(paper),
        "source": get_source(paper),
        "abstract": reconstruct_abstract(paper),
        "matched_terms": "; ".join(
            sorted(
                set(
                    paper.get(
                        "matched_terms",
                        [],
                    )
                )
            )
        ),
    }

    clean_papers.append(clean_paper)


# ---------------------------------------------------------
# Sort by publication date
# ---------------------------------------------------------

clean_papers.sort(
    key=lambda paper: paper[
        "publication_date"
    ] or "",
    reverse=True,
)

fieldnames = [
    "openalex_id",
    "title",
    "publication_date",
    "doi",
    "authors",
    "source",
    "abstract",
    "matched_terms",
]

with open(
    OUTPUT_FILE,
    "w",
    newline="",
    encoding="utf-8",
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames,
    )

    writer.writeheader()
    writer.writerows(clean_papers)

print()
print(
    f"Saved {len(clean_papers)} papers "
    f"to {OUTPUT_FILE}"
)
# -----------