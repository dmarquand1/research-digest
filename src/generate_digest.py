import csv
from datetime import date, timedelta
from pathlib import Path

INPUT_FILE = Path("data/ranked_papers.csv")
OUTPUT_DIR = Path("output")

NUMBER_OF_PAPERS = 10
DAYS_IN_DIGEST = 7

def load_ranked_papers():
    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        reader = csv.DictReader(file)
        return list(reader)

def get_digest_dates():
    end_date = date.today()

    start_date = end_date - timedelta(
        days=DAYS_IN_DIGEST
    )

    return start_date, end_date

def format_date(date_value):
    return date_value.strftime(
        "%d %B %Y"
    )

def format_authors(authors_text):
    if not authors_text:
        return "Authors unavailable"

    authors = [
        author.strip()
        for author in authors_text.split(";")
        if author.strip()
    ]

    if len(authors) <= 3:
        return ", ".join(authors)

    return f"{authors[0]} et al."

def get_paper_url(paper):
    doi = paper.get("doi", "").strip()

    if doi:
        return doi

    return paper.get("openalex_id", "")

def format_relevance(category):
    labels = {
        "very high": "🔥 Very high",
        "high": "⭐ High",
        "medium": "👀 Medium",
        "low": "Low",
    }

    return labels.get(
        category,
        category,
    )

def format_matches(matches):
    if not matches:
        return "No specific matches recorded"

    terms = [
        term.strip()
        for term in matches.split(";")
        if term.strip()
    ]

    return ", ".join(terms)

def make_paper_entry(number, paper):
    title = paper.get(
        "title",
        "Untitled paper",
    )

    authors = format_authors(
        paper.get("authors", "")
    )

    source = (
        paper.get("source")
        or "Source unavailable"
    )

    publication_date = (
        paper.get("publication_date")
        or "Date unavailable"
    )

    relevance = format_relevance(
        paper.get(
            "relevance_category",
            "",
        )
    )

    score = paper.get(
        "relevance_score",
        "",
    )

    matches = format_matches(
        paper.get(
            "matched_interests",
            "",
        )
    )

    url = get_paper_url(paper)

    lines = []

    lines.append(
        f"### {number}. {title}"
    )

    lines.append("")

    lines.append(
        f"**{authors}**"
    )

    lines.append(
        f"*{source}* · {publication_date}"
    )

    lines.append("")

    lines.append(
        f"**Relevance:** {relevance} "
        f"· Score {score}"
    )

    lines.append("")

    lines.append(
        f"**Matched interests:** {matches}"
    )

    lines.append("")
    if url:
        lines.append(
            f"{url}"
        )

        lines.append("")
    lines.append("---")
    lines.append("")

    return "\n".join(lines)

def make_header(
    start_date,
    end_date,
    total_candidates,
    selected_papers,
):
    lines = []

    lines.append(
        "# 🔬 Daniel's Research Digest"
    )

    lines.append("")

    lines.append(
        f"**{format_date(start_date)} "
        f"to {format_date(end_date)}**"
    )

    lines.append("")

    lines.append(
        f"{total_candidates} candidate papers found. "
        f"The top {selected_papers} are shown below."
    )

    lines.append("")

    lines.append(
        "## 📚 Top papers"
    )

    lines.append("")

    return "\n".join(lines)

def build_digest(papers):
    start_date, end_date = (
        get_digest_dates()
    )

    selected_papers = papers[
        :NUMBER_OF_PAPERS
    ]

    sections = []

    sections.append(
        make_header(
            start_date,
            end_date,
            len(papers),
            len(selected_papers),
        )
    )

    for number, paper in enumerate(
        selected_papers,
        start=1,
    ):
        sections.append(
            make_paper_entry(
                number,
                paper,
            )
        )

    return "\n".join(sections)

def get_output_file():
    today = date.today()

    filename = (
        f"research_digest_"
        f"{today.isoformat()}.md"
    )

    return OUTPUT_DIR / filename

def save_digest(content):
    OUTPUT_DIR.mkdir(
        exist_ok=True
    )

    output_file = get_output_file()

    with open(
        output_file,
        "w",
        encoding="utf-8",
    ) as file:
        file.write(content)

    return output_file

def main():
    papers = load_ranked_papers()

    print(
        f"Loaded {len(papers)} "
        f"ranked papers"
    )

    if not papers:
        print(
            "No ranked papers available."
        )
        return

    digest = build_digest(papers)

    output_file = save_digest(
        digest
    )

    print(
        f"Saved research digest to "
        f"{output_file}"
    )

if __name__ == "__main__":
    main()