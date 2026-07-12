"""
Sync LeetCode accepted submissions to the repository.

Fetches all accepted solutions for user 'jithin-jz' from LeetCode's GraphQL API
and writes them to the solutions/ directory organized by problem number and slug.
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

DIFFICULTY_MAP = {1: "Easy", 2: "Medium", 3: "Hard"}


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
        }
    )
    return session


def fetch_solved_problems(session):
    """Fetch list of all solved problems for the user."""
    query = """
    query userProblemsSolved($username: String!) {
        allQuestionsCount {
            difficulty
            count
        }
        matchedUser(username: $username) {
            submitStatsGlobal {
                acSubmissionNum {
                    difficulty
                    count
                }
            }
        }
    }
    """
    # First get all accepted submission slugs
    query_accepted = """
    query userProfileUserQuestionProgressV2($userSlug: String!) {
        userProfileUserQuestionProgressV2(userSlug: $userSlug) {
            numAcceptedQuestions {
                difficulty
                count
            }
        }
    }
    """

    # Fetch the full problem list with acceptance status
    problems = []
    offset = 0
    limit = 50

    while True:
        query_problemset = """
        query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
            problemsetQuestionList: questionList(
                categorySlug: $categorySlug
                limit: $limit
                skip: $skip
                filters: $filters
            ) {
                total: totalNum
                questions: data {
                    frontendQuestionId: questionFrontendId
                    title
                    titleSlug
                    difficulty
                    status
                    topicTags {
                        name
                    }
                }
            }
        }
        """

        response = session.post(
            LEETCODE_API_URL,
            json={
                "query": query_problemset,
                "variables": {
                    "categorySlug": "",
                    "skip": offset,
                    "limit": limit,
                    "filters": {"status": "AC"},
                },
            },
        )

        if response.status_code != 200:
            print(f"Error fetching problems: {response.status_code}")
            break

        data = response.json()
        question_list = data.get("data", {}).get("problemsetQuestionList", {})
        questions = question_list.get("questions", [])
        total = question_list.get("total", 0)

        if not questions:
            break

        problems.extend(questions)
        offset += limit

        if offset >= total:
            break

        time.sleep(1)  # Rate limiting

    return problems


def fetch_submission(session, title_slug):
    """Fetch the latest accepted submission for a problem."""
    query = """
    query submissionList($offset: Int!, $limit: Int!, $questionSlug: String!, $status: Int) {
        questionSubmissionList(
            offset: $offset
            limit: $limit
            questionSlug: $questionSlug
            status: $status
        ) {
            submissions {
                id
                lang
                code: submissionCode
                timestamp
                statusDisplay
            }
        }
    }
    """

    response = session.post(
        LEETCODE_API_URL,
        json={
            "query": query,
            "variables": {
                "questionSlug": title_slug,
                "offset": 0,
                "limit": 20,
                "status": 10,  # Accepted
            },
        },
    )

    if response.status_code != 200:
        return []

    data = response.json()
    submissions = (
        data.get("data", {}).get("questionSubmissionList", {}).get("submissions", [])
    )
    return submissions


def get_best_submissions(submissions):
    """Get the latest submission per language."""
    best = {}
    for sub in submissions:
        lang = sub.get("lang", "")
        if lang not in best:
            best[lang] = sub
    return best


def write_solution(problem, submissions):
    """Write solution files to the solutions directory."""
    frontend_id = problem.get("frontendQuestionId", "0")
    title_slug = problem.get("titleSlug", "unknown")
    title = problem.get("title", "Unknown")
    difficulty = problem.get("difficulty", "Unknown")
    topics = [tag["name"] for tag in problem.get("topicTags", [])]

    # Pad the problem number
    padded_id = str(frontend_id).zfill(4)
    folder_name = f"{padded_id}-{title_slug}"
    folder_path = os.path.join("solutions", folder_name)

    os.makedirs(folder_path, exist_ok=True)

    # Write each language submission
    for lang, sub in submissions.items():
        ext = LANGUAGE_EXTENSIONS.get(lang, lang)
        filename = f"solution.{ext}"
        filepath = os.path.join(folder_path, filename)

        # Add a header comment
        code = sub.get("code", "")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code)

    # Write README for the problem
    readme_path = os.path.join(folder_path, "README.md")
    if not os.path.exists(readme_path):
        readme_content = f"""# {padded_id}. {title}

**Difficulty:** {difficulty}

**Topics:** {', '.join(topics) if topics else 'N/A'}

**Link:** [https://leetcode.com/problems/{title_slug}/](https://leetcode.com/problems/{title_slug}/)
"""
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)


def main():
    print("Starting LeetCode sync...")
    session = get_session()

    print("Fetching solved problems...")
    problems = fetch_solved_problems(session)
    print(f"Found {len(problems)} solved problems.")

    if not problems:
        print("No solved problems found. Check your credentials.")
        return

    synced = 0
    for i, problem in enumerate(problems):
        title_slug = problem.get("titleSlug", "")
        frontend_id = problem.get("frontendQuestionId", "0")
        title = problem.get("title", "Unknown")

        print(f"[{i+1}/{len(problems)}] Processing: {frontend_id}. {title}")

        submissions = fetch_submission(session, title_slug)
        if not submissions:
            print(f"  No accepted submissions found, skipping.")
            continue

        best = get_best_submissions(submissions)
        write_solution(problem, best)
        synced += 1

        time.sleep(1.5)  # Rate limiting to avoid being blocked

    print(f"\nSync complete! {synced} problems synced.")


if __name__ == "__main__":
    main()
