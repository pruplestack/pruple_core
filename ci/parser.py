# tagmap_parser.py
import os
import yaml
from typing import Dict, List

# -----------------------------------------------------------
# 1. YAML Parsing
# -----------------------------------------------------------
def parse_tag_map(path: str = os.path.join(os.path.dirname(__file__), "tag_map.yaml")) -> tuple[Dict[str, str], Dict[str, List[str]]]:
    """
    Parse tag_map.yaml and return:
      repos       → {repo_alias: repo_url}
      tag_to_repo → {tag: [repo_aliases]}
    """
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # --- Extract repo URLs
    repos_section = data.get("repos", {})
    repos = {name: info["url"] for name, info in repos_section.items()}
    # --- Build tag → repo mapping
    tag_to_repo: Dict[str, List[str]] = {}
    for entry in data.get("tag_map", []):
        if not isinstance(entry, dict):
            print(f"[!] Skipping malformed entry: {entry}")
            continue
        for repo_alias, tags in entry.items():
            if not isinstance(tags, list):
                print(f"[!] Skipping invalid tag list for {repo_alias}: {tags}")
                continue
            for tag in tags:
                tag_to_repo.setdefault(tag, []).append(repo_alias)

    return repos, tag_to_repo


# -----------------------------------------------------------
# 2. File Tag Utilities
# -----------------------------------------------------------
def file_has_tag(file_path: str, tag: str) -> bool:
    """Return True if a file contains a '#tag' string."""
    if not os.path.isfile(file_path):
        print(f"[!] File not found: {file_path}")
        return False
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f"#{tag}" in f.read()
    except Exception as e:
        print(f"[!] Error reading {file_path}: {e}")
        return False


def list_tags_in_file(file_path: str, known_tags: dict[str, list[str]]) -> list[str]:
    """
    Extract all #tags from a file that exist in the provided tag map.
    """
    if not os.path.isfile(file_path):
        print(f"[!] File not found: {file_path}")
        return []

    found = set()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for word in f.read().split():
                if word.startswith("#"):
                    tag = word[1:]
                    if tag in known_tags:
                        found.add(tag)
    except Exception as e:
        print(f"[!] Error reading {file_path}: {e}")
    return sorted(found)
def build_file_repo_dict_map(base_dir: str, tag_to_repo: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    Scan all files in base_dir and map each file to the list of repositories
    it should be included in based on its tags.
    """
    file_repo_map: Dict[str, List[str]] = {}
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file == os.path.basename(__file__):
                continue  # Skip the parser script itself
            #skip hidden files , especially .git
            if file.startswith('.'):
                continue
            
            file_path = os.path.join(root, file)
            try:
                tags = list_tags_in_file(file_path, tag_to_repo)
            except Exception as e:  # binary files or read errors
                print(f"[!] Error processing {file_path}: {e}")
                continue
            target_repos = set()
            for tag in tags:
                if tag in tag_to_repo:
                    target_repos.update(tag_to_repo[tag])
            if target_repos:
                file_repo_map[file_path] = sorted(target_repos)
    return file_repo_map

# -----------------------------------------------------------
# 3. CLI / Debug Entry Point
# -----------------------------------------------------------
if __name__ == "__main__":
    repos, tag_to_repo = parse_tag_map()

    print("Repositories:")
    for r, url in repos.items():
        print(f"  {r}: {url}")

    print("\nTag → Repo mapping:")
    for tag, repos in tag_to_repo.items():
        print(f"  {tag}: {repos}")

