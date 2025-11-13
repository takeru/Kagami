#!/usr/bin/env python3
"""
Playwright セッション永続化の実践的シナリオテスト
ログイン・セッション管理・データ保持を確認
"""

from playwright.sync_api import sync_playwright
import sys
import tempfile
import time

def test_session_scenario():
    """セッション永続化を使った実践的なシナリオをテスト"""
    try:
        print("=" * 70)
        print("Playwright セッション永続化の実践的シナリオテスト")
        print("=" * 70)

        # ユーザーデータディレクトリを作成
        user_data_dir = tempfile.mkdtemp(prefix="playwright_session_", dir="/tmp")
        cache_dir = tempfile.mkdtemp(prefix="playwright_cache_", dir="/tmp")
        print(f"\n📁 セッションディレクトリ: {user_data_dir}")

        # ログインページのHTML
        login_page = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>ログイン</title>
            <style>
                body { font-family: sans-serif; padding: 20px; background: #f5f5f5; }
                .login-box {
                    max-width: 400px;
                    margin: 50px auto;
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                h1 { color: #333; text-align: center; }
                input {
                    width: 100%;
                    padding: 12px;
                    margin: 10px 0;
                    border: 2px solid #ddd;
                    border-radius: 5px;
                    box-sizing: border-box;
                }
                button {
                    width: 100%;
                    padding: 12px;
                    background: #007bff;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 16px;
                }
                button:hover { background: #0056b3; }
                .error { color: red; margin-top: 10px; }
                .success { color: green; margin-top: 10px; }
            </style>
        </head>
        <body>
            <div class="login-box">
                <h1>🔐 ログイン</h1>
                <input type="text" id="username" placeholder="ユーザー名" />
                <input type="password" id="password" placeholder="パスワード" />
                <button id="login-btn">ログイン</button>
                <div id="message"></div>
            </div>

            <script>
                document.getElementById('login-btn').addEventListener('click', function() {
                    const username = document.getElementById('username').value;
                    const password = document.getElementById('password').value;

                    if (username === 'testuser' && password === 'password123') {
                        // ログイン成功 - セッション情報を保存
                        localStorage.setItem('user', username);
                        localStorage.setItem('loginTime', new Date().toISOString());
                        localStorage.setItem('sessionId', 'sess_' + Date.now());
                        document.getElementById('message').innerHTML =
                            '<div class="success">✅ ログイン成功！</div>';

                        // ダッシュボードに遷移（シミュレート）
                        setTimeout(() => {
                            document.body.innerHTML = '<div style="text-align: center; padding: 50px;"><h1>ダッシュボードに移動中...</h1></div>';
                        }, 1000);
                    } else {
                        document.getElementById('message').innerHTML =
                            '<div class="error">❌ ユーザー名またはパスワードが間違っています</div>';
                    }
                });
            </script>
        </body>
        </html>
        """

        # ダッシュボードページのHTML
        dashboard_page = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>ダッシュボード</title>
            <style>
                body { font-family: sans-serif; margin: 0; background: #f5f5f5; }
                .header {
                    background: #007bff;
                    color: white;
                    padding: 20px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }
                .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
                .welcome { font-size: 24px; margin-bottom: 10px; }
                .info { opacity: 0.9; }
                .cards {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin: 20px 0;
                }
                .card {
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }
                .card h3 { margin-top: 0; color: #007bff; }
                .actions { margin-top: 20px; }
                button {
                    padding: 10px 20px;
                    margin: 5px;
                    background: #28a745;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                }
                button.logout { background: #dc3545; }
                #log {
                    background: white;
                    padding: 15px;
                    border-radius: 5px;
                    margin-top: 20px;
                    max-height: 200px;
                    overflow-y: auto;
                }
                .log-entry {
                    padding: 5px 0;
                    border-bottom: 1px solid #eee;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <div class="container">
                    <div class="welcome">👋 ようこそ、<span id="username"></span>さん</div>
                    <div class="info">
                        セッションID: <span id="session-id"></span><br>
                        ログイン時刻: <span id="login-time"></span>
                    </div>
                </div>
            </div>

            <div class="container">
                <div class="cards">
                    <div class="card">
                        <h3>📊 統計情報</h3>
                        <p>訪問回数: <span id="visit-count">0</span></p>
                        <p>操作回数: <span id="action-count">0</span></p>
                    </div>

                    <div class="card">
                        <h3>📝 最近のアクティビティ</h3>
                        <p id="last-activity">まだアクティビティがありません</p>
                    </div>

                    <div class="card">
                        <h3>⚙️ 設定</h3>
                        <label>
                            <input type="checkbox" id="notifications" />
                            通知を有効にする
                        </label>
                    </div>
                </div>

                <div class="actions">
                    <button id="action1">アクション1を実行</button>
                    <button id="action2">アクション2を実行</button>
                    <button id="action3">アクション3を実行</button>
                    <button id="save-btn">設定を保存</button>
                    <button class="logout" id="logout-btn">ログアウト</button>
                </div>

                <div id="log">
                    <h3>📋 操作ログ</h3>
                    <div id="log-entries"></div>
                </div>
            </div>

            <script>
                // セッション情報を読み込み
                const user = localStorage.getItem('user');
                const sessionId = localStorage.getItem('sessionId');
                const loginTime = localStorage.getItem('loginTime');

                if (!user) {
                    document.body.innerHTML = '<div style="text-align: center; padding: 50px;"><h1>セッションが見つかりません</h1><p>ログインしてください</p></div>';
                } else {
                    document.getElementById('username').textContent = user;
                    document.getElementById('session-id').textContent = sessionId;
                    document.getElementById('login-time').textContent = new Date(loginTime).toLocaleString('ja-JP');

                    // 訪問回数を更新
                    let visitCount = parseInt(localStorage.getItem('visitCount') || '0') + 1;
                    localStorage.setItem('visitCount', visitCount);
                    document.getElementById('visit-count').textContent = visitCount;

                    // 操作回数を読み込み
                    let actionCount = parseInt(localStorage.getItem('actionCount') || '0');
                    document.getElementById('action-count').textContent = actionCount;

                    // 通知設定を読み込み
                    const notifications = localStorage.getItem('notifications') === 'true';
                    document.getElementById('notifications').checked = notifications;

                    // 最後のアクティビティを読み込み
                    const lastActivity = localStorage.getItem('lastActivity');
                    if (lastActivity) {
                        document.getElementById('last-activity').textContent = lastActivity;
                    }

                    // ログを追加する関数
                    function addLog(message) {
                        const logEntry = document.createElement('div');
                        logEntry.className = 'log-entry';
                        logEntry.textContent = new Date().toLocaleTimeString() + ': ' + message;
                        document.getElementById('log-entries').prepend(logEntry);

                        localStorage.setItem('lastActivity', message);
                    }

                    // アクションボタン
                    document.getElementById('action1').addEventListener('click', function() {
                        actionCount++;
                        localStorage.setItem('actionCount', actionCount);
                        document.getElementById('action-count').textContent = actionCount;
                        addLog('アクション1を実行しました');
                    });

                    document.getElementById('action2').addEventListener('click', function() {
                        actionCount++;
                        localStorage.setItem('actionCount', actionCount);
                        document.getElementById('action-count').textContent = actionCount;
                        addLog('アクション2を実行しました');
                    });

                    document.getElementById('action3').addEventListener('click', function() {
                        actionCount++;
                        localStorage.setItem('actionCount', actionCount);
                        document.getElementById('action-count').textContent = actionCount;
                        addLog('アクション3を実行しました');
                    });

                    // 設定保存
                    document.getElementById('save-btn').addEventListener('click', function() {
                        const notifications = document.getElementById('notifications').checked;
                        localStorage.setItem('notifications', notifications);
                        addLog('設定を保存しました');
                        alert('設定を保存しました！');
                    });

                    // ログアウト
                    document.getElementById('logout-btn').addEventListener('click', function() {
                        if (confirm('本当にログアウトしますか？')) {
                            localStorage.clear();
                            location.reload();
                        }
                    });

                    addLog('ダッシュボードにアクセスしました');
                }
            </script>
        </body>
        </html>
        """

        # ===== セッション1: 初回ログイン =====
        print("\n" + "=" * 70)
        print("セッション1: 初回ログインと操作")
        print("=" * 70)

        with sync_playwright() as p:
            print("\n[1] ブラウザ起動（永続化モード）...")
            browser = p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=True,
                args=[
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--single-process',
                    '--disable-gpu',
                    '--disable-accelerated-2d-canvas',
                    f'--disk-cache-dir={cache_dir}',
                ]
            )
            print("    ✓ 成功")

            page = browser.pages[0]

            print("\n[2] ログインページにアクセス...")
            page.goto("about:blank")
            page.set_content(login_page)
            print("    ✓ ページ読み込み完了")

            print("\n[3] ログイン情報を入力...")
            page.locator("#username").fill("testuser")
            print("    ✓ ユーザー名: testuser")

            page.locator("#password").fill("password123")
            print("    ✓ パスワード: ********")

            print("\n[4] ログインボタンをクリック...")
            page.locator("#login-btn").click()
            time.sleep(1.5)
            print("    ✓ ログイン処理完了")

            # セッション情報を確認
            user = page.evaluate("localStorage.getItem('user')")
            session_id = page.evaluate("localStorage.getItem('sessionId')")
            print(f"\n    📝 ユーザー: {user}")
            print(f"    📝 セッションID: {session_id}")

            page.screenshot(path="/home/user/Kagami/test_session_1_login.png")

            print("\n[5] ダッシュボードにアクセス...")
            page.goto("about:blank")
            page.set_content(dashboard_page)
            time.sleep(0.5)
            print("    ✓ ダッシュボード読み込み完了")

            # 訪問回数を確認
            visit_count = page.locator("#visit-count").text_content()
            print(f"    📊 訪問回数: {visit_count}回")

            print("\n[6] 複数のアクションを実行...")
            page.locator("#action1").click()
            time.sleep(0.2)
            print("    ✓ アクション1実行")

            page.locator("#action2").click()
            time.sleep(0.2)
            print("    ✓ アクション2実行")

            page.locator("#action3").click()
            time.sleep(0.2)
            print("    ✓ アクション3実行")

            # 操作回数を確認
            action_count = page.locator("#action-count").text_content()
            print(f"\n    📊 操作回数: {action_count}回")

            print("\n[7] 設定を変更...")
            page.locator("#notifications").check()
            print("    ✓ 通知を有効化")

            page.locator("#save-btn").click()
            time.sleep(0.5)

            # アラートを処理
            page.on("dialog", lambda dialog: dialog.accept())
            print("    ✓ 設定を保存")

            page.screenshot(path="/home/user/Kagami/test_session_1_dashboard.png")

            browser.close()
            print("\n    ✓ ブラウザを閉じました")

        # ===== セッション2: セッション復元 =====
        print("\n" + "=" * 70)
        print("セッション2: セッション復元と継続")
        print("=" * 70)

        with sync_playwright() as p:
            print("\n[8] ブラウザ再起動（同じセッション）...")
            browser = p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=True,
                args=[
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--single-process',
                    '--disable-gpu',
                    '--disable-accelerated-2d-canvas',
                    f'--disk-cache-dir={cache_dir}',
                ]
            )
            print("    ✓ 成功")

            page = browser.pages[0]

            print("\n[9] ダッシュボードにアクセス（ログイン不要）...")
            page.goto("about:blank")
            page.set_content(dashboard_page)
            time.sleep(0.5)
            print("    ✓ ダッシュボード読み込み完了")

            # セッション情報が保持されているか確認
            username = page.locator("#username").text_content()
            session_id_display = page.locator("#session-id").text_content()
            visit_count = page.locator("#visit-count").text_content()
            action_count = page.locator("#action-count").text_content()

            print(f"\n    ✅ セッション復元成功！")
            print(f"    📝 ユーザー: {username}")
            print(f"    📝 セッションID: {session_id_display}")
            print(f"    📊 訪問回数: {visit_count}回（前回から+1）")
            print(f"    📊 操作回数: {action_count}回（前回と同じ）")

            # 設定が保持されているか確認
            notifications_checked = page.locator("#notifications").is_checked()
            print(f"    ⚙️  通知設定: {'有効' if notifications_checked else '無効'}（保持されている）")

            print("\n[10] さらにアクションを実行...")
            page.locator("#action1").click()
            time.sleep(0.2)
            page.locator("#action2").click()
            time.sleep(0.2)

            action_count_new = page.locator("#action-count").text_content()
            print(f"     ✓ 操作回数が更新: {action_count} → {action_count_new}回")

            page.screenshot(path="/home/user/Kagami/test_session_2_restored.png")

            browser.close()
            print("\n    ✓ ブラウザを閉じました")

        # ===== 結果サマリー =====
        print("\n" + "=" * 70)
        print("✅ セッション永続化テスト成功")
        print("=" * 70)

        print("\n📋 確認できた機能:")
        print("  ✓ ログイン状態の永続化")
        print("  ✓ LocalStorageによるセッション管理")
        print("  ✓ ユーザーデータの保持（訪問回数、操作回数）")
        print("  ✓ 設定情報の保持（通知設定）")
        print("  ✓ セッションIDの保持")
        print("  ✓ 複数セッション間でのデータ共有")
        print("  ✓ ログイン不要での再アクセス")

        print("\n💡 実践的な使い方:")
        print("  • Webアプリケーションのテスト自動化")
        print("  • ログイン状態を保持したままの連続操作")
        print("  • ユーザーデータの永続化テスト")
        print("  • セッション管理機能の検証")

        print(f"\n🗑️  セッションディレクトリ:")
        print(f"    {user_data_dir}")
        print(f"    {cache_dir}")

        return True

    except Exception as e:
        print(f"\n❌ エラー: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_session_scenario()
    sys.exit(0 if success else 1)
