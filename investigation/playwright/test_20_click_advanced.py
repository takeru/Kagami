#!/usr/bin/env python3
"""
テスト20: 証明書エラーページで「Advanced」ボタンをクリック

proxy.py方式 + 証明書エラーページで「Advanced」→「Accept the Risk」をクリック
"""
import asyncio
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_click_advanced_button():
    """証明書エラーページで「Advanced」ボタンをクリック"""
    print("=" * 70)
    print("テスト: 証明書エラーページで「Advanced」をクリック")
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
            except Exception as e:
                print(f"   ⚠ エラー（expected）: {e}")

            # スナップショットを取得
            print("\n3. ページ状態を確認中...")
            result = await session.call_tool(
                "browser_snapshot",
                arguments={}
            )
            snapshot = result.content[0].text if result.content else ""

            if "Security Risk" in snapshot and "[ref=e16]" in snapshot:
                print("   ✅ 証明書エラーページを検出")
                print("\n4. 「Advanced…」ボタンをクリック中...")

                # browser_clickツールで「Advanced」ボタンをクリック
                try:
                    result = await session.call_tool(
                        "browser_click",
                        arguments={
                            "element": "Advanced… button",
                            "ref": "e16"
                        }
                    )
                    print("   ✅ 「Advanced」ボタンをクリック成功")
                    print(f"   結果: {result.content[0].text if result.content else 'No content'}")
                except Exception as e:
                    print(f"   ❌ クリック失敗: {e}")

                # クリック後のスナップショットを取得
                print("\n5. クリック後のページ状態を確認中...")
                result = await session.call_tool(
                    "browser_snapshot",
                    arguments={}
                )
                snapshot_after = result.content[0].text if result.content else ""
                print(f"   スナップショットサイズ: {len(snapshot_after)} 文字")

                # 「Accept the Risk」ボタンを探す
                if "accept" in snapshot_after.lower() or "continue" in snapshot_after.lower():
                    print("\n   ✅ 新しいオプションが表示されました")
                    lines = snapshot_after.split('\n')
                    for line in lines:
                        if 'button' in line.lower() or 'link' in line.lower():
                            if any(keyword in line.lower() for keyword in ['accept', 'continue', 'proceed', 'exception']):
                                print(f"     候補: {line.strip()}")

                    print("\n6. スナップショット詳細:")
                    print(snapshot_after[:2000])

            # ブラウザを閉じる
            await session.call_tool("browser_close", arguments={})
            print("\n✅ テスト完了")

            return "Example Domain" in snapshot_after if 'snapshot_after' in locals() else False


async def main():
    try:
        success = await test_click_advanced_button()
        return success
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
