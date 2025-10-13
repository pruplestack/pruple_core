# tagmap_parser.py
import os
import yaml
from collections import defaultdict

def find_and_parse_tagmap(file_path: str = str(os.path.join(os.path.dirname(__file__), "tag_map.yaml"))) -> dict | None:
    """
    Locate and parse a YAML tag map file.

    Parameters
    ----------
    file_path : str
        Path to the tag map YAML file (default: 'tag_map.yaml').

    Returns
    -------
    dict or None
        Parsed YAML data as a Python dictionary, or None if not found / invalid.
    """
    if not os.path.isfile(file_path):
        print(f"[!] File not found: {file_path}")
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data: dict = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"[!] YAML parsing error in {file_path}: {e}")
        return None
    except Exception as e:
        print(f"[!] Unexpected error reading {file_path}: {e}")
        return None

    if not isinstance(data, dict):
        print(f"[!] Invalid format: expected mapping at root of {file_path}")
        return None

    return data


def build_tag_to_repo_map(raw_data: dict) -> dict[str, list[str]]:
    """
    Build a mapping of tag -> [repos] from repo -> [tags].

    Parameters
    ----------
    raw_data : dict
        The parsed YAML data containing a 'tag_map' section.

    Returns
    -------
    dict[str, list[str]]
        Inverted mapping from tags to the list of repositories that use them.
    """
    repo_map = raw_data.get("tag_map", raw_data)  # fallback if no 'tag_map' key
    tag_to_repos = defaultdict(list)

    if isinstance(repo_map, list):
        # handle the case where YAML was loaded as list of strings (bad formatting)
        for entry in repo_map:
            try:
                repo, taglist_str = entry.split(":", 1)
                tags = yaml.safe_load(taglist_str)
                for tag in tags:
                    tag_to_repos[tag].append(repo.strip())
            except Exception as e:
                print(f"[!] Could not parse entry {entry}: {e}")
    elif isinstance(repo_map, dict):
        for repo, tags in repo_map.items():
            if not isinstance(tags, (list, tuple)):
                print(f"[!] Skipping malformed tag list for {repo}: {tags}")
                continue
            for tag in tags:
                tag_to_repos[tag].append(repo)
    else:
        print("[!] tag_map has invalid type:", type(repo_map))

    return dict(tag_to_repos)


if __name__ == "__main__":
    tagmap = find_and_parse_tagmap()
    if not tagmap:
        exit(1)

    tag_to_repo = build_tag_to_repo_map(tagmap)
    print("Tag → Repo mapping:")
    for tag, repos in tag_to_repo.items():
        print(f"  {tag}: {repos}")
