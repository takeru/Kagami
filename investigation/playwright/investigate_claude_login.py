#!/usr/bin/env python3
"""
claude.ai/codeのログインフローを調査
ページ構造を解析してログイン要素を特定
"""
import subprocess
import time
import os
import tempfile
from playwright.sync_api import sync_playwright


print("="*60)
print("Claude AI Login Flow Investigation")
print("="*60)
print()

# proxy.pyを起動
print("Starting proxy.py...")
proxy_process = subprocess.Popen(
    [
        'uv', 'run', 'proxy',
        '--hostname', '127.0.0.1',
        '--port', '8903',
        '--plugins', 'proxy.plugin.proxy_pool.ProxyPoolPlugin',
        '--proxy-pool', os.environ['HTTPS_PROXY'],
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

time.sleep(5)
print("✅ Proxy started\n")

# 一時ディレクトリ
user_data_dir = tempfile.mkdtemp(prefix="claude_investigate_", dir="/tmp")
cache_dir = tempfile.mkdtemp(prefix="cache_", dir="/tmp")

try:
    with sync_playwright() as p:
        print("Launching Chromium...")

        browser = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=True,
            args=[
                '--disable-dev-shm-usage',
                '--single-process',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--proxy-server=http://127.0.0.1:8903',
                '--ignore-certificate-errors',
                '--disable-blink-features=AutomationControlled',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                '--disable-gpu',
                f'--disk-cache-dir={cache_dir}',
            ]
        )

        print("✅ Browser launched\n")

        page = browser.pages[0]

        # Anti-detection
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            window.chrome = { runtime: {} };
        """)

        # アクセス
        print("Accessing https://claude.ai/code/ ...")
        response = page.goto("https://claude.ai/code/", timeout=60000)
        print(f"✅ Status: {response.status}")
        print(f"✅ URL: {response.url}\n")

        # 少し待つ
        time.sleep(3)

        # ページ情報を取得
        title = page.title()
        print(f"Title: {title}")

        # HTMLコンテンツを取得
        content = page.content()

        # HTMLをファイルに保存
        html_file = "claude_code_page.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ HTML saved to: {html_file} ({len(content)} bytes)\n")

        print("="*60)
        print("Page Structure Analysis")
        print("="*60)

        # ボタンを探す
        print("\n1. Looking for buttons...")
        buttons = page.locator("button").all()
        print(f"   Found {len(buttons)} buttons:")
        for i, btn in enumerate(buttons[:10], 1):  # 最初の10個
            try:
                text = btn.text_content(timeout=1000)
                visible = btn.is_visible()
                print(f"   [{i}] Text: '{text}' | Visible: {visible}")
            except:
                print(f"   [{i}] (could not get info)")

        # リンクを探す
        print("\n2. Looking for links...")
        links = page.locator("a").all()
        print(f"   Found {len(links)} links:")
        for i, link in enumerate(links[:10], 1):
            try:
                text = link.text_content(timeout=1000)
                href = link.get_attribute("href", timeout=1000)
                print(f"   [{i}] Text: '{text}' | Href: {href}")
            except:
                print(f"   [{i}] (could not get info)")

        # フォーム要素を探す
        print("\n3. Looking for form elements...")
        inputs = page.locator("input").all()
        print(f"   Found {len(inputs)} input fields:")
        for i, inp in enumerate(inputs[:10], 1):
            try:
                type_attr = inp.get_attribute("type", timeout=1000)
                placeholder = inp.get_attribute("placeholder", timeout=1000)
                name = inp.get_attribute("name", timeout=1000)
                print(f"   [{i}] Type: {type_attr} | Placeholder: {placeholder} | Name: {name}")
            except:
                print(f"   [{i}] (could not get info)")

        # 特定のキーワードを含む要素を探す
        print("\n4. Looking for login-related elements...")
        keywords = ["login", "sign", "email", "auth", "continue"]

        for keyword in keywords:
            try:
                # テキストで検索
                elements = page.get_by_text(keyword, exact=False).all()
                if elements:
                    print(f"   '{keyword}': Found {len(elements)} elements")
            except:
                pass

        # スクリーンショット
        page.screenshot(path="claude_investigate.png", full_page=True)
        print(f"\n✅ Screenshot saved: claude_investigate.png")

        # JavaScriptで追加情報を取得
        print("\n5. JavaScript Information...")
        try:
            js_info = page.evaluate("""
                () => {
                    return {
                        hasReact: !!window.React || !!document.querySelector('[data-reactroot]'),
                        hasVue: !!window.Vue,
                        hasAngular: !!window.angular,
                        bodyClasses: document.body.className,
                        metaTags: Array.from(document.querySelectorAll('meta')).map(m => ({
                            name: m.name,
                            property: m.property,
                            content: m.content?.substring(0, 50)
                        })).slice(0, 10)
                    };
                }
            """)
            print(f"   React: {js_info['hasReact']}")
            print(f"   Body classes: {js_info['bodyClasses']}")
            print(f"   Meta tags: {len(js_info['metaTags'])} found")
        except Exception as e:
            print(f"   Could not get JS info: {e}")

        browser.close()

        print("\n" + "="*60)
        print("✅ Investigation completed!")
        print("="*60)
        print(f"\nFiles created:")
        print(f"  - {html_file}")
        print(f"  - claude_investigate.png")
        print(f"\nNext steps:")
        print(f"  1. Review the HTML file to understand the page structure")
        print(f"  2. Identify the login button/link selectors")
        print(f"  3. Understand the authentication flow")

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
