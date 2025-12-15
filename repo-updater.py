import os
import subprocess


# Repos that should NOT be pushed to (they can still be fetched/pulled)
REPOS_TO_NOT_PUSH = {
    "Curso-Aprendizaje-de-Maquinas",
    "mds_dsproject_classes_notes",
    "CEC",
    "imperial-segmentacion-de-clientes",
    "cpsc330-2025W1",
    "AppliedMachineLearning_Project_3",
}

# Directories to skip while walking
SKIP_DIR_PREFIXES = ("tarea-0",)
SKIP_DIR_NAMES = {"cc5905"}  # kept for your “memes purposes” comment

# Files that should NOT be ignored by update_gitignore()
KEEP_FILES = {"README.md", "README.template.md", ".gitignore"}


def run_git(repo_path: str, args: list[str], capture: bool = False) -> str:
    """Run a git command in repo_path. If capture=True, returns stdout (str)."""
    if capture:
        return subprocess.check_output(["git", *args], cwd=repo_path).decode("utf-8", errors="replace")
    subprocess.run(["git", *args], cwd=repo_path, check=True)
    return ""


def base_directory() -> str:
    """Directory containing this script file."""
    return os.path.dirname(os.path.abspath(__file__))


def update_gitignore() -> None:
    """
    Update the .gitignore file in the script directory with all files and directories
    except the script file and READMEs.
    """
    current_dir = base_directory()
    script_name = os.path.basename(__file__)
    gitignore_path = os.path.join(current_dir, ".gitignore")

    keep = set(KEEP_FILES)
    keep.add(script_name)

    # Read existing .gitignore entries (if present)
    gitignore_entries: set[str] = set()
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as f:
            gitignore_entries = set(line.rstrip("\n") for line in f)

    # List all items in the script directory
    items = os.listdir(current_dir)

    new_entries: set[str] = set()
    for item in items:
        if item in keep:
            continue

        full_path = os.path.join(current_dir, item)
        item_entry = f"{item}/" if os.path.isdir(full_path) else item

        if item_entry not in gitignore_entries:
            new_entries.add(item_entry)

    if new_entries:
        with open(gitignore_path, "a", encoding="utf-8") as f:
            for entry in sorted(new_entries):
                f.write(f"{entry}\n")
        print(f"Added {len(new_entries)} new entries to .gitignore.")
    else:
        print("No new entries to add to .gitignore.")


def is_git_repo(path: str) -> bool:
    """Check if a directory is a Git repository."""
    return os.path.isdir(os.path.join(path, ".git"))


def has_upstream(repo_path: str) -> bool:
    """Check if the current branch has an upstream branch set."""
    try:
        run_git(repo_path, ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], capture=True)
        return True
    except subprocess.CalledProcessError:
        return False


def working_tree_dirty(repo_path: str) -> bool:
    """
    Detect any local changes (staged, unstaged, untracked) in a language-independent way.
    """
    out = run_git(repo_path, ["status", "--porcelain"], capture=True)
    return bool(out.strip())


def ahead_behind(repo_path: str) -> tuple[bool, bool]:
    """
    Return (ahead, behind) relative to upstream.
    """
    out = run_git(repo_path, ["rev-list", "HEAD...@{u}", "--left-right"], capture=True)
    ahead = False
    behind = False
    for line in out.splitlines():
        if line.startswith("<"):
            ahead = True
        elif line.startswith(">"):
            behind = True
    return ahead, behind


def safe_repo_label(repo_path: str, base_dir: str) -> str:
    """
    Human-friendly repo identifier: relative path from base_dir when possible.
    """
    try:
        rel = os.path.relpath(repo_path, base_dir)
        return rel if rel and rel != "." else repo_path
    except Exception:
        return repo_path


def check_status(repo_path: str, base_dir: str) -> None:
    """
    Fetch changes, then:
      - if diverged: tell user manual update required
      - if behind: pull
      - if ahead: push (unless protected)
      - if working tree dirty: add/commit/push (unless protected)
    """
    label = safe_repo_label(repo_path, base_dir)

    try:
        print(f"Fetching and checking status in {label}...")
        run_git(repo_path, ["fetch"])

        if not has_upstream(repo_path):
            print(f"Repository '{label}' does not have an upstream branch set.")
            return

        ahead, behind = ahead_behind(repo_path)
        dirty = working_tree_dirty(repo_path)
        protected = (os.path.basename(repo_path) in REPOS_TO_NOT_PUSH) or (label in REPOS_TO_NOT_PUSH)

        if ahead and behind:
            print(f"Repository '{label}' has diverged from the remote. Manual update required.")
            return

        if behind:
            print(f"Repository '{label}' is behind the remote. Pulling updates...")
            run_git(repo_path, ["pull"])
            # After pulling, refresh state
            ahead, behind = ahead_behind(repo_path)
            dirty = working_tree_dirty(repo_path)

        if dirty:
            if protected:
                print(f"Repository '{label}' has local changes but is marked as no-push. Skipping commit/push.")
                return

            run_git(repo_path, ["add", "."])
            commit_message = input(f"Commit message for repo {label}: ").strip()
            if not commit_message:
                commit_message = "automatic commit message"
            run_git(repo_path, ["commit", "-m", commit_message])
            print(f"Pushing committed changes for '{label}'...")
            run_git(repo_path, ["push"])
            return

        if ahead:
            if protected:
                print(f"Repository '{label}' is ahead of the remote but is marked as no-push. Skipping push.")
                return
            print(f"Repository '{label}' is ahead of the remote. Pushing updates...")
            run_git(repo_path, ["push"])
            return

        print(f"No changes detected in {label}.")

    except subprocess.CalledProcessError as e:
        print(f"Failed to fetch/pull in {label}: {e}")


def update_directories(base_dir: str) -> None:
    """Recursively scan for Git repositories and update them."""
    for root, dirs, _ in os.walk(base_dir):
        # In-place filter of dirs to prevent walking into skipped folders
        dirs[:] = [
            d for d in dirs
            if (not d.startswith(SKIP_DIR_PREFIXES)) and (d not in SKIP_DIR_NAMES)
        ]

        for d in dirs:
            dir_path = os.path.join(root, d)
            if is_git_repo(dir_path):
                check_status(dir_path, base_dir)


if __name__ == "__main__":
    BASE_DIR = base_directory()
    update_gitignore()
    update_directories(BASE_DIR)
