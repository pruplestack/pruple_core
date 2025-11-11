# tagmap_parser.py
import os
import re
import yaml
from typing import Dict, List, Set

# -----------------------------------------------------------
# 1. YAML Parsing
# -----------------------------------------------------------

def parse_tag_map(
    path: str = os.path.join(os.path.dirname(__file__), "../config/tag_map.yaml")
) -> tuple[Dict[str, str], Dict[str, List[str]]]:
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
                tag_to_repo.setdefault(tag.lower(), []).append(repo_alias)

    return repos, tag_to_repo


# -----------------------------------------------------------
# 2. File Tag Utilities (Obsidian-compatible)
# -----------------------------------------------------------

# Valid Obsidian tag pattern: #tag or #parent/child/subchild
# Letters, digits, underscores, hyphens, and forward slashes are allowed.
TAG_PATTERN = re.compile(r"#([A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*)\b")

def _is_valid_obsidian_tag(tag: str) -> bool:
    """
    Ensure tag contains at least one non-digit character (per Obsidian rules).
    """
    return bool(re.search(r"[A-Za-z_/-]", tag))


def file_has_tag(file_path: str, tag: str) -> bool:
    """
    Return True if a file contains the given #tag (Obsidian style).
    Case-insensitive, supports nested tags (#tag/child).
    """
    if not os.path.isfile(file_path):
        print(f"[!] File not found: {file_path}")
        return False
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        for match in TAG_PATTERN.finditer(content):
            found_tag = match.group(1)
            if not _is_valid_obsidian_tag(found_tag):
                continue
            # Normalize both sides
            found_tag_lower = found_tag.lower()
            tag_lower = tag.lower()
            if found_tag_lower == tag_lower or found_tag_lower.startswith(tag_lower + "/"):
                return True
        return False
    except Exception as e:
        print(f"[!] Error reading {file_path}: {e}")
        return False


def list_tags_in_file(file_path: str, known_tags: Dict[str, List[str]]) -> List[str]:
    """
    Extract all Obsidian-style tags from file that exist in the provided tag map.
    Matches nested tags (#parent/child) as belonging to the parent if applicable.
    """
    if not os.path.isfile(file_path):
        print(f"[!] File not found: {file_path}")
        return []

    found: Set[str] = set()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        for match in TAG_PATTERN.finditer(content):
            tag = match.group(1)
            if not _is_valid_obsidian_tag(tag):
                continue
            tag_norm = tag.lower()
            # Match both exact and nested parent tags
            for known in known_tags:
                known_norm = known.lower()
                if tag_norm == known_norm or tag_norm.startswith(known_norm + "/"):
                    found.add(known)
    except Exception as e:
        print(f"[!] Error reading {file_path}: {e}")
    return sorted(found)


def build_file_repo_dict_map(base_dir: str, tag_to_repo: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    Scan all files in base_dir and map each file to the list of repositories
    it should be included in based on its Obsidian-style tags.
    """
    file_repo_map: Dict[str, List[str]] = {}
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file == os.path.basename(__file__):
                continue  # Skip this parser
            if file.startswith('.'):
                continue  # Skip hidden files
            if '.git' in root.split(os.sep):
                continue  # Skip git dirs
            if not file.lower().endswith((
                '.txt', '.md', '.py', '.yaml', '.yml', '.json',
                '.cfg', '.ini', '.csv', '.log', '.xml', '.html', '.htm', '.js', '.css'
            )):
                continue  # Skip binaries
            file_path = os.path.join(root, file)
            try:
                tags = list_tags_in_file(file_path, tag_to_repo)
            except Exception as e:
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

    # Example: Build file to repo map for current directory
    file_repo_map = build_file_repo_dict_map(".", tag_to_repo)
    print("\nFile → Repo mapping:")
    for file, repos in file_repo_map.items():
        print(f"  {file}: {repos}")
