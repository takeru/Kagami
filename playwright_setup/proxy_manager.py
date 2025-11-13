#!/usr/bin/env python3
"""
プロキシマネージャー

バックグラウンドでproxy.pyを起動・停止・状態確認するユーティリティ

使い方:
    # プロキシを起動
    uv run python playwright_setup/proxy_manager.py start

    # 状態確認
    uv run python playwright_setup/proxy_manager.py status

    # プロキシを停止
    uv run python playwright_setup/proxy_manager.py stop

    # プロキシのログを表示
    uv run python playwright_setup/proxy_manager.py logs
"""
import subprocess
import sys
import os
import signal
import time
from pathlib import Path


# プロキシ設定
PROXY_HOST = "127.0.0.1"
PROXY_PORT = 8900
PID_FILE = Path("/tmp/playwright_proxy.pid")
LOG_FILE = Path("/tmp/playwright_proxy.log")


def is_running():
    """プロキシが動作中かチェック"""
    if not PID_FILE.exists():
        return False

    try:
        pid = int(PID_FILE.read_text())
        # プロセスが存在するか確認
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, ValueError):
        # プロセスが存在しない
        PID_FILE.unlink(missing_ok=True)
        return False


def get_pid():
    """プロキシのPIDを取得"""
    if not PID_FILE.exists():
        return None
    try:
        return int(PID_FILE.read_text())
    except ValueError:
        return None


def start_proxy():
    """プロキシを起動"""
    if is_running():
        print(f"⚠️  プロキシは既に起動しています (PID: {get_pid()})")
        print(f"   http://{PROXY_HOST}:{PROXY_PORT}")
        return

    # 環境変数の確認
    if not os.getenv("HTTPS_PROXY"):
        print("❌ エラー: HTTPS_PROXY 環境変数が設定されていません")
        sys.exit(1)

    print("="*60)
    print("プロキシを起動...")
    print("="*60)

    # ログファイルを開く
    log_file = open(LOG_FILE, "w")

    # プロキシを起動
    process = subprocess.Popen(
        [
            'uv', 'run', 'proxy',
            '--hostname', PROXY_HOST,
            '--port', str(PROXY_PORT),
            '--plugins', 'proxy.plugin.proxy_pool.ProxyPoolPlugin',
            '--proxy-pool', os.environ['HTTPS_PROXY'],
        ],
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,  # デーモン化
    )

    # PIDを保存
    PID_FILE.write_text(str(process.pid))

    # 起動を待機
    print("起動中...")
    time.sleep(3)

    if is_running():
        print(f"✅ プロキシが起動しました")
        print(f"   PID: {process.pid}")
        print(f"   URL: http://{PROXY_HOST}:{PROXY_PORT}")
        print(f"   ログ: {LOG_FILE}")
        print(f"\nこのプロキシは以下で使用できます:")
        print(f"   browser.launch(args=['--proxy-server=http://{PROXY_HOST}:{PROXY_PORT}'])")
    else:
        print(f"❌ プロキシの起動に失敗しました")
        print(f"   ログを確認してください: {LOG_FILE}")
        sys.exit(1)


def stop_proxy():
    """プロキシを停止"""
    if not is_running():
        print("⚠️  プロキシは起動していません")
        PID_FILE.unlink(missing_ok=True)
        return

    pid = get_pid()
    print("="*60)
    print(f"プロキシを停止... (PID: {pid})")
    print("="*60)

    try:
        # SIGTERM を送信
        os.kill(pid, signal.SIGTERM)

        # 終了を待機（最大5秒）
        for i in range(10):
            time.sleep(0.5)
            if not is_running():
                break
        else:
            # 強制終了
            print("⚠️  正常終了しないため強制終了します")
            os.kill(pid, signal.SIGKILL)
            time.sleep(0.5)

        PID_FILE.unlink(missing_ok=True)
        print("✅ プロキシを停止しました")

    except ProcessLookupError:
        print("⚠️  プロセスが見つかりません")
        PID_FILE.unlink(missing_ok=True)


def show_status():
    """プロキシの状態を表示"""
    print("="*60)
    print("プロキシの状態")
    print("="*60)

    if is_running():
        pid = get_pid()
        print(f"✅ 起動中")
        print(f"   PID: {pid}")
        print(f"   URL: http://{PROXY_HOST}:{PROXY_PORT}")
        print(f"   ログ: {LOG_FILE}")

        # プロセス情報を取得
        try:
            result = subprocess.run(
                ["ps", "-p", str(pid), "-o", "rss,vsz,pmem,pcpu,etime"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    print(f"\nリソース使用状況:")
                    print(f"   {lines[0]}")
                    print(f"   {lines[1]}")
        except:
            pass

    else:
        print("❌ 停止中")
        if PID_FILE.exists():
            print(f"   （PIDファイルのみ存在: {PID_FILE}）")


def show_logs():
    """ログを表示"""
    print("="*60)
    print(f"プロキシログ: {LOG_FILE}")
    print("="*60)

    if not LOG_FILE.exists():
        print("❌ ログファイルが存在しません")
        return

    # 最新50行を表示
    try:
        result = subprocess.run(
            ["tail", "-n", "50", str(LOG_FILE)],
            capture_output=True,
            text=True
        )
        print(result.stdout)
    except Exception as e:
        print(f"❌ ログの読み込みに失敗: {e}")


def main():
    if len(sys.argv) < 2:
        print("使い方:")
        print("  uv run python playwright_setup/proxy_manager.py start   # プロキシを起動")
        print("  uv run python playwright_setup/proxy_manager.py stop    # プロキシを停止")
        print("  uv run python playwright_setup/proxy_manager.py status  # 状態確認")
        print("  uv run python playwright_setup/proxy_manager.py logs    # ログ表示")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "start":
        start_proxy()
    elif command == "stop":
        stop_proxy()
    elif command == "status":
        show_status()
    elif command == "logs":
        show_logs()
    else:
        print(f"❌ 不明なコマンド: {command}")
        print("   start, stop, status, logs のいずれかを指定してください")
        sys.exit(1)


if __name__ == "__main__":
    main()
