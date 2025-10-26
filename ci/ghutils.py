# ghutils.py

import subprocess
import json
import os
GITHUB_TOKEN = os.getenv("GH_PAT")
if not GITHUB_TOKEN:
    raise EnvironmentError("GITHUB_TOKEN environment variable not set")
def run_gh(*args: str) -> str:
    """Run a GitHub CLI command and return stdout. Throw on error."""
    result = subprocess.run(["gh", *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def repository_exists(repo: str) -> bool:
    """Return True if the given GitHub repository exists."""
    try:
        run_gh("repo", "view", repo)
        return True
    except RuntimeError:
        return False


def get_description(repo: str) -> str:
    """Return the repository description as a string."""
    output = run_gh("repo", "view", repo, "--json", "description")
    data = json.loads(output)
    return data.get("description", "") or ""


def description_contains(repo: str, text: str) -> bool:
    """Return True if the repository description contains the given text."""
    return text in get_description(repo)

def set_description(repo: str, description: str) -> None:
    """Set the repository description."""
    run_gh("repo", "edit", repo, "--description", description)

def create_if_not_exists(repo: str, public: bool = True, create_in_user_space: bool = False) -> bool:
    """
    Create the repository if it does not already exist.
    Returns True if created, False otherwise.
    """
    if not create_in_user_space:
        if "/" not in repo:
            raise ValueError("Repository name must be in the form 'organization/name' when create_in_user_space is False")
    if repository_exists(repo):
        return False

    visibility = "--public" if public else "--private"
    run_gh("repo", "create", repo, visibility, "--yes")
    set_description(repo, "Created by PRUPLE's ghutils.py")
    return True
def ensure_pruple_managed(repo: str) -> None:
    """Ensure the repository description indicates it is managed by PRUPLE."""
    description = get_description(repo)
    marker = "Managed by PRUPLE"
    if marker not in description:
        if description:
            description += " | "
        description += marker
        set_description(repo, description)
    return None

def push_mirror_if_target_description_matches(local_repo_path: str, target_repo: str, match_text: str) -> bool:
    """
    Mirror-push the local repository to target_repo if the target repo's description contains match_text.

    local_repo_path: local git repository path
    target_repo:     GitHub repo in the form "owner/name"
    match_text:      String to match in the target repository description

    Returns True if push occurred, False otherwise.
    """
    # Ensure target exists before checking description
    create_if_not_exists(target_repo)

    if not description_contains(target_repo, match_text):
        return False

    # Perform mirror push using git and the token-authenticated URL
    remote_url = f"https://{GITHUB_TOKEN}:x-oauth-basic@github.com/{target_repo}.git"
    subprocess.run(
        ["git", "-C", local_repo_path, "push", "--mirror", remote_url],
        check=True
    )
    return True
#push_mirror is an alias for push_mirror_if_target_description_matches with match_text preset
def push_mirror(local_repo_path: str, target_repo: str) -> bool:
    """
    Mirror-push the local repository to target_repo if the target repo is PRUPLE-managed.

    local_repo_path: local git repository path
    target_repo:     GitHub repo in the form "owner/name"

    Returns True if push occurred, False otherwise.
    """
    return push_mirror_if_target_description_matches(local_repo_path, target_repo, "Managed by PRUPLE")