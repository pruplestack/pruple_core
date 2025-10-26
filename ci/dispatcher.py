# dispatcher.py

import os
import subprocess
import shutil
import sys
from typing import Dict, List

from parser import parse_tag_map, build_file_repo_dict_map
from ghutils import create_if_not_exists, ensure_pruple_managed, push_mirror


def create_local_repo(repo_name: str):
    """Initialize / ensure local folder contains a git repository."""
    if not os.path.exists(repo_name):
        os.makedirs(repo_name)

    # initialize git repo if not present
    if not os.path.exists(os.path.join(repo_name, ".git")):
        subprocess.run(["git", "init"], cwd=repo_name, check=True)

    return repo_name


def fill_repo(repo_name: str, file_repo_map: Dict[str, List[str]], vault_root: str = "."):
    """Replace repo contents (except .git/) with the tagged files."""
    repo_path = os.path.abspath(repo_name)

    # wipe working tree except .git
    for item in os.listdir(repo_path):
        full = os.path.join(repo_path, item)
        if item == ".git":
            continue
        if os.path.isfile(full):
            os.remove(full)
        else:
            shutil.rmtree(full)

    # copy files belonging to this repo
    copied_files = 0
    for file_path, repos in file_repo_map.items():
        if repo_name in repos:
            src = os.path.join(vault_root, file_path)
            dest = os.path.join(repo_path, file_path)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(src, dest)
            copied_files += 1

    # stage + commit
    subprocess.run(["git", "add", "-A"], cwd=repo_path, check=False)
    subprocess.run(["git", "commit", "-m", "Automated dispatch update"], cwd=repo_path, check=False)

    print(f"[i] {repo_name}: {copied_files} files included.")


def dispatch(vault_root: str = "."):
    # Load tag mappings
    repos, tag_to_repo = parse_tag_map()
    file_repo_map = build_file_repo_dict_map(vault_root, tag_to_repo)

    print(f"[i] Managing {len(repos)} repositories.")

    for alias, remote_repo in repos.items():
        print(f"\n[>] Processing {alias} ({remote_repo})")

        # local repo folder name = alias
        local_repo = create_local_repo(alias)

        # ensure remote repo exists and is PRUPLE-managed
        create_if_not_exists(remote_repo)
        ensure_pruple_managed(remote_repo)

        # fill local repo contents
        fill_repo(local_repo, file_repo_map, vault_root=vault_root)

        # push mirror to remote
        print(f"[>] Pushing mirror...")
        push_mirror(local_repo, remote_repo)

        print(f"[✓] {alias} synchronized.")


if __name__ == "__main__":
    dispatch()
