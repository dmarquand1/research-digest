import os

import requests
from dotenv import load_dotenv


load_dotenv()

api_key = os.getenv("OPENALEX_API_KEY")

if api_key is None:
    raise ValueError("OPENALEX_API_KEY was not found.")

url = "https://api.openalex.org/works"

params = {
    "search": "automated insect monitoring",
    "filter": "from_publication_date:2026-01-01",
    "per_page": 10,
    "api_key": api_key,
}

response = requests.get(url, params=params, timeout=30)
response.raise_for_status()

data = response.json()

papers = data["results"]

for number, paper in enumerate(papers, start=1):
    title = paper.get("title")
    date = paper.get("publication_date")
    doi = paper.get("doi")

    print(f"{number}. {title}")
    print(f"   Published: {date}")
    print(f"   DOI: {doi}")
    print()