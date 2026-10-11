#!/usr/bin/env python3
"""Publish generated files without checking out or rewriting the source branch."""
import argparse
import os
from pathlib import Path
import subprocess


def git(*args, **kwargs):
    return subprocess.check_output(["git", *args], text=True, **kwargs).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    current = git("ls-remote", "origin", "refs/heads/main").split()[0]
    if current != args.revision:
        print("A newer main commit exists; retain the current catalog until its build completes.")
        return
    existing = git("ls-remote", "origin", "refs/heads/catalog").split()
    parents = []
    if existing:
        git("fetch", "--no-tags", "origin", "catalog")
        parents = ["-p", existing[0]]
    index = Path(os.environ["RUNNER_TEMP"]) / "facetra-catalog.index"
    index.unlink(missing_ok=True)
    env = dict(os.environ, GIT_INDEX_FILE=str(index))
    git("read-tree", "--empty", env=env)
    for path in sorted(args.output.iterdir()):
        if path.is_file():
            oid = git("hash-object", "-w", str(path))
            git("update-index", "--add", "--cacheinfo", f"100644,{oid},{path.name}", env=env)
    tree = git("write-tree", env=env)
    if existing and git("rev-parse", existing[0] + "^{tree}") == tree:
        print("Catalog is already current.")
        return
    git("config", "user.name", "github-actions[bot]")
    git("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    commit = git("commit-tree", tree, *parents, "-m", "chore: publish catalog for " + args.revision)
    git("push", "origin", commit + ":refs/heads/catalog")
    print("Published catalog for " + args.revision)


if __name__ == "__main__":
    main()
