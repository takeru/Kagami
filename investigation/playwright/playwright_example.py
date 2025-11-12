#!/usr/bin/env python3
"""
Playwright 実用例 - 複雑なHTML操作とスクレイピング
"""

from playwright.sync_api import sync_playwright
import json

def example_complex_interaction():
    """複雑なHTML操作の例"""

    with sync_playwright() as p:
        # サンドボックス無効でブラウザ起動
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu'
            ]
        )

        page = browser.new_page()

        # 複雑なHTMLページを作成
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>データテーブル</title>
            <style>
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid black; padding: 8px; text-align: left; }
                th { background-color: #4CAF50; color: white; }
                .clickable { cursor: pointer; color: blue; }
                #result { margin-top: 20px; padding: 10px; background: #f0f0f0; }
            </style>
        </head>
        <body>
            <h1>GitHub Issues風データテーブル</h1>

            <table id="issues-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>タイトル</th>
                        <th>ステータス</th>
                        <th>優先度</th>
                    </tr>
                </thead>
                <tbody>
                    <tr data-id="1">
                        <td class="issue-id">1</td>
                        <td class="clickable">Playwrightのセットアップ</td>
                        <td class="status">完了</td>
                        <td class="priority">高</td>
                    </tr>
                    <tr data-id="2">
                        <td class="issue-id">2</td>
                        <td class="clickable">自動テストの追加</td>
                        <td class="status">進行中</td>
                        <td class="priority">中</td>
                    </tr>
                    <tr data-id="3">
                        <td class="issue-id">3</td>
                        <td class="clickable">ドキュメント更新</td>
                        <td class="status">未着手</td>
                        <td class="priority">低</td>
                    </tr>
                </tbody>
            </table>

            <div id="result"></div>

            <script>
                document.querySelectorAll('.clickable').forEach(el => {
                    el.addEventListener('click', function() {
                        const row = this.closest('tr');
                        const id = row.dataset.id;
                        const title = this.textContent;
                        const status = row.querySelector('.status').textContent;

                        document.getElementById('result').innerHTML =
                            `<strong>選択されたIssue:</strong><br>` +
                            `ID: ${id}<br>` +
                            `タイトル: ${title}<br>` +
                            `ステータス: ${status}`;
                    });
                });
            </script>
        </body>
        </html>
        """

        # HTMLを設定
        page.set_content(html_content)

        print("=" * 60)
        print("Playwright 実用例デモ")
        print("=" * 60)

        # 1. テーブルデータの抽出
        print("\n[1] テーブルデータの抽出")
        rows = page.locator("tbody tr").all()
        issues = []

        for row in rows:
            issue = {
                "id": row.locator(".issue-id").text_content(),
                "title": row.locator(".clickable").text_content(),
                "status": row.locator(".status").text_content(),
                "priority": row.locator(".priority").text_content()
            }
            issues.append(issue)
            print(f"  - Issue #{issue['id']}: {issue['title']} [{issue['status']}]")

        # 2. 条件に基づく要素の検索
        print("\n[2] ステータスが「進行中」のIssueを検索")
        in_progress = page.locator("tr:has(.status:text('進行中'))").all()
        print(f"  見つかった件数: {len(in_progress)}")

        # 3. クリックイベントのシミュレーション
        print("\n[3] 2番目のIssueをクリック")
        page.locator("tbody tr:nth-child(2) .clickable").click()
        page.wait_for_timeout(100)  # JavaScriptの実行を待つ

        result_text = page.locator("#result").text_content()
        print(f"  結果表示: {result_text.strip()}")

        # 4. JavaScriptを使った高度なデータ抽出
        print("\n[4] JavaScriptでの高度なデータ抽出")
        js_data = page.evaluate("""
            () => {
                const rows = Array.from(document.querySelectorAll('tbody tr'));
                return rows.map(row => ({
                    id: row.querySelector('.issue-id').textContent,
                    title: row.querySelector('.clickable').textContent,
                    status: row.querySelector('.status').textContent,
                    priority: row.querySelector('.priority').textContent,
                    row_html: row.innerHTML.length
                }));
            }
        """)
        print(f"  抽出されたデータ: {json.dumps(js_data, ensure_ascii=False, indent=2)}")

        # 5. スクリーンショット
        print("\n[5] スクリーンショット撮影")
        page.screenshot(path="/home/user/Kagami/playwright_example.png", full_page=True)
        print("  保存先: /home/user/Kagami/playwright_example.png")

        browser.close()

        print("\n" + "=" * 60)
        print("✅ デモ完了")
        print("=" * 60)

        return issues

if __name__ == "__main__":
    example_complex_interaction()
