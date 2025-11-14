#!/usr/bin/env python3
"""
Claude Cookie Manager のテスト

このテストは、ClaudeCookieManagerクラスの基本的な機能をテストします。
暗号化、保存、読み込み、復号化の各機能を確認します。
"""

import sys
import os
import tempfile
import json
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.claude_cookie_manager import ClaudeCookieManager


def test_initialization():
    """ClaudeCookieManagerの初期化テスト"""
    print("=" * 70)
    print("Test: ClaudeCookieManager Initialization")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = os.path.join(tmpdir, "test_cookies.enc")
        encryption_key = "test_encryption_key_12345"

        # インスタンス作成
        manager = ClaudeCookieManager(
            storage_path=storage_path,
            encryption_key=encryption_key
        )

        # 基本的なプロパティを確認
        assert manager.storage_path == storage_path, "Storage path mismatch"
        assert manager.encryption_key == encryption_key, "Encryption key mismatch"

        print(f"✅ Storage path: {manager.storage_path}")
        print(f"✅ Encryption key: {manager.encryption_key[:20]}...")

    print("\n✅ Test passed: Initialization")
    return True


def test_cookie_encryption_and_decryption():
    """Cookie暗号化と復号化のテスト"""
    print("\n" + "=" * 70)
    print("Test: Cookie Encryption and Decryption")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = os.path.join(tmpdir, "test_cookies.enc")
        encryption_key = "test_encryption_key_12345"

        manager = ClaudeCookieManager(
            storage_path=storage_path,
            encryption_key=encryption_key
        )

        # テスト用のCookieデータ
        test_cookies = [
            {
                'name': 'session_id',
                'value': 'abc123def456',
                'domain': '.claude.ai',
                'path': '/',
                'expires': 1234567890,
                'httpOnly': True,
                'secure': True,
                'sameSite': 'Lax'
            },
            {
                'name': 'user_token',
                'value': 'token_xyz789',
                'domain': '.claude.ai',
                'path': '/',
                'expires': 9876543210,
                'httpOnly': False,
                'secure': True,
                'sameSite': 'Strict'
            }
        ]

        # Cookieを保存
        print("\n[1] Saving cookies...")
        manager.save_cookies(test_cookies, storage_path)

        # ファイルが作成されているか確認
        assert os.path.exists(storage_path), "Cookie file not created"
        print(f"✅ Cookie file created: {storage_path}")

        # Cookieを読み込み
        print("\n[2] Loading cookies...")
        loaded_cookies = manager.load_cookies(storage_path)

        # Cookieが正しく復号化されているか確認
        assert len(loaded_cookies) == len(test_cookies), "Cookie count mismatch"
        print(f"✅ Loaded {len(loaded_cookies)} cookies")

        # 各Cookieの内容を確認
        for i, (original, loaded) in enumerate(zip(test_cookies, loaded_cookies)):
            assert original['name'] == loaded['name'], f"Cookie {i} name mismatch"
            assert original['value'] == loaded['value'], f"Cookie {i} value mismatch"
            assert original['domain'] == loaded['domain'], f"Cookie {i} domain mismatch"
            print(f"✅ Cookie {i+1}: {original['name']} = {original['value']}")

    print("\n✅ Test passed: Encryption and Decryption")
    return True


def test_wrong_encryption_key():
    """間違った暗号化キーでの復号化テスト"""
    print("\n" + "=" * 70)
    print("Test: Wrong Encryption Key")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = os.path.join(tmpdir, "test_cookies.enc")

        # Cookieを保存（キー1）
        manager1 = ClaudeCookieManager(
            storage_path=storage_path,
            encryption_key="correct_key_123"
        )

        test_cookies = [
            {'name': 'test_cookie', 'value': 'test_value', 'domain': '.example.com'}
        ]

        manager1.save_cookies(test_cookies, storage_path)
        print("✅ Cookies saved with key 1")

        # 間違ったキーで読み込み（キー2）
        manager2 = ClaudeCookieManager(
            storage_path=storage_path,
            encryption_key="wrong_key_456"
        )

        try:
            manager2.load_cookies(storage_path)
            print("❌ Should have failed with wrong key")
            return False
        except Exception as e:
            print(f"✅ Correctly failed with wrong key: {str(e)[:50]}...")

    print("\n✅ Test passed: Wrong Encryption Key")
    return True


def test_cookie_info():
    """Cookie情報取得のテスト"""
    print("\n" + "=" * 70)
    print("Test: Cookie Info")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ClaudeCookieManager(
            storage_path=os.path.join(tmpdir, "test.enc"),
            encryption_key="test_key"
        )

        # テスト用のCookieデータ
        test_cookies = [
            {'name': 'cookie1', 'domain': '.claude.ai'},
            {'name': 'cookie2', 'domain': '.claude.ai'},
            {'name': 'cookie3', 'domain': '.anthropic.com'},
        ]

        # Cookie情報を取得
        info = manager.get_cookie_info(test_cookies)

        assert info['count'] == 3, "Cookie count mismatch"
        assert '.claude.ai' in info['domains'], "Domain not found"
        assert '.anthropic.com' in info['domains'], "Domain not found"
        assert 'cookie1' in info['names'], "Cookie name not found"

        print(f"✅ Cookie count: {info['count']}")
        print(f"✅ Domains: {info['domains']}")
        print(f"✅ Names: {info['names']}")

        # Cookie情報を表示
        manager.print_cookie_info(test_cookies)

    print("\n✅ Test passed: Cookie Info")
    return True


def test_cookies_exist():
    """Cookieファイル存在確認のテスト"""
    print("\n" + "=" * 70)
    print("Test: Cookies Exist")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = os.path.join(tmpdir, "test_cookies.enc")

        manager = ClaudeCookieManager(
            storage_path=storage_path,
            encryption_key="test_key"
        )

        # 最初は存在しない
        assert not manager.cookies_exist(), "Cookies should not exist"
        print("✅ Cookies do not exist (initial)")

        # Cookieを保存
        test_cookies = [{'name': 'test', 'value': 'value'}]
        manager.save_cookies(test_cookies)

        # 保存後は存在する
        assert manager.cookies_exist(), "Cookies should exist"
        print("✅ Cookies exist after saving")

        # Cookieを削除
        manager.delete_cookies()

        # 削除後は存在しない
        assert not manager.cookies_exist(), "Cookies should not exist after deletion"
        print("✅ Cookies do not exist after deletion")

    print("\n✅ Test passed: Cookies Exist")
    return True


def main():
    """テストを実行"""
    print("\n" + "=" * 70)
    print("Claude Cookie Manager - Tests")
    print("=" * 70)
    print()

    tests = [
        test_initialization,
        test_cookie_encryption_and_decryption,
        test_wrong_encryption_key,
        test_cookie_info,
        test_cookies_exist,
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
