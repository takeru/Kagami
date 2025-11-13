#!/usr/bin/env python3
"""
Pull Requestを作成するスクリプト
"""
import os
from github import Github

# GitHub API認証
g = Github(os.getenv("GITHUB_TOKEN"))
repo = g.get_repo("takeru/Kagami")

# PR作成
pr = repo.create_pull(
    title="Add comprehensive Playwright setup guide and implementation",
    body="""## 📦 概要

まっさらな状態からPlaywrightがスムーズに使えるようになる完全なセットアップパッケージを実装しました。

## ✨ 主な追加内容

### セットアップパッケージ (`playwright_setup/`)
- **setup_playwright.py**: ワンコマンドセットアップスクリプト
- **proxy_manager.py**: バックグラウンドプロキシ管理ツール
- **README.md**: 完全な使い方ガイド（458行）
- **QUICKSTART.md**: 5分クイックスタート
- **TROUBLESHOOTING.md**: トラブルシューティング（450行）

### サンプルコード（6つ）
1. `01_basic_example.py`: 基本的な使い方
2. `02_with_proxy.py`: プロキシ経由アクセス ✅
3. `03_session_persistence.py`: セッション永続化
4. `04_cloudflare_bypass.py`: Cloudflare回避
5. `05_full_example.py`: 完全版（全機能統合）✅
6. `06_with_shared_proxy.py`: 共有プロキシ使用 ✅

### 調査・実装ファイル (`investigation/playwright/`)
- **SHARED_MEMORY_SOLUTION.md**: 共有メモリ問題の解決策
- **session_persistence_working.py**: セッション永続化の動作確認
- **test_claude_undetected.py**: Cloudflare回避テスト ✅
- **claude_automated_login.py**: claude.ai/code 自動ログイン実装
- その他多数のテストスクリプト

## 🎯 実装した機能

### Claude Code Web環境対応
- [x] 共有メモリ問題の解決 (`--disable-dev-shm-usage`)
- [x] プロセス分離の無効化 (`--single-process`)
- [x] JWT認証プロキシ対応 (proxy.py)
- [x] 証明書エラー回避

### 実用機能
- [x] プロキシ経由アクセス
- [x] セッション永続化
- [x] Cloudflare回避（Anti-detection）
- [x] バックグラウンドプロキシ管理
- [x] エラーハンドリング

## 📊 統計

- **追加ファイル**: 61ファイル
- **追加行数**: 7,647行
- **動作確認済みサンプル**: 3/6
- **ドキュメント**: 3ファイル（1,125行超）

## ✅ 動作確認

| サンプル | 状態 | 備考 |
|---------|------|------|
| 02_with_proxy.py | ✅ | Status 200, スクリーンショット保存 |
| 05_full_example.py | ✅ | 完全動作、全機能統合 |
| 06_with_shared_proxy.py | ✅ | 2秒以内で完了（3秒高速化） |
| proxy_manager.py | ✅ | start/stop/status/logs すべて動作 |

## 🚀 使い方

```bash
# 1. セットアップ（1分）
uv run python playwright_setup/setup_playwright.py

# 2. サンプル実行（1分）
uv run python playwright_setup/samples/02_with_proxy.py
```

## 🔗 関連Issue

Closes #7

## 📝 コミット履歴

- Add comprehensive Playwright setup guide and samples
- Add proxy manager for background proxy operation
- Add QUICKSTART guide for 5-minute setup
- Implement claude.ai/code automated login detection
- Add sample output screenshots and summary document
""",
    head="claude/playwright-chromium-persistence-011CV4qqFsKhe8DN7yoLL25A",
    base="main"
)

print(f"✅ Pull Request created: {pr.html_url}")
print(f"   Number: #{pr.number}")
print(f"   Title: {pr.title}")
