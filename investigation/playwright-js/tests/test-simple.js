#!/usr/bin/env node
/**
 * シンプルなPlaywright + プロキシテスト
 *
 * 使用方法:
 * 1. ターミナル1でプロキシ起動: npm run proxy
 * 2. ターミナル2でこのスクリプト実行: node tests/test-simple.js
 */

import { chromium } from 'playwright';

const PROXY_URL = 'http://127.0.0.1:8888';
const TEST_URL = 'https://example.com';

async function test() {
  console.log('🎭 Starting simple Playwright test...\n');
  console.log(`📍 Proxy: ${PROXY_URL}`);
  console.log(`🔗 URL: ${TEST_URL}\n`);

  let browser = null;

  try {
    console.log('⏳ Launching browser...');
    browser = await chromium.launch({
      headless: true,
      proxy: { server: PROXY_URL },
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    });
    console.log('✅ Browser launched\n');

    const context = await browser.newContext({ ignoreHTTPSErrors: true });
    const page = await context.newPage();

    console.log('⏳ Navigating to page...');
    const response = await page.goto(TEST_URL, {
      waitUntil: 'domcontentloaded',
      timeout: 30000,
    });

    if (response) {
      console.log(`✅ Response: ${response.status()}`);
      const title = await page.title();
      console.log(`✅ Title: ${title}`);

      await page.screenshot({ path: 'tests/screenshot-simple.png' });
      console.log('✅ Screenshot saved\n');

      console.log('🎉 Test passed!\n');
    } else {
      console.log('❌ No response received\n');
    }

    await context.close();
  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
    if (error.stack) {
      console.error(error.stack);
    }
  } finally {
    if (browser) {
      await browser.close();
      console.log('🔒 Browser closed\n');
    }
  }
}

test();
