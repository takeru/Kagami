#!/usr/bin/env python3
"""
Seleniumで基本的なテスト
- プロキシなしで動作するか確認
- DOM操作が正常に動作するか確認
"""
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import subprocess


print("="*60, flush=True)
print("Selenium Basic Test (No Proxy)", flush=True)
print("="*60, flush=True)
print(flush=True)

# Chromiumのパスを探す
print("Finding Chromium binary...", flush=True)
result = subprocess.run(
    ["find", "/root/.cache/ms-playwright", "-name", "headless_shell", "-type", "f"],
    capture_output=True,
    text=True,
)

if result.returncode == 0 and result.stdout.strip():
    chromium_path = result.stdout.strip().split('\n')[0]
    print(f"✅ Found: {chromium_path}", flush=True)
else:
    print("❌ Chromium not found", flush=True)
    sys.exit(1)

print(flush=True)

html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Test Page</title>
</head>
<body>
    <h1 id="heading">Hello World</h1>
    <button id="btn" onclick="document.getElementById('output').textContent='Clicked!'">Click me</button>
    <div id="output"></div>
</body>
</html>"""

try:
    # Chrome optionsを設定
    chrome_options = Options()
    chrome_options.binary_location = chromium_path
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument('--disable-gpu')

    print("Launching Chrome with Selenium...", flush=True)
    sys.stdout.flush()

    # Note: ChromeDriverが必要だが、まず試してみる
    driver = webdriver.Chrome(options=chrome_options)

    print("✅ Browser launched", flush=True)
    sys.stdout.flush()

    # Test 1: HTMLファイルをロード
    print("\nTest 1: Loading HTML via data URL", flush=True)
    import base64
    html_b64 = base64.b64encode(html_content.encode()).decode()
    data_url = f"data:text/html;base64,{html_b64}"

    driver.get(data_url)
    print("✅ Page loaded", flush=True)

    # Test 2: Get title
    print("\nTest 2: driver.title", flush=True)
    title = driver.title
    print(f"✅ Title: {title}", flush=True)

    # Test 3: Find element
    print("\nTest 3: find_element", flush=True)
    h1 = driver.find_element(By.ID, "heading")
    h1_text = h1.text
    print(f"✅ H1 text: {h1_text}", flush=True)

    # Test 4: Click button
    print("\nTest 4: Click button", flush=True)
    button = driver.find_element(By.ID, "btn")
    button.click()

    output = driver.find_element(By.ID, "output")
    output_text = output.text
    print(f"✅ Output after click: {output_text}", flush=True)

    # Test 5: Execute JavaScript
    print("\nTest 5: Execute JavaScript", flush=True)
    result = driver.execute_script("return document.title;")
    print(f"✅ JS result: {result}", flush=True)

    print("\n" + "="*60, flush=True)
    print("ALL TESTS PASSED!", flush=True)
    print("="*60, flush=True)

    driver.quit()

except Exception as e:
    print(f"\n❌ Test failed: {e}", flush=True)
    import traceback
    traceback.print_exc()
