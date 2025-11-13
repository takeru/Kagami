#!/usr/bin/env node
/**
 * Playwright + ローカルプロキシ統合テスト
 *
 * このスクリプトを実行する前に、別ターミナルで以下を実行してください:
 *   npm run proxy
 *
 * または、このスクリプトが自動的にプロキシサーバーを起動します。
 */

import { chromium } from 'playwright';
import { spawn } from 'child_process';
import { setTimeout } from 'timers/promises';

const PROXY_HOST = '127.0.0.1';
const PROXY_PORT = 8888;
const PROXY_URL = `http://${PROXY_HOST}:${PROXY_PORT}`;

// テストするURL
const TEST_URLS = [
  { name: 'HTTPBin HTTPS', url: 'https://httpbin.org/html' },
  { name: 'Google', url: 'https://www.google.com' },
  { name: 'Example.com', url: 'https://example.com' },
  { name: 'Claude.ai Login', url: 'https://claude.ai/login' },
];

let proxyProcess = null;

/**
 * プロキシサーバーを起動
 */
async function startProxyServer() {
  console.log('🚀 Starting local proxy server...\n');

  proxyProcess = spawn('node', ['src/local-proxy.js'], {
    cwd: process.cwd(),
    stdio: 'inherit',
    env: process.env,
  });

  proxyProcess.on('error', (error) => {
    console.error('❌ Failed to start proxy server:', error.message);
    process.exit(1);
  });

  // サーバーが起動するまで待機
  await setTimeout(2000);
  console.log('✅ Proxy server started\n');
}

/**
 * プロキシサーバーを停止
 */
function stopProxyServer() {
  if (proxyProcess) {
    console.log('\n🛑 Stopping proxy server...');
    proxyProcess.kill('SIGINT');
    proxyProcess = null;
  }
}

/**
 * Playwrightでテスト実行
 */
async function runTests() {
  console.log('='.repeat(70));
  console.log('🎭 Playwright + Local Proxy Integration Test');
  console.log('='.repeat(70));
  console.log(`📍 Proxy: ${PROXY_URL}`);
  console.log(`🔍 Tests: ${TEST_URLS.length} URLs`);
  console.log('='.repeat(70));
  console.log('');

  let browser = null;
  const results = [];

  try {
    // Chromiumを起動（プロキシ設定付き）
    console.log('🌐 Launching Chromium with proxy...\n');
    browser = await chromium.launch({
      headless: true,
      proxy: {
        server: PROXY_URL,
      },
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        // プロキシ関連のフラグ
        '--disable-features=NetworkService',
        '--disable-features=VizDisplayCompositor',
      ],
    });

    console.log('✅ Browser launched\n');

    const context = await browser.newContext({
      ignoreHTTPSErrors: true, // 証明書エラーを無視
    });

    const page = await context.newPage();

    // 各URLをテスト
    for (const test of TEST_URLS) {
      console.log(`\n${'─'.repeat(70)}`);
      console.log(`📄 Testing: ${test.name}`);
      console.log(`🔗 URL: ${test.url}`);
      console.log('');

      const startTime = Date.now();
      let result = {
        name: test.name,
        url: test.url,
        success: false,
        error: null,
        duration: 0,
        title: null,
      };

      try {
        // ページにアクセス（タイムアウト30秒）
        console.log('   ⏳ Navigating...');
        const response = await page.goto(test.url, {
          waitUntil: 'domcontentloaded',
          timeout: 30000,
        });

        result.duration = Date.now() - startTime;

        if (response) {
          console.log(`   ✓ Response: ${response.status()} ${response.statusText()}`);
          console.log(`   ✓ Duration: ${result.duration}ms`);

          // タイトルを取得
          try {
            result.title = await page.title();
            console.log(`   ✓ Title: ${result.title}`);
          } catch (titleError) {
            console.log(`   ⚠ Could not get title: ${titleError.message}`);
          }

          // スクリーンショットを保存
          const screenshotPath = `tests/screenshot-${test.name.toLowerCase().replace(/\s+/g, '-')}.png`;
          await page.screenshot({ path: screenshotPath });
          console.log(`   ✓ Screenshot saved: ${screenshotPath}`);

          result.success = true;
          console.log(`   ✅ SUCCESS`);
        } else {
          console.log(`   ⚠ No response received`);
          result.error = 'No response';
        }
      } catch (error) {
        result.duration = Date.now() - startTime;
        result.error = error.message;
        console.log(`   ✗ Error: ${error.message}`);
        console.log(`   ✗ Duration: ${result.duration}ms`);
        console.log(`   ❌ FAILED`);
      }

      results.push(result);
    }

    await context.close();
  } catch (error) {
    console.error('\n❌ Fatal error:', error.message);
    console.error(error.stack);
  } finally {
    if (browser) {
      await browser.close();
      console.log('\n🔒 Browser closed');
    }
  }

  // 結果サマリー
  console.log('\n\n' + '='.repeat(70));
  console.log('📊 Test Results Summary');
  console.log('='.repeat(70));
  console.log('');

  const successCount = results.filter((r) => r.success).length;
  const failCount = results.length - successCount;

  results.forEach((result, index) => {
    const icon = result.success ? '✅' : '❌';
    console.log(`${icon} ${index + 1}. ${result.name}`);
    console.log(`   URL: ${result.url}`);
    console.log(`   Duration: ${result.duration}ms`);
    if (result.title) {
      console.log(`   Title: ${result.title}`);
    }
    if (result.error) {
      console.log(`   Error: ${result.error}`);
    }
    console.log('');
  });

  console.log('─'.repeat(70));
  console.log(`Total: ${results.length} | Success: ${successCount} | Failed: ${failCount}`);
  console.log('='.repeat(70));
  console.log('');

  return successCount > 0 ? 0 : 1;
}

/**
 * メイン処理
 */
async function main() {
  let exitCode = 1;

  try {
    // プロキシサーバーを起動
    await startProxyServer();

    // テスト実行
    exitCode = await runTests();
  } catch (error) {
    console.error('\n❌ Unexpected error:', error.message);
    console.error(error.stack);
  } finally {
    // クリーンアップ
    stopProxyServer();
  }

  process.exit(exitCode);
}

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n\n👋 Interrupted by user');
  stopProxyServer();
  process.exit(1);
});

// 実行
main();
