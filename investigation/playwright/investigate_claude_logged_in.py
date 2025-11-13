#!/usr/bin/env python3
"""
claude.ai/codeにアクセス成功後、ページ構造を調査
成功した設定（test_claude_undetected.py）をベースに実装
"""
import subprocess
import time
import os
import tempfile
from playwright.sync_api import sync_playwright


print("="*60)
print("Claude AI Page Structure Investigation")
print("="*60)
print()

# proxy.pyを起動
print("Starting proxy.py...")
proxy_process = subprocess.Popen(
    [
        'uv', 'run', 'proxy',
        '--hostname', '127.0.0.1',
        '--port', '8904',
        '--plugins', 'proxy.plugin.proxy_pool.ProxyPoolPlugin',
        '--proxy-pool', os.environ['HTTPS_PROXY'],
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

time.sleep(5)
print("✅ Proxy started\n")

# 一時ディレクトリ
user_data_dir = tempfile.mkdtemp(prefix="claude_logged_", dir="/tmp")
cache_dir = tempfile.mkdtemp(prefix="cache_", dir="/tmp")

try:
    with sync_playwright() as p:
        print("Launching Chromium (undetected mode)...")

        browser = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=True,
            args=[
                # 共有メモリ対策
                '--disable-dev-shm-usage',
                '--single-process',

                # サンドボックス無効化
                '--no-sandbox',
                '--disable-setuid-sandbox',

                # プロキシ設定
                '--proxy-server=http://127.0.0.1:8904',
                '--ignore-certificate-errors',

                # Bot検出回避（test_claude_undetected.pyと同じ設定）
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',

                # Headless検出回避
                '--window-size=1920,1080',
                '--start-maximized',

                # その他
                '--disable-gpu',
                '--disable-accelerated-2d-canvas',
                f'--disk-cache-dir={cache_dir}',

                # User agent
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            ]
        )

        print("✅ Browser launched\n")

        page = browser.pages[0]

        # Anti-detection JavaScript（test_claude_undetected.pyと同じ）
        await_js = """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        window.chrome = { runtime: {} };
        """

        page.add_init_script(await_js)
        print("✅ Anti-detection scripts injected\n")

        # アクセス
        print("Accessing https://claude.ai/code/ ...")
        response = page.goto("https://claude.ai/code/", timeout=60000)
        print(f"✅ Status: {response.status}")
        print(f"✅ URL: {response.url}")

        # タイトル取得
        title = page.title()
        print(f"✅ Title: {title}\n")

        # 少し待つ
        time.sleep(3)

        print("="*60)
        print("Page Structure Analysis")
        print("="*60)

        # HTMLコンテンツを保存
        content = page.content()
        html_file = "claude_code_page_success.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"\n✅ HTML saved to: {html_file} ({len(content)} bytes)")

        # ボタンを探す
        print("\n1. Buttons...")
        buttons = page.locator("button").all()
        print(f"   Total: {len(buttons)} buttons")
        for i, btn in enumerate(buttons[:15], 1):
            try:
                text = btn.text_content(timeout=1000) or ""
                text = text.strip()[:50]
                visible = btn.is_visible()
                classes = btn.get_attribute("class", timeout=1000) or ""
                print(f"   [{i}] '{text}' | Visible: {visible} | Classes: {classes[:50]}")
            except Exception as e:
                print(f"   [{i}] Error: {e}")

        # リンクを探す
        print("\n2. Links...")
        links = page.locator("a").all()
        print(f"   Total: {len(links)} links")
        for i, link in enumerate(links[:15], 1):
            try:
                text = link.text_content(timeout=1000) or ""
                text = text.strip()[:30]
                href = link.get_attribute("href", timeout=1000) or ""
                print(f"   [{i}] '{text}' | Href: {href[:50]}")
            except Exception as e:
                print(f"   [{i}] Error: {e}")

        # 入力フィールドを探す
        print("\n3. Input fields...")
        inputs = page.locator("input").all()
        print(f"   Total: {len(inputs)} inputs")
        for i, inp in enumerate(inputs[:10], 1):
            try:
                type_attr = inp.get_attribute("type", timeout=1000)
                placeholder = inp.get_attribute("placeholder", timeout=1000)
                name = inp.get_attribute("name", timeout=1000)
                print(f"   [{i}] Type: {type_attr} | Placeholder: {placeholder} | Name: {name}")
            except Exception as e:
                print(f"   [{i}] Error: {e}")

        # キーワード検索
        print("\n4. Login-related keywords...")
        keywords = ["log in", "sign in", "login", "signin", "email", "continue", "get started"]

        for keyword in keywords:
            try:
                count = page.get_by_text(keyword, exact=False).count()
                if count > 0:
                    print(f"   '{keyword}': {count} matches")
                    # 最初の要素の情報を取得
                    first = page.get_by_text(keyword, exact=False).first
                    tag = first.evaluate("el => el.tagName")
                    text = first.text_content()[:50]
                    print(f"      First: <{tag}> '{text}'")
            except Exception as e:
                pass

        # スクリーンショット
        page.screenshot(path="claude_investigate_success.png", full_page=True)
        print(f"\n✅ Screenshot saved: claude_investigate_success.png")

        # JavaScriptで情報取得
        print("\n5. JavaScript Analysis...")
        try:
            js_info = page.evaluate("""
                () => {
                    const info = {
                        url: window.location.href,
                        title: document.title,
                        bodyClasses: document.body.className,
                        bodyId: document.body.id,
                        rootDivs: Array.from(document.querySelectorAll('body > div')).map(d => ({
                            id: d.id,
                            classes: d.className,
                            hasChildren: d.children.length > 0
                        })),
                        hasReact: !!window.React || !!document.querySelector('[data-reactroot]') || !!document.querySelector('[data-reactid]'),
                        localStorageKeys: Object.keys(localStorage),
                    };
                    return info;
                }
            """)
            print(f"   URL: {js_info['url']}")
            print(f"   Title: {js_info['title']}")
            print(f"   Body classes: {js_info['bodyClasses']}")
            print(f"   Has React: {js_info['hasReact']}")
            print(f"   LocalStorage keys: {len(js_info['localStorageKeys'])} keys")
            if js_info['localStorageKeys']:
                print(f"      Keys: {', '.join(js_info['localStorageKeys'][:5])}")
            print(f"   Root divs: {len(js_info['rootDivs'])}")
            for i, div in enumerate(js_info['rootDivs'][:3], 1):
                print(f"      [{i}] id={div['id']}, classes={div['classes'][:50]}")
        except Exception as e:
            print(f"   Error: {e}")

        browser.close()

        print("\n" + "="*60)
        print("✅ Investigation completed!")
        print("="*60)
        print(f"\nFiles created:")
        print(f"  - {html_file}")
        print(f"  - claude_investigate_success.png")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    print("\nStopping proxy...")
    proxy_process.terminate()
    try:
        proxy_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proxy_process.kill()
    print("✅ Done")
