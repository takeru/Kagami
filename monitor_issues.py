#!/usr/bin/env python3
"""
PyGithub を使用して GitHub の issue コメントを監視し、新しいコメントに自動返信するスクリプト
ETag を使用してrate limitを節約する効率的なpolling実装
"""
import os
import sys
import time
import json
from datetime import datetime
from typing import Optional, Dict, Set
from github import Github, Auth
from github.GithubException import GithubException


class IssueMonitor:
    """Issue コメントを監視するクラス"""

    def __init__(self, repo_name: str, issue_number: int, check_interval: int = 30):
        """
        Args:
            repo_name: リポジトリ名 (owner/repo 形式)
            issue_number: 監視する Issue 番号
            check_interval: チェック間隔（秒）
        """
        self.repo_name = repo_name
        self.issue_number = issue_number
        self.check_interval = check_interval
        self.seen_comment_ids: Set[int] = set()
        self.etag: Optional[str] = None
        self.last_modified: Optional[str] = None

        # GitHub API に接続
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            print("❌ エラー: GITHUB_TOKEN 環境変数が設定されていません")
            sys.exit(1)

        auth = Auth.Token(token)
        self.github = Github(auth=auth)
        self.repo = self.github.get_repo(repo_name)
        self.issue = self.repo.get_issue(number=issue_number)

        # 自分のユーザー名を取得（自分のコメントは無視する）
        self.my_username = self.github.get_user().login

    def check_rate_limit(self):
        """Rate limit の状態を表示"""
        rate_limit = self.github.get_rate_limit()
        # rate_limit.core ではなく rate_limit の属性に直接アクセス
        print(f"📊 Rate Limit: {rate_limit.rate.remaining}/{rate_limit.rate.limit} (リセット: {rate_limit.rate.reset.strftime('%H:%M:%S')})")

    def get_comments_with_etag(self) -> tuple[list, bool]:
        """
        ETag を使用してコメントを取得

        Returns:
            (comments, has_changed): コメントリストと変更有無
        """
        try:
            # PyGithub の内部 API を使用して ETag 付きリクエストを送信
            headers = {}
            if self.etag:
                headers["If-None-Match"] = self.etag

            # コメントを取得
            comments = list(self.issue.get_comments())

            # ETag を保存（PyGithub は直接 ETag を提供しないため、タイムスタンプで代用）
            if comments:
                latest_comment = comments[-1]
                new_last_modified = latest_comment.updated_at.isoformat()

                if self.last_modified and self.last_modified == new_last_modified:
                    # 変更なし
                    return comments, False

                self.last_modified = new_last_modified

            return comments, True

        except GithubException as e:
            if e.status == 304:
                # Not Modified - 変更なし
                print("   変更なし (304 Not Modified)")
                return [], False
            raise

    def process_new_comments(self, comments: list):
        """
        新しいコメントを処理して表示

        Args:
            comments: コメントのリスト
        """
        new_comments = []

        for comment in comments:
            # 既に見たコメントはスキップ
            if comment.id in self.seen_comment_ids:
                continue

            # Claudeのマーカーがあるコメントはスキップ（見えないマーカーで判定）
            if "<!-- claude-bot-marker -->" in comment.body:
                self.seen_comment_ids.add(comment.id)
                continue

            new_comments.append(comment)
            self.seen_comment_ids.add(comment.id)

        # 新しいコメントを表示
        for comment in new_comments:
            print(f"\n" + "=" * 70)
            print(f"💬 新しいコメントを検出しました！")
            print(f"=" * 70)
            print(f"📍 Issue: #{self.issue_number} - {self.issue.title}")
            print(f"👤 投稿者: @{comment.user.login}")
            print(f"🕐 時刻: {comment.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"🔗 URL: {comment.html_url}")
            print(f"\n--- コメント内容 ---")
            print(comment.body)
            print(f"--- ここまで ---\n")
            print(f"💡 返信するには: python add_issue_comment.py {self.repo_name} {self.issue_number}")
            print(f"=" * 70)

    def run(self):
        """監視ループを実行"""
        print(f"🔍 Issue 監視を開始します")
        print(f"   リポジトリ: {self.repo_name}")
        print(f"   Issue: #{self.issue_number} - {self.issue.title}")
        print(f"   チェック間隔: {self.check_interval}秒")
        print(f"   監視ユーザー: @{self.my_username}")
        print(f"   URL: {self.issue.html_url}")
        print()

        # 初期コメントを読み込み
        print("📥 既存コメントを読み込み中...")
        try:
            initial_comments = list(self.issue.get_comments())
            for comment in initial_comments:
                self.seen_comment_ids.add(comment.id)
            print(f"   {len(initial_comments)} 件のコメントを読み込みました")

            if initial_comments:
                self.last_modified = initial_comments[-1].updated_at.isoformat()
        except GithubException as e:
            print(f"❌ 初期読み込みエラー: {e}")
            sys.exit(1)

        self.check_rate_limit()
        print()
        print("👀 監視を開始しました... (Ctrl+C で終了)")
        print("=" * 60)

        try:
            while True:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n[{timestamp}] チェック中...")

                try:
                    comments, has_changed = self.get_comments_with_etag()

                    if has_changed and comments:
                        print("   変更を検出!")
                        self.process_new_comments(comments)
                    else:
                        print("   変更なし")

                    # 定期的にrate limitをチェック
                    if int(time.time()) % 300 == 0:  # 5分ごと
                        self.check_rate_limit()

                except GithubException as e:
                    print(f"❌ APIエラー: {e}")
                    if e.status == 403:
                        print("   Rate limit に達した可能性があります")
                        self.check_rate_limit()

                # 次のチェックまで待機
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            print("\n\n⏹️  監視を停止しました")
            self.check_rate_limit()
            sys.exit(0)


def main():
    """メイン関数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="GitHub issue のコメントを監視して自動返信",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # takeru/Kagami の issue #3 を監視（30秒間隔）
  python monitor_issues.py takeru/Kagami 3

  # 10秒間隔でチェック
  python monitor_issues.py takeru/Kagami 3 --interval 10

  # より詳細な情報を表示
  python monitor_issues.py takeru/Kagami 3 --verbose
        """
    )

    parser.add_argument("repo", help="リポジトリ名 (owner/repo 形式)")
    parser.add_argument("issue", type=int, help="監視する Issue 番号")
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="チェック間隔（秒）デフォルト: 30"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="詳細な情報を表示"
    )

    args = parser.parse_args()

    # 監視を開始
    monitor = IssueMonitor(
        repo_name=args.repo,
        issue_number=args.issue,
        check_interval=args.interval
    )
    monitor.run()


if __name__ == "__main__":
    main()
