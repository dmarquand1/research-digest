# Research Digest

A Python tool for automatically discovering, ranking, and compiling newly published scientific literature into a weekly research digest.

The project was developed to make it easier to keep up with research across biodiversity monitoring, automated ecological monitoring, computer vision, machine learning, bioacoustics, and related topics.

The system searches OpenAlex for recently published literature, removes duplicate records, scores papers according to a configurable research-interest profile, and generates a ranked Markdown digest.

## Overview

The pipeline works as follows:

```text
Research interests
      │
      ▼
OpenAlex literature search
      │
      ▼
Candidate papers
      │
      ▼
Deduplication
      │
      ▼
Relevance scoring
      │
      ▼
Ranked papers
      │
      ▼
Markdown research digest
```

The complete pipeline can be run with:

```bash
python run_digest.py
```

## Project structure

```text
research-digest/
│
├── config/
│   └── interests.yaml
│
├── data/
│   ├── candidate_papers.csv
│   └── ranked_papers.csv
│
├── output/
│   └── research_digest_YYYY-MM-DD.md
│
├── src/
│   ├── collect_papers.py
│   ├── rank_papers.py
│   └── generate_digest.py
│
├── .env
├── .gitignore
├── README.md
├── requirements.txt
└── run_digest.py
```

Generated files in `data/` and `output/` are excluded from Git.

The `.env` file is also excluded from Git and is used for locally storing API credentials.

## Pipeline

### 1. Literature collection

`src/collect_papers.py`

The collector:

1. Loads literature search queries from `config/interests.yaml`.
2. Calculates the required publication-date window.
3. Searches OpenAlex for matching publications.
4. Retrieves publication metadata, including titles, authors, dates, DOIs, sources, and abstracts where available.
5. Combines results from multiple searches.
6. Removes duplicate OpenAlex records.
7. Normalises paper titles to identify additional duplicate or version records.
8. Retains the most recent version where records have equivalent titles.
9. Saves the resulting literature pool to:

```text
data/candidate_papers.csv
```

### 2. Relevance ranking

`src/rank_papers.py`

The ranking system compares each candidate paper against the interests defined in:

```text
config/interests.yaml
```

Papers receive points when relevant terms occur in their titles or abstracts.

The scoring system considers:

- research themes
- taxonomic interests
- methodological interests
- ecological topics
- adjacent interests
- high-interest watch terms
- excluded or generally irrelevant topics

Title matches receive greater weight than abstract matches.

The system deliberately uses a simple and transparent keyword-based scoring approach rather than an AI recommendation model.

Papers are assigned:

- a numerical relevance score
- a relevance category
- a list of matched research interests

The ranked results are saved to:

```text
data/ranked_papers.csv
```

### 3. Digest generation

`src/generate_digest.py`

The digest generator takes the ranked papers and produces a Markdown newsletter containing the highest-ranked publications.

Entries include information such as:

- title
- authors
- publication source
- publication date
- relevance score
- relevance category
- matched research interests
- DOI or OpenAlex link

The generated digest is saved to the project's:

```text
output/
```

directory.

It can also be configured to save an additional copy to a separate notes directory.

### 4. Pipeline runner

`run_digest.py`

This is the main entry point for the application.

It executes:

```text
collect_papers.py
        ↓
rank_papers.py
        ↓
generate_digest.py
```

If any stage fails, the pipeline stops rather than continuing with potentially outdated intermediate data.

---

# Installation

## Requirements

- Python 3
- Git
- An OpenAlex API key
- The Python packages listed in `requirements.txt`

## Clone the repository

```bash
git clone YOUR_REPOSITORY_URL
cd research-digest
```

## Create a virtual environment

On Windows:

```bash
python -m venv .venv
```

When using Git Bash:

```bash
source .venv/Scripts/activate
```

The prompt should then display:

```text
(.venv)
```

You can confirm which Python interpreter is active with:

```bash
which python
```

## Install dependencies

```bash
python -m pip install -r requirements.txt
```

## Configure the OpenAlex API key

Make an account with OpenAlex and create an API key: [openalex.org/settings/api-key](https://openalex.org/settings/api-key)

Create a file in the project root called:

```text
.env
```

Add:

```text
OPENALEX_API_KEY=YOUR_API_KEY_HERE
```

Do not commit this file to Git.

The repository's `.gitignore` should contain:

```gitignore
.env
```

You can check that Git is ignoring the file with:

```bash
git check-ignore -v .env
```

---

# Configuring research interests

Research interests are defined in:

```text
config/interests.yaml
```

This keeps the scientific configuration separate from the Python code.

The configuration includes sections such as:

```yaml
research_themes:

  high_priority:
    - automated biodiversity monitoring
    - automated insect monitoring
    - computer vision for biodiversity

  medium_priority:
    - biodiversity monitoring technology
    - ecological monitoring
```

Other sections can define:

```yaml
taxa:
methods:
ecological_topics:
adjacent_interests:
watch_terms:
exclude_topics:
search_queries:
```

## Search queries versus research interests

`search_queries` control **which literature OpenAlex retrieves**.

For example:

```yaml
search_queries:
  - automated insect monitoring
  - computer vision biodiversity
  - automated biodiversity monitoring
  - insect camera trap
```

The other interest categories determine **how strongly the retrieved papers are ranked**.

This means literature discovery and relevance ranking can be adjusted independently.

---

# Running the digest

Activate the project's virtual environment:

```bash
source .venv/Scripts/activate
```

Then run:

```bash
python run_digest.py
```

A successful run performs the complete workflow:

```text
Search OpenAlex
      ↓
Collect recent papers
      ↓
Deduplicate records
      ↓
Score relevance
      ↓
Rank papers
      ↓
Generate digest
```

The finished digest will appear in:

```text
output/
```

with a filename such as:

```text
research_digest_2026-09-28.md
```

Generated Markdown files can be previewed directly in VS Code.

---

# Running individual stages

The pipeline components can also be run independently when debugging.

## Collect papers

```bash
python src/collect_papers.py
```

## Rank papers

```bash
python src/rank_papers.py
```

## Generate the digest

```bash
python src/generate_digest.py
```

Running the stages individually is useful when developing or troubleshooting a particular part of the pipeline.

---

# Relevance scoring

The scoring system is intentionally simple and interpretable.

The current weighting scheme gives different values to high-priority, medium-priority, adjacent, and watch-term matches.

For example, high-priority interests receive more points than medium-priority interests, and matches in a paper's title receive more weight than matches found only in its abstract.

Excluded topics receive negative points.

Relevant papers are grouped into broad categories such as:

```text
Very high
High
Medium
Low
```

The objective is not to perfectly predict whether a paper will be interesting. The ranking is intended to bring potentially useful literature towards the top while still allowing wider scientific reading to appear in the digest.

---

# Deduplication

Literature databases can contain multiple records relating to the same underlying publication.

The collection pipeline therefore performs multiple levels of deduplication.

First, identical OpenAlex IDs returned by different search queries are merged.

Paper titles are then normalised by:

- converting to lowercase
- removing punctuation
- removing repeated whitespace

Records with equivalent normalised titles are treated as versions of the same work.

Where multiple versions exist, the most recent publication record is retained while matched search terms are combined.

Related but distinct research outputs, such as a journal article and an associated software or design repository, may remain as separate records.

---

# Data and generated files

The pipeline generates intermediate data files including:

```text
data/candidate_papers.csv
data/ranked_papers.csv
```

and final digest files under:

```text
output/
```

These files are generated automatically and do not need to be stored in Git.

The source code and configuration files are sufficient to reproduce them.

---

# Security

API keys and other credentials must never be committed to the repository.

Credentials should be stored in:

```text
.env
```

and loaded by Python using environment variables.

Before pushing changes, it is good practice to check:

```bash
git status
```

and confirm that `.env` is not being tracked.

You can additionally check:

```bash
git ls-files .env
```

This command should return no output.

---

# Development workflow

A typical development workflow is:

```bash
git status
git add -A
git status
git commit -m "Describe the change"
git push
```

Always inspect `git status` before committing, particularly when working with configuration files or credentials.

---

# Current status

The current version supports:

- configurable research interests
- configurable literature search queries
- OpenAlex API searching
- recent-publication date filtering
- metadata and abstract collection
- duplicate/version handling
- transparent relevance scoring
- ranked literature output
- Markdown research digest generation
- one-command pipeline execution
- optional additional digest output location

## Potential future improvements

Possible future developments include:

- tracking papers already shown in previous digests
- separating core recommendations from wider reading
- improved handling of preprints and final journal publications
- additional metadata sources where organisationally appropriate
- automated weekly execution
- approved email or other notification delivery
- evaluation of retrieval and ranking quality over time

---

# Purpose

The project is intended as a lightweight, transparent literature-monitoring tool.

Rather than attempting to automate scientific judgement, it reduces the repetitive work involved in searching for newly published literature and provides a manageable shortlist for human review.