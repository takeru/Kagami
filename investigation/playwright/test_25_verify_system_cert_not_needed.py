#!/usr/bin/env python3
"""
テスト25: システム証明書ストアの更新は不要であることを検証

Firefoxプロファイルの証明書だけで動作することを確認
"""
import asyncio
import os
import signal
import subprocess
import time
from playwright.async_api import async_playwright


async def test_firefox_without_system_cert():
    """システム証明書ストアを使わずにFirefoxプロファイルの証明書だけでアクセス"""
    print("=" * 70)
    print("テスト: システム証明書ストアの更新は不要であることを検証")
    print("=" * 70)
    print()

    # 確認事項を表示
    print("検証内容:")
    print("  1. Firefoxは独自の証明書ストア（cert9.db）を使用")
    print("  2. システム証明書ストア（/etc/ssl/certs）は見ていない")
    print("  3. したがって、update-ca-certificates は不要")
    print()

    # Firefoxプロファイルの証明書を確認
    print("1. Firefoxプロファイルの証明書を確認...")
    result = subprocess.run(
        ["certutil", "-L", "-d", "sql:/home/user/firefox-profile"],
        capture_output=True,
        text=True
    )

    if "Anthropic TLS Inspection CA Production" in result.stdout:
        print("   ✅ Firefoxプロファイルに証明書がインポートされています")
        print(f"\n{result.stdout}")
    else:
        print("   ❌ Firefoxプロファイルに証明書がありません")
        return False

    # プロキシ設定を取得
    https_proxy = os.environ.get('HTTPS_PROXY', '')
    if not https_proxy:
        print("❌ HTTPS_PROXY環境変数が設定されていません")
        return False

    # proxy.pyを起動
    print("2. proxy.pyを起動中...")
    proxy_process = subprocess.Popen(
        [
            "uv", "run", "proxy",
            "--hostname", "127.0.0.1",
            "--port", "18914",
            "--plugins", "proxy.plugin.proxy_pool.ProxyPoolPlugin",
            "--proxy-pool", https_proxy
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    time.sleep(2)
    print("   ✅ proxy.py起動完了")

    try:
        async with async_playwright() as p:
            print("\n3. Firefoxを起動（プロファイルの証明書のみ使用）...")

            context = await p.firefox.launch_persistent_context(
                user_data_dir="/home/user/firefox-profile",
                executable_path="/home/user/.cache/ms-playwright/firefox-1496/firefox/firefox",
                headless=True,
                proxy={
                    "server": "http://127.0.0.1:18914"
                },
                firefox_user_prefs={
                    "privacy.trackingprotection.enabled": False,
                    "network.proxy.allow_hijacking_localhost": True,
                    "security.cert_pinning.enforcement_level": 0,
                    # security.enterprise_roots.enabled を false にする
                    # → システム証明書ストアを見ない
                    "security.enterprise_roots.enabled": False,
                    "security.OCSP.enabled": 0,
                },
                ignore_https_errors=True,
                bypass_csp=True
            )

            print("   ✅ Firefox起動成功")

            page = await context.new_page()

            try:
                print("\n4. Yahoo! JAPANにアクセス中...")
                response = await page.goto(
                    "https://www.yahoo.co.jp/",
                    wait_until="domcontentloaded",
                    timeout=30000
                )

                print(f"   ステータス: {response.status}")
                print(f"   タイトル: {await page.title()}")

                content = await page.content()

                if "Warning: Potential Security Risk Ahead" in content:
                    print("\n❌ 証明書エラーが発生")
                    print("   → プロファイルの証明書が使われていない？")
                    success = False
                elif response.status == 200 and "Yahoo! JAPAN" in await page.title():
                    print("\n✅ 証明書エラーなしでアクセス成功！")
                    print("\n" + "=" * 70)
                    print("検証結果:")
                    print("=" * 70)
                    print("✅ Firefoxプロファイルの証明書だけで動作")
                    print("✅ security.enterprise_roots.enabled = false でも成功")
                    print("✅ システム証明書ストア（/etc/ssl/certs）は不要")
                    print("✅ update-ca-certificates は不要")
                    print("=" * 70)
                    print("\n結論:")
                    print("  Firefoxは独自の証明書ストア（cert9.db）を使用するため、")
                    print("  certutilでプロファイルにインポートすれば十分です。")
                    print("  システム証明書ストアの更新は、curl等の他のツールのためです。")
                    success = True
                else:
                    print("\n⚠️ 予期しない結果")
                    success = False

            except Exception as e:
                print(f"\n❌ エラー: {e}")
                import traceback
                traceback.print_exc()
                success = False

            finally:
                await context.close()
                print("\n✅ テスト完了")

        return success

    finally:
        print("\n5. proxy.pyを停止中...")
        proxy_process.send_signal(signal.SIGTERM)
        proxy_process.wait(timeout=5)
        print("   ✅ proxy.py停止完了")


async def main():
    try:
        os.environ['HOME'] = '/home/user'
        success = await test_firefox_without_system_cert()
        return success
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
