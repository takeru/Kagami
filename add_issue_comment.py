#!/usr/bin/env python3
"""
PyGithub を使用して GitHub の issue に気の利いたコメントを追加するスクリプト
"""
import os
import sys
from github import Github, Auth
from github.GithubException import GithubException


def get_repo_info():
    """現在の git リポジトリから owner/repo を取得する"""
    import subprocess
    try:
        # git remote の URL を取得
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            check=True
        )
        remote_url = result.stdout.strip()

        # URL から owner/repo を抽出
        # 例: https://github.com/takeru/Kagami.git または git@github.com:takeru/Kagami.git
        if "github.com" in remote_url:
            if remote_url.startswith("https://"):
                # https://github.com/owner/repo.git
                parts = remote_url.replace("https://github.com/", "").replace(".git", "").split("/")
            elif remote_url.startswith("git@"):
                # git@github.com:owner/repo.git
                parts = remote_url.replace("git@github.com:", "").replace(".git", "").split("/")
            else:
                return None

            if len(parts) >= 2:
                return f"{parts[0]}/{parts[1]}"
    except subprocess.CalledProcessError:
        pass

    return None


def add_witty_comment_to_issue(repo_name: str, issue_number: int = None, custom_message: str = None):
    """
    指定された issue にコメントを追加する

    Args:
        repo_name: リポジトリ名 (owner/repo 形式)
        issue_number: Issue番号 (None の場合は最初のオープンissueを使用)
        custom_message: カスタムメッセージ (None の場合はデフォルトメッセージを使用)
    """
    # GitHub トークンを環境変数から取得
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("エラー: GITHUB_TOKEN 環境変数が設定されていません")
        sys.exit(1)

    # GitHub API に接続（新しい Auth API を使用）
    auth = Auth.Token(token)
    g = Github(auth=auth)

    try:
        # リポジトリを取得
        repo = g.get_repo(repo_name)
        print(f"📦 リポジトリ: {repo.full_name}")

        # Issue を取得
        if issue_number:
            issue = repo.get_issue(number=issue_number)
        else:
            # オープンな issue を取得
            issues = repo.get_issues(state="open")
            issues_list = list(issues[:5])  # 最初の5件を取得

            if not issues_list:
                print("オープンな issue が見つかりませんでした")
                return

            issue = issues_list[0]

        print(f"🎯 Issue #{issue.number}: {issue.title}")
        print(f"   URL: {issue.html_url}")

        # コメントテキストを決定
        if custom_message:
            comment_text = custom_message
            print(f"\n📝 カスタムメッセージを使用します")
        else:
            # 気の利いたコメントを作成
            witty_comments = [
                "🤖 Claude からこんにちは！\n\nこの issue について分析してみました。PyGithub を使って自動的にコメントを追加する機能をテストしています。\n\n何か具体的なサポートが必要な場合は、お知らせください！",
                "👋 自動化テストでお邪魔します！\n\nPyGithub の API 統合が正常に動作していることを確認しました。この issue に関して、何かお手伝いできることがあれば教えてください。\n\n素敵な一日を！✨",
                "🚀 GitHub API 統合テストを実行中...\n\nPyGithub を使用してこのコメントを自動的に追加しています。API が正常に動作していることを確認できました！\n\nこの issue の進捗を応援しています！📊"
            ]

            # ランダムにコメントを選択（issue番号を使ってシード）
            import random
            random.seed(issue.number)
            comment_text = random.choice(witty_comments)
            print(f"\n📝 デフォルトメッセージを使用します")

        # コメントを追加
        comment = issue.create_comment(comment_text)

        print(f"\n✅ コメントを追加しました!")
        print(f"   コメントURL: {comment.html_url}")

    except GithubException as e:
        print(f"❌ GitHub API エラー: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ エラー: {e}")
        sys.exit(1)


def main():
    """メイン関数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="GitHub issue にコメントを追加",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 現在のリポジトリの最初のオープン issue にコメント
  python add_issue_comment.py

  # 特定のリポジトリの issue にコメント
  python add_issue_comment.py takeru/Kagami 1

  # カスタムメッセージを指定
  python add_issue_comment.py takeru/Kagami 1 --message "こんにちは！"
        """
    )

    parser.add_argument("repo", nargs="?", help="リポジトリ名 (owner/repo 形式)")
    parser.add_argument("issue", nargs="?", type=int, help="Issue番号")
    parser.add_argument(
        "--message", "-m",
        help="カスタムメッセージ（指定しない場合はデフォルトメッセージ）"
    )

    args = parser.parse_args()

    # リポジトリ名の決定
    repo_name = args.repo
    if not repo_name:
        # git リポジトリから自動的に取得を試みる
        repo_name = get_repo_info()
        if not repo_name:
            parser.print_help()
            sys.exit(1)

    print(f"🔍 リポジトリ: {repo_name}")
    if args.issue:
        print(f"🔢 Issue番号: {args.issue}")
    else:
        print("🔢 最初のオープンissueを使用します")
    print()

    # コメントを追加
    add_witty_comment_to_issue(repo_name, args.issue, args.message)


if __name__ == "__main__":
    main()
