#!/usr/bin/env node
/**
 * ローカルHTTP/HTTPSプロキシサーバー (JavaScript/Node.js版)
 *
 * Chromium/Playwright → localhost:8888 → JWT Proxy → Internet
 *
 * 機能:
 * - CONNECTトンネル対応（HTTPS対応）
 * - JWT認証プロキシへの透過的な転送
 * - 詳細なロギング
 */

import http from 'http';
import net from 'net';
import { URL } from 'url';

const LOCAL_HOST = '127.0.0.1';
const LOCAL_PORT = 8888;

// 環境変数から上流プロキシを取得
const upstreamProxyUrl = process.env.HTTPS_PROXY || process.env.HTTP_PROXY;

if (!upstreamProxyUrl) {
  console.error('❌ Error: HTTPS_PROXY or HTTP_PROXY environment variable not set');
  process.exit(1);
}

// プロキシURLをパース
let upstreamProxy;
try {
  upstreamProxy = new URL(upstreamProxyUrl);
  console.log('✅ Upstream proxy configured');
  console.log(`   Host: ${upstreamProxy.hostname}`);
  console.log(`   Port: ${upstreamProxy.port}`);
  console.log(`   Auth: ${upstreamProxy.username ? '✓ (JWT)' : '✗'}`);
} catch (error) {
  console.error('❌ Error parsing proxy URL:', error.message);
  process.exit(1);
}

/**
 * CONNECTメソッドを処理（HTTPSトンネル）
 */
function handleConnect(req, clientSocket, head) {
  const startTime = Date.now();
  const { host, port } = parseHostPort(req.url);

  console.log(`\n🔵 CONNECT ${host}:${port}`);
  console.log(`   Client: ${clientSocket.remoteAddress}:${clientSocket.remotePort}`);

  // 上流プロキシへの接続
  const proxySocket = net.connect({
    host: upstreamProxy.hostname,
    port: parseInt(upstreamProxy.port),
  }, () => {
    console.log(`   ✓ Connected to upstream proxy (${Date.now() - startTime}ms)`);

    // 上流プロキシにCONNECTリクエストを送信
    const connectRequest = [
      `CONNECT ${host}:${port} HTTP/1.1`,
      `Host: ${host}:${port}`,
    ];

    // JWT認証情報を追加
    if (upstreamProxy.username) {
      const auth = Buffer.from(
        `${decodeURIComponent(upstreamProxy.username)}:${decodeURIComponent(upstreamProxy.password)}`
      ).toString('base64');
      connectRequest.push(`Proxy-Authorization: Basic ${auth}`);
    }

    connectRequest.push('', '');

    const requestData = connectRequest.join('\r\n');
    console.log(`   → Sending CONNECT to upstream proxy`);
    proxySocket.write(requestData);
  });

  // プロキシからの応答を処理
  let receivedResponse = false;
  proxySocket.once('data', (data) => {
    receivedResponse = true;
    const response = data.toString();
    console.log(`   ← Response from upstream proxy: ${response.split('\r\n')[0]}`);

    if (response.includes('200') || response.includes('Connection established')) {
      console.log(`   ✓ Tunnel established (${Date.now() - startTime}ms)`);

      // クライアントに成功を通知
      clientSocket.write('HTTP/1.1 200 Connection Established\r\n\r\n');

      // 双方向にデータをパイプ
      proxySocket.pipe(clientSocket);
      clientSocket.pipe(proxySocket);

      // HEADデータがあれば転送
      if (head && head.length > 0) {
        proxySocket.write(head);
      }
    } else {
      console.log(`   ✗ Tunnel failed: ${response.split('\r\n')[0]}`);
      clientSocket.end('HTTP/1.1 502 Bad Gateway\r\n\r\n');
      proxySocket.end();
    }
  });

  // エラーハンドリング
  proxySocket.on('error', (error) => {
    console.log(`   ✗ Proxy socket error: ${error.message}`);
    if (!receivedResponse) {
      clientSocket.end('HTTP/1.1 502 Bad Gateway\r\n\r\n');
    }
  });

  clientSocket.on('error', (error) => {
    console.log(`   ✗ Client socket error: ${error.message}`);
    proxySocket.end();
  });

  proxySocket.on('end', () => {
    console.log(`   ⚫ Proxy connection closed (${Date.now() - startTime}ms)`);
  });

  clientSocket.on('end', () => {
    console.log(`   ⚫ Client connection closed (${Date.now() - startTime}ms)`);
  });
}

/**
 * 通常のHTTPリクエストを処理
 */
function handleHttpRequest(req, res) {
  const startTime = Date.now();
  console.log(`\n🟢 ${req.method} ${req.url}`);
  console.log(`   Headers:`, Object.keys(req.headers).length);

  // 上流プロキシへのリクエスト作成
  const options = {
    method: req.method,
    host: upstreamProxy.hostname,
    port: parseInt(upstreamProxy.port),
    path: req.url,
    headers: { ...req.headers },
  };

  // JWT認証情報を追加
  if (upstreamProxy.username) {
    const auth = Buffer.from(
      `${decodeURIComponent(upstreamProxy.username)}:${decodeURIComponent(upstreamProxy.password)}`
    ).toString('base64');
    options.headers['Proxy-Authorization'] = `Basic ${auth}`;
  }

  const proxyReq = http.request(options, (proxyRes) => {
    console.log(`   ← Status: ${proxyRes.statusCode} (${Date.now() - startTime}ms)`);

    res.writeHead(proxyRes.statusCode, proxyRes.headers);
    proxyRes.pipe(res);
  });

  proxyReq.on('error', (error) => {
    console.log(`   ✗ Request error: ${error.message}`);
    res.writeHead(502);
    res.end('Bad Gateway');
  });

  req.pipe(proxyReq);
}

/**
 * ホスト名とポートをパース
 */
function parseHostPort(hostPort) {
  const [host, port = '443'] = hostPort.split(':');
  return { host, port };
}

/**
 * プロキシサーバーを起動
 */
function startProxyServer() {
  const server = http.createServer(handleHttpRequest);

  // CONNECTメソッドのハンドラー
  server.on('connect', handleConnect);

  server.listen(LOCAL_PORT, LOCAL_HOST, () => {
    console.log('\n' + '='.repeat(70));
    console.log('🚀 Local Proxy Server Started (JavaScript/Node.js)');
    console.log('='.repeat(70));
    console.log(`📍 Listening: http://${LOCAL_HOST}:${LOCAL_PORT}`);
    console.log(`🔗 Upstream: ${upstreamProxy.hostname}:${upstreamProxy.port}`);
    console.log(`🔑 Auth: ${upstreamProxy.username ? 'JWT/Bearer' : 'None'}`);
    console.log('');
    console.log('📖 Usage with Playwright:');
    console.log('   const browser = await chromium.launch({');
    console.log(`     proxy: { server: 'http://${LOCAL_HOST}:${LOCAL_PORT}' }`);
    console.log('   });');
    console.log('='.repeat(70));
    console.log('\n✅ Server ready. Press Ctrl+C to stop\n');
  });

  server.on('error', (error) => {
    console.error('❌ Server error:', error.message);
    process.exit(1);
  });

  // Graceful shutdown
  process.on('SIGINT', () => {
    console.log('\n\n👋 Shutting down proxy server...');
    server.close(() => {
      console.log('✅ Server stopped');
      process.exit(0);
    });
  });
}

// サーバー起動
startProxyServer();
