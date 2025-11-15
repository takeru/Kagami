#!/usr/bin/env python3
"""
テスト19: 証明書エラーページをバイパスする試み

proxy.py方式 + 証明書エラーページで「Advanced」→「Continue」をクリック
"""
import asyncio
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_bypass_cert_error():
    """証明書エラーページをバイパス"""
    print("=" * 70)
    print("テスト: 証明書エラーページのバイパス試行")
    print("=" * 70)
    print()

    project_root = Path(__file__).parent.parent.parent

    # proxy.pyを起動するコマンド（HOME=/home/user）
    server_params = StdioServerParameters(
        command="bash",
        args=[
            "-c",
            'uv run proxy --hostname 127.0.0.1 --port 18911 --plugins proxy.plugin.proxy_pool.ProxyPoolPlugin --proxy-pool "$HTTPS_PROXY" >/dev/null 2>&1 & PROXY_PID=$!; trap "kill $PROXY_PID 2>/dev/null" EXIT; sleep 2; node /opt/node22/lib/node_modules/@playwright/mcp/cli.js --config .mcp/playwright-firefox-config.json --browser firefox --proxy-server http://127.0.0.1:18911'
        ],
        env={
            **os.environ,
            "HOME": "/home/user"
        }
    )

    print("1. MCPサーバーに接続中...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("   ✅ MCPサーバーに接続")

            # example.comにナビゲート
            print("\n2. example.comにナビゲート中...")
            try:
                result = await session.call_tool(
                    "browser_navigate",
                    arguments={"url": "https://example.com"}
                )
                nav_result = result.content[0].text if result.content else ''
                print(f"   結果: {nav_result[:200]}")
            except Exception as e:
                print(f"   ⚠ エラー: {e}")

            # スナップショットを取得して、証明書エラーページか確認
            print("\n3. ページ状態を確認中...")
            result = await session.call_tool(
                "browser_snapshot",
                arguments={}
            )
            snapshot = result.content[0].text if result.content else ""
            print(f"   スナップショットサイズ: {len(snapshot)} 文字")

            if "Security Risk" in snapshot:
                print("   ⚠ 証明書エラーページを検出")
                print("\n4. 証明書エラーをバイパスするボタンを探します...")

                # スナップショットから「Advanced」や「Accept」ボタンを探す
                lines = snapshot.split('\n')
                for i, line in enumerate(lines):
                    if 'button' in line.lower() or 'link' in line.lower():
                        if any(keyword in line.lower() for keyword in ['advanced', 'accept', 'continue', 'proceed']):
                            print(f"     候補: {line.strip()}")

                # 「Advanced」ボタンを探してクリックを試みる
                # TODO: browser_clickツールを使ってボタンをクリック
                print("\n   📝 Note: MCPではref指定が必要なため、手動でのクリックは難しい")
                print("        別のアプローチが必要（Firefoxの設定強化）")

            else:
                print("   ✅ 証明書エラーページではありません")

            # ブラウザを閉じる
            await session.call_tool("browser_close", arguments={})
            print("\n✅ テスト完了")

            # スナップショットの詳細を表示
            print("\n" + "=" * 70)
            print("スナップショット詳細:")
            print("=" * 70)
            print(snapshot[:2000])

            return "Example Domain" in snapshot


async def main():
    try:
        success = await test_bypass_cert_error()
        return success
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
