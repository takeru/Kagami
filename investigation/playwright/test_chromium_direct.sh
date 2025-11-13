#!/bin/bash
# Chromiumを直接コマンドラインから使用するテスト

set -e

CHROMIUM="/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome"
OUTPUT_DIR="/home/user/Kagami/investigation/playwright"

echo "============================================================"
echo "Chromium Direct Command Line Test"
echo "============================================================"
echo

# Test 1: Simple screenshot without proxy
echo "Test 1: Screenshot of data: URL (no proxy)"
echo "-----------------------------------------------------------"
timeout 10 "$CHROMIUM" \
    --headless \
    --no-sandbox \
    --disable-setuid-sandbox \
    --disable-gpu \
    --disable-dev-shm-usage \
    --screenshot="${OUTPUT_DIR}/chromium_data_url.png" \
    "data:text/html,<html><body><h1>Hello from Chromium!</h1></body></html>" \
    2>&1 | head -20

if [ -f "${OUTPUT_DIR}/chromium_data_url.png" ]; then
    echo "✅ Screenshot created successfully"
    ls -lh "${OUTPUT_DIR}/chromium_data_url.png"
else
    echo "❌ Screenshot not created"
fi
echo

# Test 2: Screenshot with proxy
echo "Test 2: Screenshot with proxy (example.com)"
echo "-----------------------------------------------------------"

# まずローカルプロキシを起動（バックグラウンド）
python3 << 'PYTHON_SCRIPT' &
import sys
import os
sys.path.insert(0, '/home/user/Kagami')
from src.local_proxy import run_proxy_server
run_proxy_server(port=8889)
PYTHON_SCRIPT

PROXY_PID=$!
echo "Started local proxy (PID: $PROXY_PID)"
sleep 3

# Chromiumでプロキシ経由アクセス
timeout 15 "$CHROMIUM" \
    --headless \
    --no-sandbox \
    --disable-setuid-sandbox \
    --disable-gpu \
    --disable-dev-shm-usage \
    --proxy-server="http://127.0.0.1:8889" \
    --ignore-certificate-errors \
    --screenshot="${OUTPUT_DIR}/chromium_example_proxy.png" \
    "https://example.com" \
    2>&1 | head -30 &

CHROMIUM_PID=$!
echo "Started Chromium (PID: $CHROMIUM_PID)"

# 15秒待つ
sleep 15

# プロセスをクリーンアップ
kill $CHROMIUM_PID 2>/dev/null || true
kill $PROXY_PID 2>/dev/null || true

if [ -f "${OUTPUT_DIR}/chromium_example_proxy.png" ]; then
    echo "✅ Screenshot created successfully"
    ls -lh "${OUTPUT_DIR}/chromium_example_proxy.png"
else
    echo "❌ Screenshot not created (likely timeout)"
fi
echo

# Test 3: PDF generation (no proxy)
echo "Test 3: PDF generation of data: URL"
echo "-----------------------------------------------------------"
timeout 10 "$CHROMIUM" \
    --headless \
    --no-sandbox \
    --disable-setuid-sandbox \
    --disable-gpu \
    --disable-dev-shm-usage \
    --print-to-pdf="${OUTPUT_DIR}/chromium_test.pdf" \
    "data:text/html,<html><body><h1>PDF Test</h1><p>This is a test PDF</p></body></html>" \
    2>&1 | head -20

if [ -f "${OUTPUT_DIR}/chromium_test.pdf" ]; then
    echo "✅ PDF created successfully"
    ls -lh "${OUTPUT_DIR}/chromium_test.pdf"
else
    echo "❌ PDF not created"
fi
echo

echo "============================================================"
echo "Summary"
echo "============================================================"
echo "Chromiumバイナリの直接実行テストが完了しました"
echo
echo "作成されたファイル:"
ls -lh "${OUTPUT_DIR}"/chromium_* 2>/dev/null || echo "(none)"
