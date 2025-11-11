import subprocess
import json
import os

# ---------------------------------------------------------------------
#  Configuration and Token Setup
# ---------------------------------------------------------------------
GITHUB_TOKEN = os.getenv("PRUPLEPAT")
if not GITHUB_TOKEN:
    raise EnvironmentError("PRUPLEPAT environment variable not set")

# Unset GitHub Actions' default token to prevent gh from auto-authing as github-actions[bot]
os.environ.pop("GITHUB_TOKEN", None)

# Authenticate gh manually with your own token
subprocess.run(
    ["gh", "auth", "login", "--with-token"],
    input=GITHUB_TOKEN.encode(),
    text=True,
    check=True
)
subprocess.run(["gh", "auth", "setup-git"], check=True)


# ---------------------------------------------------------------------
#  Utility Functions
# ---------------------------------------------------------------------
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
            raise ValueError("Repository name must be 'organization/name' when create_in_user_space=False")

    if repository_exists(repo):
        return False

    visibility = "--public" if public else "--private"
    run_gh("repo", "create", repo, visibility)
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


# ---------------------------------------------------------------------
#  Push Function
# ---------------------------------------------------------------------
def push_mirror_if_target_description_matches(local_repo_path: str, target_repo: str, match_text: str) -> bool:
    """
    Mirror-push the local repository to target_repo if the target repo's description contains match_text.

    local_repo_path: local git repository path
    target_repo:     GitHub repo in the form "owner/name"
    match_text:      String to match in the target repository description

    Returns True if push occurred, False otherwise.
    """
    create_if_not_exists(target_repo)

    if not description_contains(target_repo, match_text):
        print(f"[!] Skipping push: target repo '{target_repo}' is not PRUPLE-managed.")
        return False

    remote_url = f"https://x-access-token:{GITHUB_TOKEN}@github.com/{target_repo}.git"
    safe_remote = f"https://x-access-token:*****@github.com/{target_repo}.git"

    # Clean remote, re-add fresh one
    subprocess.run(
        ["git", "-C", local_repo_path, "remote", "remove", "pruple-mirror"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    subprocess.run(
        ["git", "-C", local_repo_path, "remote", "add", "pruple-mirror", remote_url],
        check=True
    )

    print(f"[>] Pushing mirror to {safe_remote} ...")
    result = subprocess.run(
        ["git", "-C", local_repo_path, "push", "--mirror", "pruple-mirror"],
        text=True,
        capture_output=True
    )

    if result.returncode != 0:
        stderr = result.stderr.replace(GITHUB_TOKEN, "*****")
        stdout = result.stdout.replace(GITHUB_TOKEN, "*****")
        print(f"[!] Push failed with code {result.returncode}")
        print(stdout)
        print(stderr)
        raise subprocess.CalledProcessError(result.returncode, result.args, output=stdout, stderr=stderr)

    print("[✓] Mirror push successful.")
    return True


def push_mirror(local_repo_path: str, target_repo: str) -> bool:
    """Alias for push_mirror_if_target_description_matches with 'Managed by PRUPLE'."""
    return push_mirror_if_target_description_matches(local_repo_path, target_repo, "Managed by PRUPLE")
