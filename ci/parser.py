# tagmap_parser.py
import os
import yaml

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

if __name__ == "__main__":
    tagmap = find_and_parse_tagmap()
    if tagmap is not None:
        print("Parsed tag map:")
        print(tagmap)