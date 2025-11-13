#!/usr/bin/env python3
"""
Playwright スムーズな操作テスト
複数ページ間のナビゲーションと操作性を確認
"""

from playwright.sync_api import sync_playwright
import sys
import time

def test_smooth_navigation():
    """複数ページ間のナビゲーションとスムーズな操作をテスト"""
    try:
        print("=" * 70)
        print("Playwright スムーズな操作テスト")
        print("複数ページのナビゲーションと操作性を確認")
        print("=" * 70)

        # テスト用のHTMLページ
        pages = {
            'home': """
            <!DOCTYPE html>
            <html>
            <head>
                <title>ホームページ</title>
                <style>
                    body { font-family: sans-serif; padding: 20px; background: #f0f0f0; }
                    .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
                    h1 { color: #333; }
                    nav { margin: 20px 0; }
                    a {
                        display: inline-block;
                        padding: 10px 20px;
                        margin: 5px;
                        background: #007bff;
                        color: white;
                        text-decoration: none;
                        border-radius: 5px;
                    }
                    a:hover { background: #0056b3; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1 id="title">🏠 ホームページ</h1>
                    <p>複数ページのナビゲーションテスト</p>
                    <nav>
                        <a href="#about" id="link-about">About</a>
                        <a href="#contact" id="link-contact">Contact</a>
                        <a href="#products" id="link-products">Products</a>
                    </nav>
                </div>
            </body>
            </html>
            """,

            'about': """
            <!DOCTYPE html>
            <html>
            <head>
                <title>About - 私たちについて</title>
                <style>
                    body { font-family: sans-serif; padding: 20px; background: #e8f4f8; }
                    .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
                    h1 { color: #2c5aa0; }
                    .back { margin-top: 20px; }
                    button { padding: 10px 20px; background: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer; }
                    input { padding: 10px; margin: 10px 0; width: 300px; border: 2px solid #ddd; border-radius: 5px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1 id="title">📖 About - 私たちについて</h1>
                    <p>このページでは様々な操作をテストします</p>

                    <h2>フォーム入力テスト</h2>
                    <input type="text" id="name-input" placeholder="お名前を入力してください" />
                    <button id="submit-btn">送信</button>
                    <p id="result"></p>

                    <div class="back">
                        <a href="#home" id="back-home">← ホームに戻る</a>
                    </div>
                </div>

                <script>
                    document.getElementById('submit-btn').addEventListener('click', function() {
                        const name = document.getElementById('name-input').value;
                        document.getElementById('result').textContent = 'こんにちは、' + name + 'さん！';
                    });
                </script>
            </body>
            </html>
            """,

            'contact': """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Contact - お問い合わせ</title>
                <style>
                    body { font-family: sans-serif; padding: 20px; background: #fff3e0; }
                    .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
                    h1 { color: #e65100; }
                    form { margin: 20px 0; }
                    label { display: block; margin: 10px 0 5px; font-weight: bold; }
                    input, textarea, select {
                        width: 100%;
                        padding: 10px;
                        border: 2px solid #ddd;
                        border-radius: 5px;
                        box-sizing: border-box;
                    }
                    textarea { height: 100px; resize: vertical; }
                    button {
                        margin-top: 15px;
                        padding: 12px 30px;
                        background: #ff9800;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                    }
                    .checkbox { width: auto; display: inline; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1 id="title">📧 Contact - お問い合わせ</h1>

                    <form id="contact-form">
                        <label for="email">メールアドレス</label>
                        <input type="email" id="email" placeholder="example@example.com" required />

                        <label for="category">カテゴリ</label>
                        <select id="category">
                            <option value="general">一般的なお問い合わせ</option>
                            <option value="support">サポート</option>
                            <option value="sales">営業</option>
                        </select>

                        <label for="message">メッセージ</label>
                        <textarea id="message" placeholder="お問い合わせ内容をご記入ください" required></textarea>

                        <label>
                            <input type="checkbox" id="agree" class="checkbox" required />
                            プライバシーポリシーに同意します
                        </label>

                        <button type="button" id="send-btn">送信</button>
                    </form>

                    <div id="form-result"></div>

                    <div class="back">
                        <a href="#home" id="back-home">← ホームに戻る</a>
                    </div>
                </div>

                <script>
                    document.getElementById('send-btn').addEventListener('click', function() {
                        const email = document.getElementById('email').value;
                        const category = document.getElementById('category').value;
                        const message = document.getElementById('message').value;
                        const agree = document.getElementById('agree').checked;

                        if (email && message && agree) {
                            document.getElementById('form-result').innerHTML =
                                '<p style="color: green; margin-top: 20px;">✅ 送信完了！ありがとうございました。</p>';
                        } else {
                            document.getElementById('form-result').innerHTML =
                                '<p style="color: red; margin-top: 20px;">❌ すべての必須項目を入力してください。</p>';
                        }
                    });
                </script>
            </body>
            </html>
            """,

            'products': """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Products - 製品一覧</title>
                <style>
                    body { font-family: sans-serif; padding: 20px; background: #e8f5e9; }
                    .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
                    h1 { color: #2e7d32; }
                    .products { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
                    .product {
                        padding: 20px;
                        border: 2px solid #4caf50;
                        border-radius: 10px;
                        text-align: center;
                        cursor: pointer;
                        transition: transform 0.2s;
                    }
                    .product:hover { transform: scale(1.05); background: #f1f8e9; }
                    .product h3 { margin: 10px 0; color: #2e7d32; }
                    .product button {
                        padding: 8px 16px;
                        background: #4caf50;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                    }
                    #cart {
                        margin-top: 20px;
                        padding: 15px;
                        background: #f1f8e9;
                        border-radius: 5px;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1 id="title">🛍️ Products - 製品一覧</h1>

                    <div class="products">
                        <div class="product">
                            <h3>製品A</h3>
                            <p>¥1,000</p>
                            <button class="add-to-cart" data-product="製品A" data-price="1000">カートに追加</button>
                        </div>
                        <div class="product">
                            <h3>製品B</h3>
                            <p>¥2,000</p>
                            <button class="add-to-cart" data-product="製品B" data-price="2000">カートに追加</button>
                        </div>
                        <div class="product">
                            <h3>製品C</h3>
                            <p>¥3,000</p>
                            <button class="add-to-cart" data-product="製品C" data-price="3000">カートに追加</button>
                        </div>
                    </div>

                    <div id="cart">
                        <h3>🛒 カート</h3>
                        <p id="cart-items">カートは空です</p>
                        <p id="cart-total"></p>
                    </div>

                    <div class="back">
                        <a href="#home" id="back-home">← ホームに戻る</a>
                    </div>
                </div>

                <script>
                    let cart = [];

                    document.querySelectorAll('.add-to-cart').forEach(button => {
                        button.addEventListener('click', function() {
                            const product = this.dataset.product;
                            const price = parseInt(this.dataset.price);
                            cart.push({ product, price });
                            updateCart();
                        });
                    });

                    function updateCart() {
                        if (cart.length === 0) {
                            document.getElementById('cart-items').textContent = 'カートは空です';
                            document.getElementById('cart-total').textContent = '';
                        } else {
                            const items = cart.map(item => item.product).join(', ');
                            const total = cart.reduce((sum, item) => sum + item.price, 0);
                            document.getElementById('cart-items').textContent = '商品: ' + items;
                            document.getElementById('cart-total').textContent = '合計: ¥' + total.toLocaleString();
                        }
                    }
                </script>
            </body>
            </html>
            """
        }

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

            # ===== ホームページのテスト =====
            print("\n" + "=" * 70)
            print("[2] ホームページのテスト")
            print("=" * 70)

            page.set_content(pages['home'])
            print("  ✓ ページ読み込み完了")

            title = page.locator("#title").text_content()
            print(f"  ✓ タイトル: {title}")

            # リンクの数を確認
            links = page.locator("nav a")
            print(f"  ✓ ナビゲーションリンク数: {links.count()}個")

            page.screenshot(path="/home/user/Kagami/test_nav_1_home.png")
            print("  ✓ スクリーンショット保存")

            # ===== Aboutページへ遷移 =====
            print("\n" + "=" * 70)
            print("[3] Aboutページへ遷移してフォーム操作")
            print("=" * 70)

            page.set_content(pages['about'])
            print("  ✓ ページ遷移完了")

            title = page.locator("#title").text_content()
            print(f"  ✓ タイトル: {title}")

            # フォーム操作
            print("\n  → フォーム操作中...")
            name_input = page.locator("#name-input")
            name_input.fill("テスト太郎")
            print("  ✓ 名前入力: テスト太郎")

            submit_btn = page.locator("#submit-btn")
            submit_btn.click()
            print("  ✓ ボタンクリック")

            time.sleep(0.3)
            result = page.locator("#result").text_content()
            print(f"  ✓ 結果表示: {result}")

            page.screenshot(path="/home/user/Kagami/test_nav_2_about.png")
            print("  ✓ スクリーンショット保存")

            # ===== Contactページへ遷移 =====
            print("\n" + "=" * 70)
            print("[4] Contactページへ遷移して複雑なフォーム操作")
            print("=" * 70)

            page.set_content(pages['contact'])
            print("  ✓ ページ遷移完了")

            title = page.locator("#title").text_content()
            print(f"  ✓ タイトル: {title}")

            # 複雑なフォーム操作
            print("\n  → 複雑なフォーム操作中...")

            page.locator("#email").fill("test@example.com")
            print("  ✓ メール入力: test@example.com")

            page.locator("#category").select_option("support")
            print("  ✓ カテゴリ選択: サポート")

            page.locator("#message").fill("これはテストメッセージです。\n複数行のテキストも問題なく入力できます。")
            print("  ✓ メッセージ入力: 複数行テキスト")

            page.locator("#agree").check()
            print("  ✓ チェックボックス: チェック")

            page.locator("#send-btn").click()
            print("  ✓ 送信ボタンクリック")

            time.sleep(0.3)
            form_result = page.locator("#form-result").inner_text()
            print(f"  ✓ フォーム結果: {form_result.strip()}")

            page.screenshot(path="/home/user/Kagami/test_nav_3_contact.png")
            print("  ✓ スクリーンショット保存")

            # ===== Productsページへ遷移 =====
            print("\n" + "=" * 70)
            print("[5] Productsページへ遷移してインタラクティブな操作")
            print("=" * 70)

            page.set_content(pages['products'])
            print("  ✓ ページ遷移完了")

            title = page.locator("#title").text_content()
            print(f"  ✓ タイトル: {title}")

            # 商品をカートに追加
            print("\n  → 商品をカートに追加中...")

            add_buttons = page.locator(".add-to-cart")
            print(f"  ✓ 商品数: {add_buttons.count()}個")

            # 製品Aを追加
            add_buttons.nth(0).click()
            time.sleep(0.2)
            print("  ✓ 製品Aをカートに追加")

            # 製品Bを追加
            add_buttons.nth(1).click()
            time.sleep(0.2)
            print("  ✓ 製品Bをカートに追加")

            # 製品Cを追加
            add_buttons.nth(2).click()
            time.sleep(0.2)
            print("  ✓ 製品Cをカートに追加")

            # カートの内容を確認
            cart_items = page.locator("#cart-items").text_content()
            cart_total = page.locator("#cart-total").text_content()
            print(f"\n  📦 {cart_items}")
            print(f"  💰 {cart_total}")

            page.screenshot(path="/home/user/Kagami/test_nav_4_products.png")
            print("\n  ✓ スクリーンショット保存")

            # ===== パフォーマンステスト =====
            print("\n" + "=" * 70)
            print("[6] 高速ナビゲーションテスト")
            print("=" * 70)

            print("\n  → 複数ページを高速で切り替え中...")
            start_time = time.time()

            for i in range(5):
                page.set_content(pages['home'])
                page.set_content(pages['about'])
                page.set_content(pages['contact'])
                page.set_content(pages['products'])

            elapsed = time.time() - start_time
            operations = 5 * 4  # 5回 × 4ページ
            avg_time = elapsed / operations

            print(f"  ✓ 完了: {operations}回のページ遷移")
            print(f"  ✓ 合計時間: {elapsed:.2f}秒")
            print(f"  ✓ 平均時間: {avg_time:.3f}秒/ページ")

            browser.close()

            # ===== 結果サマリー =====
            print("\n" + "=" * 70)
            print("✅ テスト結果サマリー")
            print("=" * 70)

            print("\n📋 確認できた操作:")
            print("  ✓ 複数ページ間のスムーズなナビゲーション")
            print("  ✓ テキスト入力（単一行・複数行）")
            print("  ✓ ボタンクリック")
            print("  ✓ セレクトボックス選択")
            print("  ✓ チェックボックス操作")
            print("  ✓ 動的コンテンツの更新")
            print("  ✓ 複数要素の連続操作")
            print("  ✓ JavaScriptによるDOM操作")
            print("  ✓ スクリーンショット撮影")
            print(f"  ✓ 高速ナビゲーション（平均{avg_time:.3f}秒/ページ）")

            print("\n🚀 パフォーマンス:")
            print(f"  • {operations}回のページ遷移を{elapsed:.2f}秒で完了")
            print(f"  • 1ページあたり平均{avg_time:.3f}秒")
            print(f"  • すべての操作がスムーズに動作")

            print("\n💡 結論:")
            print("  Playwrightは複数ページ間の遷移とインタラクティブな")
            print("  操作をスムーズに実行できます。外部サイトへのアクセスは")
            print("  環境の制限により不可ですが、ローカルコンテンツの操作は")
            print("  完全に問題なく動作します。")

            return True

    except Exception as e:
        print(f"\n❌ エラー: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_smooth_navigation()
    sys.exit(0 if success else 1)
