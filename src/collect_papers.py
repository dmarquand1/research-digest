import csv
import os

import requests
import yaml
from dotenv import load_dotenv


OPENALEX_URL = "https://api.openalex.org/works"


load_dotenv()

api_key = os.getenv("OPENALEX_API_KEY")

if api_key is None:
    raise ValueError("OPENALEX_API_KEY was not found.")


def search_openalex(search_term):
    params = {
        "search": search_term,
        "filter": "from_publication_date:2026-01-01",
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


def get_authors(paper):
    authors = []

    for authorship in paper.get("authorships", []):
        author = authorship.get("author", {})
        name = author.get("display_name")

        if name:
            authors.append(name)

    return "; ".join(authors)


def get_source(paper):
    primary_location = paper.get("primary_location")

    if not primary_location:
        return None

    source = primary_location.get("source")

    if not source:
        return None

    return source.get("display_name")


def reconstruct_abstract(paper):
    inverted_index = paper.get("abstract_inverted_index")

    if not inverted_index:
        return None

    words = []

    for word, positions in inverted_index.items():
        for position in positions:
            words.append((position, word))

    words.sort()

    abstract = " ".join(word for position, word in words)

    return abstract


with open("config/interests.yaml", "r", encoding="utf-8") as file:
    interests = yaml.safe_load(file)


watch_terms = interests["watch_terms"]

unique_papers = {}


for term in watch_terms:
    print(f"Searching: {term}")

    papers = search_openalex(term)

    print(f"Found {len(papers)} papers")

    for paper in papers:
        openalex_id = paper["id"]

        if openalex_id not in unique_papers:
            paper["matched_terms"] = []
            unique_papers[openalex_id] = paper

        unique_papers[openalex_id]["matched_terms"].append(term)


papers = list(unique_papers.values())

print()
print(f"Unique papers collected: {len(papers)}")


clean_papers = []

for paper in papers:
    clean_paper = {
        "openalex_id": paper.get("id"),
        "title": paper.get("title"),
        "publication_date": paper.get("publication_date"),
        "doi": paper.get("doi"),
        "authors": get_authors(paper),
        "source": get_source(paper),
        "abstract": reconstruct_abstract(paper),
        "matched_terms": "; ".join(paper.get("matched_terms", [])),
    }

    clean_papers.append(clean_paper)


output_file = "data/candidate_papers.csv"

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


with open(output_file, "w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=fieldnames)

    writer.writeheader()
    writer.writerows(clean_papers)


print()
print(f"Saved {len(clean_papers)} papers to {output_file}")