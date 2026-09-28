import csv

import yaml


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

INTERESTS_FILE = "config/interests.yaml"
INPUT_FILE = "data/candidate_papers.csv"
OUTPUT_FILE = "data/ranked_papers.csv"

TOP_PAPERS_TO_PRINT = 10


# ---------------------------------------------------------
# Scoring weights
# ---------------------------------------------------------

HIGH_PRIORITY_TITLE_WEIGHT = 5
HIGH_PRIORITY_ABSTRACT_WEIGHT = 3

MEDIUM_PRIORITY_TITLE_WEIGHT = 3
MEDIUM_PRIORITY_ABSTRACT_WEIGHT = 2

ADJACENT_TITLE_WEIGHT = 2
ADJACENT_ABSTRACT_WEIGHT = 1

WATCH_TERM_TITLE_WEIGHT = 6
WATCH_TERM_ABSTRACT_WEIGHT = 4

EXCLUDED_TITLE_WEIGHT = 8
EXCLUDED_ABSTRACT_WEIGHT = 4


# ---------------------------------------------------------
# Text matching
# ---------------------------------------------------------

def contains_term(text, term):
    """
    Return True if a term occurs in the supplied text.

    Matching is case-insensitive.
    """

    if not text:
        return False

    return term.lower() in text.lower()


def score_terms(
    title,
    abstract,
    terms,
    title_weight,
    abstract_weight,
):
    """
    Calculate the score contributed by a collection of terms.

    A term can contribute points for appearing in both
    the title and abstract.
    """

    score = 0

    for term in terms:

        if contains_term(title, term):
            score += title_weight

        if contains_term(abstract, term):
            score += abstract_weight

    return score


# ---------------------------------------------------------
# Paper scoring
# ---------------------------------------------------------

def score_paper(paper, interests):
    """
    Calculate the total relevance score for one paper.
    """

    title = paper.get("title", "")
    abstract = paper.get("abstract", "")

    score = 0

    # High-priority research themes
    score += score_terms(
        title,
        abstract,
        interests["research_themes"]["high_priority"],
        HIGH_PRIORITY_TITLE_WEIGHT,
        HIGH_PRIORITY_ABSTRACT_WEIGHT,
    )

    # Medium-priority research themes
    score += score_terms(
        title,
        abstract,
        interests["research_themes"]["medium_priority"],
        MEDIUM_PRIORITY_TITLE_WEIGHT,
        MEDIUM_PRIORITY_ABSTRACT_WEIGHT,
    )

    # High-priority taxa
    score += score_terms(
        title,
        abstract,
        interests["taxa"]["high_priority"],
        HIGH_PRIORITY_TITLE_WEIGHT,
        HIGH_PRIORITY_ABSTRACT_WEIGHT,
    )

    # Medium-priority taxa
    score += score_terms(
        title,
        abstract,
        interests["taxa"]["medium_priority"],
        MEDIUM_PRIORITY_TITLE_WEIGHT,
        MEDIUM_PRIORITY_ABSTRACT_WEIGHT,
    )

    # High-priority methods
    score += score_terms(
        title,
        abstract,
        interests["methods"]["high_priority"],
        HIGH_PRIORITY_TITLE_WEIGHT,
        HIGH_PRIORITY_ABSTRACT_WEIGHT,
    )

    # Medium-priority methods
    score += score_terms(
        title,
        abstract,
        interests["methods"]["medium_priority"],
        MEDIUM_PRIORITY_TITLE_WEIGHT,
        MEDIUM_PRIORITY_ABSTRACT_WEIGHT,
    )

    # High-priority ecological topics
    score += score_terms(
        title,
        abstract,
        interests["ecological_topics"]["high_priority"],
        HIGH_PRIORITY_TITLE_WEIGHT,
        HIGH_PRIORITY_ABSTRACT_WEIGHT,
    )

    # Medium-priority ecological topics
    score += score_terms(
        title,
        abstract,
        interests["ecological_topics"]["medium_priority"],
        MEDIUM_PRIORITY_TITLE_WEIGHT,
        MEDIUM_PRIORITY_ABSTRACT_WEIGHT,
    )

    # Adjacent interests
    score += score_terms(
        title,
        abstract,
        interests["adjacent_interests"],
        ADJACENT_TITLE_WEIGHT,
        ADJACENT_ABSTRACT_WEIGHT,
    )

    # Terms that we particularly want to watch
    score += score_terms(
        title,
        abstract,
        interests["watch_terms"],
        WATCH_TERM_TITLE_WEIGHT,
        WATCH_TERM_ABSTRACT_WEIGHT,
    )

    # Penalise topics that are generally irrelevant
    score -= score_terms(
        title,
        abstract,
        interests["exclude_topics"],
        EXCLUDED_TITLE_WEIGHT,
        EXCLUDED_ABSTRACT_WEIGHT,
    )

    return score


# ---------------------------------------------------------
# Matching interests
# ---------------------------------------------------------

def get_all_interest_terms(interests):
    """
    Combine the relevant terms from interests.yaml
    into a single list.
    """

    all_terms = []

    for section in [
        "research_themes",
        "taxa",
        "methods",
        "ecological_topics",
    ]:
        all_terms.extend(
            interests[section]["high_priority"]
        )

        all_terms.extend(
            interests[section]["medium_priority"]
        )

    all_terms.extend(
        interests["adjacent_interests"]
    )

    all_terms.extend(
        interests["watch_terms"]
    )

    return all_terms


def get_matched_interests(paper, interest_terms):
    """
    Return a readable list of interests found in the
    paper's title or abstract.
    """

    title = paper.get("title", "")
    abstract = paper.get("abstract", "")

    combined_text = f"{title} {abstract}"

    matches = set()

    for term in interest_terms:
        if contains_term(combined_text, term):
            matches.add(term)

    return "; ".join(sorted(matches))


# ---------------------------------------------------------
# Relevance categories
# ---------------------------------------------------------

def get_relevance_category(score):
    """
    Convert a numerical relevance score into a simple
    descriptive category.
    """

    if score >= 20:
        return "very high"

    if score >= 12:
        return "high"

    if score >= 6:
        return "medium"

    return "low"


# ---------------------------------------------------------
# Load files
# ---------------------------------------------------------

def load_interests():
    """
    Load the research-interest configuration.
    """

    with open(
        INTERESTS_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        return yaml.safe_load(file)


def load_papers():
    """
    Load candidate papers produced by collect_papers.py.
    """

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        reader = csv.DictReader(file)
        return list(reader)


# ---------------------------------------------------------
# Rank papers
# ---------------------------------------------------------

def rank_papers(papers, interests):
    """
    Score and rank all candidate papers.
    """

    interest_terms = get_all_interest_terms(interests)

    for paper in papers:

        score = score_paper(
            paper,
            interests,
        )

        paper["relevance_score"] = score

        paper["relevance_category"] = (
            get_relevance_category(score)
        )

        paper["matched_interests"] = (
            get_matched_interests(
                paper,
                interest_terms,
            )
        )

    return sorted(
        papers,
        key=lambda paper: paper["relevance_score"],
        reverse=True,
    )


# ---------------------------------------------------------
# Output
# ---------------------------------------------------------

def print_top_papers(ranked_papers):
    """
    Print the highest-ranked papers to the terminal.
    """

    print()
    print(
        f"Top {TOP_PAPERS_TO_PRINT} papers:"
    )
    print()

    for number, paper in enumerate(
        ranked_papers[:TOP_PAPERS_TO_PRINT],
        start=1,
    ):
        print(
            f"{number}. "
            f"[{paper['relevance_score']}] "
            f"{paper['title']}"
        )

        print(
            f"   Relevance: "
            f"{paper['relevance_category']}"
        )

        print(
            f"   Matches: "
            f"{paper['matched_interests']}"
        )

        print()


def save_ranked_papers(ranked_papers):
    """
    Save ranked papers to CSV.
    """

    if not ranked_papers:
        print("No papers to save.")
        return

    fieldnames = list(
        ranked_papers[0].keys()
    )

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
        writer.writerows(ranked_papers)

    print(
        f"Saved {len(ranked_papers)} ranked papers "
        f"to {OUTPUT_FILE}"
    )


# ---------------------------------------------------------
# Main program
# ---------------------------------------------------------

def main():
    interests = load_interests()
    papers = load_papers()

    print(
        f"Loaded {len(papers)} candidate papers"
    )

    if not papers:
        print("No candidate papers found.")
        return

    ranked_papers = rank_papers(
        papers,
        interests,
    )

    print_top_papers(ranked_papers)

    save_ranked_papers(ranked_papers)


if __name__ == "__main__":
    main()