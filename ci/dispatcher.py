#dispatcher.py
#this program's purpose 
#is to use the tagmap utility
#to build a file->repo mapping 
#then build the content of each repo
#finally dispatch each file to its repo with --mirror
import os
import subprocess
from typing import Dict, List
import sys , shutil
from parser import file_has_tag, list_tags_in_file, parse_tag_map, build_file_repo_dict_map, build_tag_to_repo_map

# -----------------------------------------------------------
# for each repo : create a git repository with all the files taged for that repository in it 
def create_git_repo(url):
    #git init
    repo_name = url.split("/")[-1].replace(".git", "")
    if not os.path.exists(repo_name):
        os.makedirs(repo_name)
    subprocess.run(["git", "init"], cwd=repo_name)
    return repo_name
def fill_repo(repo_name: str, file_repo_map: Dict[str, List[str]], vault_root: str = "."):
    """
    Fill a local repository directory with files belonging to it based on file_repo_map.

    Parameters
    ----------
    repo_name : str
        Local folder name of the repository (should already contain a .git/ directory)
    file_repo_map : dict[str, list[str]]
        Mapping of vault-relative file paths to lists of repo aliases
    vault_root : str
        Path to the root of the main vault (default: current directory)
    """
    repo_path = os.path.abspath(repo_name)
    if not os.path.isdir(repo_path):
        print(f"[!] Repository folder {repo_name} not found.")
        return

    # 1. Clean repository except .git/
    for item in os.listdir(repo_path):
        full_path = os.path.join(repo_path, item)
        if item == ".git":
            continue
        if os.path.isfile(full_path):
            os.remove(full_path)
        else:
            shutil.rmtree(full_path)

    # 2. Copy files that belong to this repository
    copied_files = []
    for file_path, repos in file_repo_map.items():
        if repo_name in repos:
            src = os.path.join(vault_root, file_path)
            dest = os.path.join(repo_path, os.path.basename(file_path))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(src, dest)
            copied_files.append(file_path)

    # 3. Stage and commit changes
    subprocess.run(["git", "add", "-A"], cwd=repo_path)
    subprocess.run(["git", "commit", "-m", "Automated dispatch update"], cwd=repo_path)

    print(f"[i] {repo_name}: {len(copied_files)} files mirrored.")

def dispatch(vault_root: str = "."):
    """
    Orchestrate full dispatch process:
    - Parse tag_map.yaml to load repos and tag mappings
    - Build file -> repo mapping
    - Create local git repos (if missing)
    - Fill each repo with its relevant files
    - Push to remote (using --mirror)
    """

    # 1. Parse tag_map.yaml
    repos, tag_to_repo = parse_tag_map()
    if not repos:
        print("[!] No repositories found in tag_map.yaml. Exiting.")
        sys.exit(1)
    if not tag_to_repo:
        print("[!] No tag mappings found in tag_map.yaml. Exiting.")
        sys.exit(0)
    print(f"[i] Loaded {len(repos)} repos and {len(tag_to_repo)} tags from tag_map.yaml.")

    # 2. Build file->repo mapping
    print("[i] Building file-to-repo mapping...")
    file_repo_map = build_file_repo_dict_map(vault_root)
    print(f"[i] Found {len(file_repo_map)} tagged files.")

    # 3. Process each repo
    for alias, url in repos.items():
        print(f"\n[>] Processing {alias} ({url})")

        # Create local repo folder if needed
        local_repo = create_git_repo(url)

        # Fill repo with relevant files
        fill_repo(local_repo, file_repo_map, vault_root=vault_root)

        # 4. Push with --mirror
        print(f"[>] Pushing {alias} to remote...")
        subprocess.run(["git", "remote", "add", "origin", url], cwd=local_repo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "push", "--mirror", url], cwd=local_repo)
        print(f"[✓] {alias} updated successfully.")


if __name__=='__main__':
    dispatch()
