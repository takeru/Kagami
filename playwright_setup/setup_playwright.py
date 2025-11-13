#!/usr/bin/env python3
"""
Playwright セットアップスクリプト

Claude Code Web環境でPlaywrightをすぐに使えるようにセットアップします。
このスクリプト1つで全ての設定が完了します。

使い方:
    uv run python playwright_setup/setup_playwright.py
"""
import subprocess
import sys
import os
import tempfile
from pathlib import Path


def print_header(text):
    """ヘッダーを表示"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)


def run_command(cmd, description, check=True):
    """コマンドを実行して結果を表示"""
    print(f"\n▶ {description}")
    print(f"  $ {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=check
        )
        if result.stdout:
            print(f"  ✅ {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ❌ エラー: {e.stderr.strip() if e.stderr else str(e)}")
        return False


def main():
    print_header("Playwright セットアップ for Claude Code Web")

    # Step 1: 依存関係の確認
    print_header("Step 1: 依存関係の確認")

    # pyproject.toml に Playwright と proxy.py が含まれているか確認
    pyproject_path = Path("pyproject.toml")
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        has_playwright = "playwright" in content
        has_proxy = "proxy.py" in content

        print(f"  playwright: {'✅ 含まれています' if has_playwright else '❌ 未追加'}")
        print(f"  proxy.py: {'✅ 含まれています' if has_proxy else '❌ 未追加'}")

        if not has_playwright or not has_proxy:
            print("\n  ℹ️  pyproject.toml に以下を追加してください:")
            print('    dependencies = [')
            if not has_playwright:
                print('        "playwright>=1.56.0",')
            if not has_proxy:
                print('        "proxy.py>=2.4.0",')
            print('    ]')
    else:
        print("  ⚠️  pyproject.toml が見つかりません")

    # Step 2: Chromium のインストール
    print_header("Step 2: Chromium のインストール")

    success = run_command(
        ["uv", "run", "playwright", "install", "chromium"],
        "Chromium をインストール"
    )

    if not success:
        print("\n  ⚠️  Chromium のインストールに失敗しました")
        print("     手動で実行してください: uv run playwright install chromium")

    # Step 3: 環境変数の確認
    print_header("Step 3: 環境変数の確認")

    https_proxy = os.getenv("HTTPS_PROXY")
    if https_proxy:
        print(f"  ✅ HTTPS_PROXY: {https_proxy[:50]}...")
    else:
        print("  ⚠️  HTTPS_PROXY が設定されていません")
        print("     プロキシを使う場合は環境変数を設定してください")

    # Step 4: テストディレクトリの作成
    print_header("Step 4: サンプルコードの配置確認")

    setup_dir = Path("playwright_setup")
    samples_dir = setup_dir / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)

    print(f"  ✅ サンプルディレクトリ: {samples_dir}")

    # サンプルファイルの一覧
    sample_files = [
        "01_basic_example.py",
        "02_with_proxy.py",
        "03_session_persistence.py",
        "04_cloudflare_bypass.py",
        "05_full_example.py"
    ]

    existing_samples = []
    for sample in sample_files:
        if (samples_dir / sample).exists():
            existing_samples.append(sample)

    if existing_samples:
        print(f"  ✅ 既存サンプル: {len(existing_samples)}個")
        for sample in existing_samples:
            print(f"     - {sample}")
    else:
        print("  ℹ️  サンプルコードを作成します")

    # Step 5: 完了メッセージ
    print_header("セットアップ完了")

    print("""
次のステップ:

1. サンプルコードを実行:
   uv run python playwright_setup/samples/01_basic_example.py

2. プロキシ付きで実行:
   uv run python playwright_setup/samples/02_with_proxy.py

3. Cloudflare回避の例:
   uv run python playwright_setup/samples/04_cloudflare_bypass.py

詳細は README.md を参照してください:
   cat playwright_setup/README.md
""")


if __name__ == "__main__":
    main()
