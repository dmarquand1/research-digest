import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent

COLLECT_SCRIPT = (
    PROJECT_ROOT
    / "src"
    / "collect_papers.py"
)

RANK_SCRIPT = (
    PROJECT_ROOT
    / "src"
    / "rank_papers.py"
)

DIGEST_SCRIPT = (
    PROJECT_ROOT
    / "src"
    / "generate_digest.py"
)


# ---------------------------------------------------------
# Pipeline helpers
# ---------------------------------------------------------

def run_script(script_path, description):
    """
    Run one Python script as part of the research
    digest pipeline.

    Returns the script's exit code.
    """

    print()
    print("=" * 60)
    print(description)
    print("=" * 60)
    print()

    result = subprocess.run(
        [
            sys.executable,
            script_path,
        ],
        cwd=PROJECT_ROOT,
    )

    return result.returncode


# ---------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------

def main():
    """
    Run the complete research digest pipeline.
    """

    print()
    print("RESEARCH DIGEST")
    print("=" * 60)

    # Step 1: Collect papers
    collect_result = run_script(
        COLLECT_SCRIPT,
        "STEP 1: Collecting new papers",
    )

    if collect_result != 0:
        print()
        print(
            "Collection failed. "
            "Stopping pipeline."
        )
        sys.exit(collect_result)

    # Step 2: Rank papers
    rank_result = run_script(
        RANK_SCRIPT,
        "STEP 2: Ranking papers",
    )

    if rank_result != 0:
        print()
        print(
            "Ranking failed. "
            "Stopping pipeline."
        )
        sys.exit(rank_result)

    # Step 3: Generate digest
    digest_result = run_script(
        DIGEST_SCRIPT,
        "STEP 3: Generating research digest",
    )

    if digest_result != 0:
        print()
        print(
            "Digest generation failed. "
            "Stopping pipeline."
        )
        sys.exit(digest_result)

    # Complete
    print()
    print("=" * 60)
    print("RESEARCH DIGEST COMPLETE")
    print("=" * 60)
    print()

    print(
        "Your latest digest is in the "
        "output directory."
    )


if __name__ == "__main__":
    main()