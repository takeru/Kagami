"""
ブラウザ拡張機能を使わずにHTTPOnly Cookieも取得する方法

開発者ツールのApplicationタブから直接Cookieをコピーする
"""

instructions = """
======================================================================
📋 すべてのCookie（HTTPOnly含む）を取得する方法
======================================================================

【方法1: 開発者ツールから直接取得（推奨）】

1. ローカルのブラウザでhttps://claude.ai/codeを開いてログイン

2. F12キーで開発者ツールを開く

3. 「Application」タブ（Chrome）または「Storage」タブ（Firefox）を開く

4. 左側のメニューで「Cookies」→「https://claude.ai」を選択

5. 以下のJavaScriptをConsoleで実行してJSONを生成:

----------------------------------------------------------------------
// 開発者ツールのApplicationタブで見えるCookieを手動でJSON化
// 以下のテンプレートを使用して、各Cookieの値を入力してください

const cookies = [
  // ★ sessionKey が最も重要！
  {
    name: "sessionKey",
    value: "ここにsessionKeyの値を貼り付け",
    domain: ".claude.ai",
    path: "/",
    httpOnly: true,
    secure: true,
    sameSite: "Lax"
  },
  // __Secure- で始まるCookieも重要
  {
    name: "__Secure-next-auth.session-token",  // 例
    value: "値があれば貼り付け",
    domain: ".claude.ai",
    path: "/",
    httpOnly: true,
    secure: true,
    sameSite: "Lax"
  },
  // その他のCookieも追加...
];

// JSON化してbase64エンコード
const cookiesJson = JSON.stringify(cookies);
const cookiesBase64 = btoa(unescape(encodeURIComponent(cookiesJson)));
copy(cookiesBase64);
console.log('✅ Cookieをbase64エンコードしてクリップボードにコピーしました！');
console.log('Cookie数:', cookies.length);
console.log('エンコード後のサイズ:', cookiesBase64.length, '文字');
----------------------------------------------------------------------

6. Applicationタブで見える全てのCookieを上記のテンプレートに追加

7. 特に以下のCookieを必ず含めること:
   - sessionKey (HTTPOnly) ★最重要★
   - __Secure- で始まるCookie
   - anthropic-device-id
   - lastActiveOrg
   - その他すべてのCookie

8. 生成されたbase64文字列をコピー

9. 環境変数に設定:
   export CLAUDE_COOKIES_BASE64='<生成したbase64文字列>'

10. スクリプトを再実行


【方法2: ブラウザ拡張機能を使用（より簡単）】

Chrome: EditThisCookie
https://chrome.google.com/webstore/detail/editthiscookie/

Firefox: Cookie Editor
https://addons.mozilla.org/firefox/addon/cookie-editor/

拡張機能をインストール後:
1. claude.ai/codeでログイン
2. 拡張機能アイコンをクリック
3. 「Export」でJSON形式でエクスポート
4. 以下のコードでbase64エンコード:

----------------------------------------------------------------------
// エクスポートしたJSON配列を貼り付け
const cookies = [... ここに拡張機能からエクスポートしたJSONを貼り付け ...];

// base64エンコード
const cookiesJson = JSON.stringify(cookies);
const cookiesBase64 = btoa(unescape(encodeURIComponent(cookiesJson)));
copy(cookiesBase64);
console.log('✅ base64エンコード完了！');
----------------------------------------------------------------------

======================================================================
"""

print(instructions)
