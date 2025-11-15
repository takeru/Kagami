#!/usr/bin/env python3
"""
MCP サーバーのツール一覧を取得するテストスクリプト
"""
import asyncio
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def list_mcp_tools():
    """MCPサーバーが提供するツール一覧を取得"""
    print("=" * 70)
    print("MCP サーバー ツール一覧取得テスト")
    print("=" * 70)
    print()

    # mcp.py経由でplaywrightサーバーに接続
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "playwright_mcp_claude_code_web/mcp.py"],
        env={
            **os.environ,
            "HOME": "/home/user"
        }
    )

    print("1. MCPサーバーに接続中...")
    print(f"   コマンド: {server_params.command} {' '.join(server_params.args)}")
    print()

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("✓ MCPサーバーに接続しました")
                print()

                # ツール一覧を取得
                print("2. 利用可能なツール一覧:")
                print("-" * 70)

                tools = await session.list_tools()

                if tools.tools:
                    for i, tool in enumerate(tools.tools, 1):
                        print(f"{i}. {tool.name}")
                        if hasattr(tool, 'description') and tool.description:
                            print(f"   説明: {tool.description}")
                        if hasattr(tool, 'inputSchema') and tool.inputSchema:
                            print(f"   パラメータ: {list(tool.inputSchema.get('properties', {}).keys())}")
                        print()

                    print("-" * 70)
                    print(f"✓ 合計 {len(tools.tools)} 個のツールが利用可能です")
                else:
                    print("⚠️ ツールが見つかりませんでした")

                print()
                return True

    except Exception as e:
        print()
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(list_mcp_tools())
    sys.exit(0 if success else 1)
