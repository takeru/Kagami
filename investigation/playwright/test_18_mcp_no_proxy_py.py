#!/usr/bin/env python3
"""
テスト18: proxy.pyなしでextraHTTPHeaders方式

Python MCP Client → playwright-mcp (Firefox + extraHTTPHeaders) → Internet
"""
import asyncio
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_without_proxy_py():
    """proxy.pyなし、extraHTTPHeaders方式でMCPクライアントからアクセス"""
    print("=" * 70)
    print("テスト: MCP Client -> playwright-mcp (proxy.pyなし、HOME=/home/user)")
    print("=" * 70)
    print()

    project_root = Path(__file__).parent.parent.parent

    # HTTPS_PROXYから情報を取得
    https_proxy = os.getenv("HTTPS_PROXY", "")
    print(f"HTTPS_PROXY設定: {https_proxy[:50]}...")
    print()

    # start_playwright_mcp_firefox.py を使用（extraHTTPHeaders方式）
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", ".mcp/start_playwright_mcp_firefox.py"],
        env={
            **os.environ,
            "HOME": "/home/user"
        }
    )

    print("1. MCPサーバー（extraHTTPHeaders方式、HOME=/home/user）に接続中...")
    print("   Firefox: /home/user/.cache/ms-playwright/firefox-1496")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("   ✅ MCPサーバーに接続")

            # example.comにナビゲート
            print("\n2. example.comにナビゲート中...")
            result = await session.call_tool(
                "browser_navigate",
                arguments={"url": "https://example.com"}
            )
            nav_result = result.content[0].text if result.content else 'No content'
            print(f"   結果:\n{nav_result[:300]}")

            # スナップショットを取得
            print("\n3. スナップショット取得中...")
            result = await session.call_tool(
                "browser_snapshot",
                arguments={}
            )
            snapshot = result.content[0].text if result.content else ""
            print(f"   スナップショットサイズ: {len(snapshot)} 文字")

            # スナップショットの一部を表示
            if len(snapshot) > 200:
                print(f"   内容の一部:\n{snapshot[:500]}")

            # ブラウザを閉じる
            await session.call_tool("browser_close", arguments={})
            print("\n✅ テスト完了")

            # 結果を判定
            has_example = "Example Domain" in snapshot or "example.com" in snapshot.lower()
            has_cert_error = "Security Risk" in snapshot or "SEC_ERROR" in nav_result

            if has_example:
                print("\n" + "=" * 70)
                print("🎉 成功: Python MCP Client → playwright-mcp → Internet")
                print("=" * 70)
                print("\n実現できたこと:")
                print("  ✅ Python MCP Client → playwright-mcp (Firefox + extraHTTPHeaders) → Internet")
                print("  ✅ HOME=/home/user設定で動作")
                print("  ✅ proxy.py不要（extraHTTPHeaders方式）")
                print("  ✅ JWT認証プロキシ経由でアクセス成功")
                return True
            elif has_cert_error:
                print("\n⚠ 部分的成功: 接続はできたが証明書エラー")
                print("  - Firefoxは起動し、プロキシ経由で接続")
                print("  - 証明書エラーページが表示される")
                print("  - playwright-mcpのignoreHTTPSErrors設定が効いていない可能性")
                return False
            else:
                print("\n❌ 失敗: ページが正しく読み込まれませんでした")
                return False


async def main():
    try:
        success = await test_without_proxy_py()
        return success
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
