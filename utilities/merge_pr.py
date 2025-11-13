#!/usr/bin/env python3
"""
Pull Requestをマージするスクリプト
"""
import os
from github import Github

# GitHub API認証
g = Github(os.getenv("GITHUB_TOKEN"))
repo = g.get_repo("takeru/Kagami")

# PR #10を取得
pr = repo.get_pull(10)

print(f"PR #{pr.number}: {pr.title}")
print(f"Status: {pr.state}")
print(f"Mergeable: {pr.mergeable}")
print(f"URL: {pr.html_url}")

# マージ
if pr.state == "open":
    result = pr.merge(
        commit_title="Merge pull request #10: Add Playwright setup guide",
        commit_message="Add comprehensive Playwright setup guide and implementation",
        merge_method="merge"  # or "squash" or "rebase"
    )

    if result.merged:
        print(f"\n✅ PR #{pr.number} がマージされました！")
        print(f"   Merge commit: {result.sha}")
    else:
        print(f"\n❌ マージに失敗しました")
        print(f"   Message: {result.message}")
else:
    print(f"\n⚠️ PRは既に{pr.state}状態です")
