#!/usr/bin/env python3
"""
Claude Login Manager の基本的なテスト

このテストは、ClaudeLoginManagerクラスの基本的な機能をテストします。
実際のログインはテストしませんが、クラスの初期化とメソッドの存在を確認します。
"""

import sys
import os
import tempfile
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.claude_login import ClaudeLoginManager


def test_initialization():
    """ClaudeLoginManagerの初期化テスト"""
    print("=" * 70)
    print("Test: ClaudeLoginManager Initialization")
    print("=" * 70)

    # カスタムセッションディレクトリを指定
    with tempfile.TemporaryDirectory() as tmpdir:
        session_dir = os.path.join(tmpdir, "test_session")

        # インスタンス作成
        manager = ClaudeLoginManager(
            session_dir=session_dir,
            proxy_port=8901,
            headless=True
        )

        # 基本的なプロパティを確認
        assert manager.session_dir == session_dir, "Session dir mismatch"
        assert manager.proxy_port == 8901, "Proxy port mismatch"
        assert manager.headless is True, "Headless mode mismatch"

        # ディレクトリが作成されているか確認
        assert os.path.exists(session_dir), "Session directory not created"
        assert os.path.exists(manager.cache_dir), "Cache directory not created"

        print(f"✅ Session dir: {manager.session_dir}")
        print(f"✅ Cache dir: {manager.cache_dir}")
        print(f"✅ Proxy port: {manager.proxy_port}")
        print(f"✅ Headless: {manager.headless}")

    print("\n✅ Test passed: Initialization")
    return True


def test_chromium_args():
    """Chromium引数のテスト"""
    print("\n" + "=" * 70)
    print("Test: Chromium Arguments")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ClaudeLoginManager(session_dir=os.path.join(tmpdir, "test_session"))

        # Chromium引数を取得
        args = manager._get_chromium_args()

        # 必須の引数が含まれているか確認
        required_args = [
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--single-process',
        ]

        for required_arg in required_args:
            assert required_arg in args, f"Missing required arg: {required_arg}"
            print(f"✅ Found: {required_arg}")

        # プロキシ設定が含まれているか確認
        proxy_arg = f'--proxy-server=http://127.0.0.1:{manager.proxy_port}'
        assert proxy_arg in args, f"Missing proxy arg: {proxy_arg}"
        print(f"✅ Found: {proxy_arg}")

    print("\n✅ Test passed: Chromium Arguments")
    return True


def test_methods_exist():
    """メソッドの存在確認テスト"""
    print("\n" + "=" * 70)
    print("Test: Methods Existence")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ClaudeLoginManager(session_dir=os.path.join(tmpdir, "test_session"))

        # 必須メソッドの存在確認
        required_methods = [
            'start_proxy',
            'stop_proxy',
            'create_browser_context',
            'wait_for_cloudflare_challenge',
            'is_logged_in',
            'access_claude_code',
            '_get_chromium_args',
            '_inject_anti_detection_scripts',
        ]

        for method_name in required_methods:
            assert hasattr(manager, method_name), f"Missing method: {method_name}"
            assert callable(getattr(manager, method_name)), f"Not callable: {method_name}"
            print(f"✅ Method exists: {method_name}")

    print("\n✅ Test passed: Methods Existence")
    return True


def test_default_session_dir():
    """デフォルトセッションディレクトリのテスト"""
    print("\n" + "=" * 70)
    print("Test: Default Session Directory")
    print("=" * 70)

    # デフォルトのセッションディレクトリを使用
    manager = ClaudeLoginManager()

    # ~/.kagami/claude_session が使用されているか確認
    home = Path.home()
    expected_session_dir = str(home / ".kagami" / "claude_session")
    expected_cache_dir = str(home / ".kagami" / "claude_cache")

    assert manager.session_dir == expected_session_dir, "Default session dir mismatch"
    assert manager.cache_dir == expected_cache_dir, "Default cache dir mismatch"

    print(f"✅ Default session dir: {manager.session_dir}")
    print(f"✅ Default cache dir: {manager.cache_dir}")

    # ディレクトリが作成されているか確認
    assert os.path.exists(manager.session_dir), "Default session directory not created"
    assert os.path.exists(manager.cache_dir), "Default cache directory not created"

    print("\n✅ Test passed: Default Session Directory")
    return True


def main():
    """テストを実行"""
    print("\n" + "=" * 70)
    print("Claude Login Manager - Basic Tests")
    print("=" * 70)
    print()

    tests = [
        test_initialization,
        test_chromium_args,
        test_methods_exist,
        test_default_session_dir,
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append((test_func.__name__, result))
        except Exception as e:
            print(f"\n❌ Test failed: {test_func.__name__}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_func.__name__, False))

    # 結果サマリー
    print("\n" + "=" * 70)
    print("Test Results Summary")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {status}: {test_name}")

    print("\n" + "=" * 70)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 70)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
