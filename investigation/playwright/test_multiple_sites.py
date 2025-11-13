#!/usr/bin/env python3
"""
Playwright 複数サイトアクセステスト
様々なサイトにアクセスして操作できるか確認
"""

from playwright.sync_api import sync_playwright
import sys
import time

def test_multiple_sites():
    """複数のサイトにアクセスしてスムーズに操作できるか確認"""
    try:
        print("=" * 70)
        print("Playwright 複数サイトアクセステスト")
        print("=" * 70)

        # テスト対象のサイトリスト
        test_sites = [
            {
                'name': 'Google',
                'url': 'https://www.google.com',
                'selector': 'input[name="q"]',  # 検索ボックス
                'action': 'search'
            },
            {
                'name': 'GitHub',
                'url': 'https://github.com',
                'selector': 'input[name="q"]',  # 検索ボックス
                'action': 'search'
            },
            {
                'name': 'Wikipedia',
                'url': 'https://www.wikipedia.org',
                'selector': '#searchInput',  # 検索ボックス
                'action': 'search'
            },
            {
                'name': 'Yahoo Japan',
                'url': 'https://www.yahoo.co.jp',
                'selector': 'input[name="p"]',  # 検索ボックス
                'action': 'search'
            },
            {
                'name': 'Qiita',
                'url': 'https://qiita.com',
                'selector': 'a[href="/login"]',  # ログインリンク
                'action': 'check'
            },
        ]

        with sync_playwright() as p:
            print("\n[1] ブラウザ起動...")
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--single-process',
                    '--disable-gpu',
                    '--disable-accelerated-2d-canvas',
                ]
            )
            print("    ✓ 成功")

            context = browser.new_context()
            page = context.new_page()

            results = []

            # 各サイトにアクセス
            for i, site in enumerate(test_sites, 1):
                print(f"\n" + "=" * 70)
                print(f"[{i}/{len(test_sites)}] {site['name']} のテスト")
                print("=" * 70)

                result = {
                    'name': site['name'],
                    'url': site['url'],
                    'success': False,
                    'error': None,
                    'load_time': 0,
                }

                try:
                    print(f"\n  → アクセス中: {site['url']}")
                    start_time = time.time()

                    # ページにアクセス（タイムアウトを15秒に設定）
                    response = page.goto(site['url'], timeout=15000, wait_until='domcontentloaded')
                    load_time = time.time() - start_time
                    result['load_time'] = load_time

                    print(f"  ✓ ページ読み込み完了: {load_time:.2f}秒")
                    print(f"  ✓ ステータスコード: {response.status}")

                    # タイトルを取得
                    title = page.title()
                    print(f"  ✓ ページタイトル: {title}")

                    # 要素の確認
                    if site['selector']:
                        print(f"\n  → 要素を確認中: {site['selector']}")
                        element = page.locator(site['selector'])

                        if element.count() > 0:
                            print(f"  ✓ 要素が見つかりました")

                            # アクションタイプに応じた操作
                            if site['action'] == 'search':
                                # 検索ボックスにテキストを入力
                                element.first.fill("Playwright test", timeout=5000)
                                print(f"  ✓ テキスト入力成功")
                                time.sleep(0.5)

                                # 入力した値を確認
                                value = element.first.input_value()
                                print(f"  ✓ 入力値確認: {value}")

                            elif site['action'] == 'check':
                                # 要素が表示されているか確認
                                if element.first.is_visible():
                                    print(f"  ✓ 要素が表示されています")
                        else:
                            print(f"  ⚠ 要素が見つかりませんでした")

                    # スクリーンショット
                    screenshot_path = f"/home/user/Kagami/test_site_{i}_{site['name'].replace(' ', '_').lower()}.png"
                    page.screenshot(path=screenshot_path)
                    print(f"\n  ✓ スクリーンショット: {screenshot_path}")

                    result['success'] = True
                    print(f"\n  ✅ {site['name']} のテスト成功")

                except Exception as e:
                    result['error'] = str(e)
                    print(f"\n  ❌ エラー: {e}")

                results.append(result)

                # 次のテストのために少し待機
                time.sleep(1)

            browser.close()

            # 結果のサマリー
            print("\n" + "=" * 70)
            print("テスト結果サマリー")
            print("=" * 70)

            success_count = sum(1 for r in results if r['success'])
            total_count = len(results)

            print(f"\n成功: {success_count}/{total_count} サイト\n")

            for result in results:
                status = "✅" if result['success'] else "❌"
                print(f"{status} {result['name']:<20} {result['url']}")

                if result['success']:
                    print(f"   └─ 読み込み時間: {result['load_time']:.2f}秒")
                else:
                    error_msg = result['error'][:60] if result['error'] else "Unknown error"
                    print(f"   └─ エラー: {error_msg}")
                print()

            print("=" * 70)

            if success_count == total_count:
                print("✅ すべてのサイトで正常に動作しました！")
                return True
            elif success_count > 0:
                print(f"⚠️  一部のサイトでエラーが発生しました ({success_count}/{total_count})")
                return True
            else:
                print("❌ すべてのサイトでエラーが発生しました")
                return False

    except Exception as e:
        print(f"\n❌ 致命的なエラー: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_multiple_sites()
    sys.exit(0 if success else 1)
