"""
Sync LeetCode accepted submissions to the repository.

Fetches all accepted solutions for user 'jithin-jz' from LeetCode's GraphQL API
and writes them to the root directory organized by problem number and slug.
"""

import os
import json
import time
import requests

LEETCODE_API_URL = "https://leetcode.com/graphql"
USERNAME = "jithin-jz"

LANGUAGE_EXTENSIONS = {
    "python": "py",
    "python3": "py",
    "javascript": "js",
    "typescript": "ts",
    "java": "java",
    "cpp": "cpp",
    "c": "c",
    "csharp": "cs",
    "go": "go",
    "rust": "rs",
    "kotlin": "kt",
    "swift": "swift",
    "ruby": "rb",
    "scala": "scala",
    "php": "php",
    "mysql": "sql",
    "mssql": "sql",
    "oraclesql": "sql",
    "postgresql": "sql",
    "pythondata": "py",
    "bash": "sh",
}


def get_session():
    """Create a requests session with LeetCode auth cookies."""
    session = requests.Session()
    leetcode_session = os.environ.get("LEETCODE_SESSION", "")
    csrf_token = os.environ.get("LEETCODE_CSRF_TOKEN", "")

    if not leetcode_session or not csrf_token:
        raise EnvironmentError(
            "LEETCODE_SESSION and LEETCODE_CSRF_TOKEN environment variables are required."
        )

    session.cookies.set("LEETCODE_SESSION", leetcode_session, domain=".leetcode.com")
    session.cookies.set("csrftoken", csrf_token, domain=".leetcode.com")
    session.headers.update(
        {
            "Content-Type": "application/json",
            "Referer": "https://leetcode.com",
            "x-csrftoken": csrf_token,
            "User-Agent": "Mozilla/5.0",
        }
    )
    return session


def fetch_recent_ac_submissions(session, limit=20):
    """Fetch recent accepted submissions via GraphQL (not IP-blocked like REST API)."""
    query = """
    query recentAcSubmissions($username: String!, $limit: Int!) {
        recentAcSubmissionList(username: $username, limit: $limit) {
            id
            title
            titleSlug
            timestamp
            lang
        }
    }
    """

    response = session.post(
        LEETCODE_API_URL,
        json={"query": query, "variables": {"username": USERNAME, "limit": limit}},
    )

    if response.status_code != 200:
        print(f"Error fetching recent submissions: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        return []

    data = response.json()
    if "errors" in data:
        print(f"GraphQL errors: {data['errors']}")
        return []

    submissions = data.get("data", {}).get("recentAcSubmissionList", [])

    # Deduplicate: keep latest submission per (slug, lang)
    seen = {}
    for sub in submissions:
        key = f"{sub.get('titleSlug')}_{sub.get('lang')}"
        if key not in seen:
            seen[key] = sub

    return list(seen.values())


def fetch_problem_details(session, title_slug):
    """Fetch problem details (number, difficulty, topics)."""
    query = """
    query questionData($titleSlug: String!) {
        question(titleSlug: $titleSlug) {
            questionFrontendId
            title
            titleSlug
            difficulty
            topicTags {
                name
            }
        }
    }
    """

    response = session.post(
        LEETCODE_API_URL,
        json={"query": query, "variables": {"titleSlug": title_slug}},
    )

    if response.status_code != 200:
        return None

    data = response.json()
    return data.get("data", {}).get("question")


def fetch_submission_code(session, submission_id):
    """Fetch the actual code of a submission."""
    query = """
    query submissionDetails($submissionId: Int!) {
        submissionDetails(submissionId: $submissionId) {
            code
            lang {
                name
                verboseName
            }
        }
    }
    """

    response = session.post(
        LEETCODE_API_URL,
        json={"query": query, "variables": {"submissionId": int(submission_id)}},
    )

    if response.status_code != 200:
        return None

    data = response.json()
    details = data.get("data", {}).get("submissionDetails")
    if details:
        return details.get("code")
    return None


def write_solution(problem_details, lang, code):
    """Write solution file to the repository root."""
    frontend_id = problem_details.get("questionFrontendId", "0")
    title_slug = problem_details.get("titleSlug", "unknown")
    title = problem_details.get("title", "Unknown")
    difficulty = problem_details.get("difficulty", "Unknown")
    topics = [tag["name"] for tag in problem_details.get("topicTags", [])]

    # Pad the problem number
    padded_id = str(frontend_id).zfill(4)
    folder_name = f"{padded_id}-{title_slug}"

    os.makedirs(folder_name, exist_ok=True)

    # Write solution file: 0069-sqrtx/0069-sqrtx.py
    ext = LANGUAGE_EXTENSIONS.get(lang, lang)
    filename = f"{folder_name}.{ext}"
    filepath = os.path.join(folder_name, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(code)

    # Write README for the problem
    readme_path = os.path.join(folder_name, "README.md")
    if not os.path.exists(readme_path):
        readme_content = f"""# {padded_id}. {title}

**Difficulty:** {difficulty}

**Topics:** {', '.join(topics) if topics else 'N/A'}

**Link:** [https://leetcode.com/problems/{title_slug}/](https://leetcode.com/problems/{title_slug}/)
"""
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)

    return filepath


def main():
    print("=" * 50)
    print("LeetCode Sync - Starting")
    print("=" * 50)

    session = get_session()

    # Fetch recent accepted submissions via GraphQL
    print("\nFetching recent accepted submissions (via GraphQL)...")
    submissions = fetch_recent_ac_submissions(session, limit=20)
    print(f"Found {len(submissions)} recent accepted submissions.")

    if not submissions:
        print("No accepted submissions found.")
        print("If you just solved a problem, wait a minute and re-run.")
        return

    # Process each submission
    synced = 0
    for i, sub in enumerate(submissions):
        title_slug = sub.get("titleSlug", "")
        lang = sub.get("lang", "")
        submission_id = sub.get("id")
        title = sub.get("title", "Unknown")

        print(f"\n[{i+1}/{len(submissions)}] Processing: {title} ({lang})")

        # Fetch the code for this submission
        code = fetch_submission_code(session, submission_id)
        time.sleep(1)

        if not code:
            print(f"  Could not fetch code, skipping.")
            continue

        # Fetch problem details for folder naming
        problem_details = fetch_problem_details(session, title_slug)
        time.sleep(1)

        if not problem_details:
            print(f"  Could not fetch problem details, skipping.")
            continue

        filepath = write_solution(problem_details, lang, code)
        print(f"  Saved: {filepath}")
        synced += 1

    # Update stats
    stats = {
        "total_synced": synced,
        "last_sync": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "username": USERNAME,
    }
    with open("stats.json", "w") as f:
        json.dump(stats, f, indent=2)

    print(f"\n{'=' * 50}")
    print(f"Sync complete! {synced} solutions synced.")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
