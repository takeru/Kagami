#!/usr/bin/env python3
"""PR #21の情報を取得"""
import os
from github import Github

def main():
    g = Github(os.getenv("GITHUB_TOKEN"))
    repo = g.get_repo("takeru/Kagami")

    pr = repo.get_pull(21)

    print(f"Title: {pr.title}")
    print(f"\nBody:\n{pr.body}")
    print(f"\nState: {pr.state}")
    print(f"\nMerged: {pr.merged}")
    print(f"\nBase branch: {pr.base.ref}")
    print(f"\nHead branch: {pr.head.ref}")

    print("\n--- Files changed ---")
    for file in pr.get_files():
        print(f"  {file.filename}")

    print("\n--- Comments ---")
    for comment in pr.get_issue_comments():
        print(f"\n{comment.user.login} at {comment.created_at}:")
        print(comment.body)

if __name__ == "__main__":
    main()
