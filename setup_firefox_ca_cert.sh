#!/bin/bash
set -e

echo "======================================================================="
echo "Firefox CA証明書インポート - セットアップスクリプト"
echo "======================================================================="
echo ""

# カラー定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ステップ1: certutilのインストール確認
echo "ステップ1: certutilのインストール確認..."
if ! command -v certutil &> /dev/null; then
    echo -e "${YELLOW}certutilがインストールされていません。インストール中...${NC}"
    apt-get update -qq
    apt-get install -y libnss3-tools > /dev/null 2>&1
    echo -e "${GREEN}✓ certutilをインストールしました${NC}"
else
    echo -e "${GREEN}✓ certutilは既にインストールされています${NC}"
fi

# ステップ2: Firefoxプロファイルの作成
echo ""
echo "ステップ2: Firefoxプロファイルの作成..."
PROFILE_DIR="/home/user/firefox-profile"

if [ -d "$PROFILE_DIR" ] && [ -f "$PROFILE_DIR/cert9.db" ]; then
    echo -e "${YELLOW}プロファイルは既に存在します: $PROFILE_DIR${NC}"
    read -p "既存のプロファイルを削除して再作成しますか？ (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$PROFILE_DIR"
        echo -e "${GREEN}✓ 既存のプロファイルを削除しました${NC}"
    else
        echo "既存のプロファイルを使用します"
    fi
fi

if [ ! -d "$PROFILE_DIR" ] || [ ! -f "$PROFILE_DIR/cert9.db" ]; then
    mkdir -p "$PROFILE_DIR"
    certutil -N -d sql:"$PROFILE_DIR" --empty-password
    echo -e "${GREEN}✓ Firefoxプロファイルを作成しました: $PROFILE_DIR${NC}"
fi

# ステップ3: CA証明書の確認
echo ""
echo "ステップ3: CA証明書の確認..."
STAGING_CERT="/usr/local/share/ca-certificates/swp-ca-staging.crt"
PRODUCTION_CERT="/usr/local/share/ca-certificates/swp-ca-production.crt"

if [ ! -f "$STAGING_CERT" ]; then
    echo -e "${RED}✗ staging CA証明書が見つかりません: $STAGING_CERT${NC}"
    exit 1
fi

if [ ! -f "$PRODUCTION_CERT" ]; then
    echo -e "${RED}✗ production CA証明書が見つかりません: $PRODUCTION_CERT${NC}"
    exit 1
fi

echo -e "${GREEN}✓ CA証明書が見つかりました${NC}"

# ステップ4: CA証明書のインポート
echo ""
echo "ステップ4: CA証明書のインポート..."

# staging CA
if certutil -L -d sql:"$PROFILE_DIR" -n "Anthropic TLS Inspection CA" &> /dev/null; then
    echo -e "${YELLOW}staging CA証明書は既にインポートされています${NC}"
else
    certutil -A -n "Anthropic TLS Inspection CA" -t "C,," -i "$STAGING_CERT" -d sql:"$PROFILE_DIR"
    echo -e "${GREEN}✓ staging CA証明書をインポートしました${NC}"
fi

# production CA
if certutil -L -d sql:"$PROFILE_DIR" -n "Anthropic TLS Inspection CA Production" &> /dev/null; then
    echo -e "${YELLOW}production CA証明書は既にインポートされています${NC}"
else
    certutil -A -n "Anthropic TLS Inspection CA Production" -t "C,," -i "$PRODUCTION_CERT" -d sql:"$PROFILE_DIR"
    echo -e "${GREEN}✓ production CA証明書をインポートしました${NC}"
fi

# ステップ5: インポート結果の確認
echo ""
echo "ステップ5: インポート結果の確認..."
echo ""
echo "インポートされた証明書:"
echo "----------------------------------------"
certutil -L -d sql:"$PROFILE_DIR" | grep -i anthropic || true
echo "----------------------------------------"

# ステップ6: Firefox build v1496の確認
echo ""
echo "ステップ6: Firefox build v1496の確認..."
FIREFOX_BUILD="/home/user/.cache/ms-playwright/firefox-1496"

if [ -d "$FIREFOX_BUILD" ]; then
    echo -e "${GREEN}✓ Firefox build v1496がインストールされています: $FIREFOX_BUILD${NC}"
else
    echo -e "${YELLOW}Firefox build v1496がインストールされていません${NC}"
    echo "インストール中... (数分かかる場合があります)"
    HOME=/home/user node /opt/node22/lib/node_modules/@playwright/mcp/node_modules/playwright/cli.js install firefox
    echo -e "${GREEN}✓ Firefox build v1496をインストールしました${NC}"
fi

# ステップ7: システム証明書ストアの更新（オプション）
echo ""
echo "ステップ7: システム証明書ストアの更新（オプション）..."
echo -e "${YELLOW}注: Firefoxのためには不要です（curl等のために実行）${NC}"
update-ca-certificates --fresh > /dev/null 2>&1
echo -e "${GREEN}✓ システム証明書ストアを更新しました${NC}"
echo ""
echo "補足:"
echo "  - Firefoxは独自の証明書ストア（cert9.db）を使用"
echo "  - システム証明書ストアはcurl、wget等のために更新"
echo ""

# 完了
echo ""
echo "======================================================================="
echo -e "${GREEN}セットアップが完了しました！${NC}"
echo "======================================================================="
echo ""
echo "次のステップ:"
echo "  1. テストを実行:"
echo "     HOME=/home/user uv run python investigation/playwright/test_24_firefox_profile_with_proxy_py.py"
echo ""
echo "  2. 詳細なドキュメント:"
echo "     cat investigation/playwright/CA_CERTIFICATE_IMPORT_GUIDE.md"
echo ""
echo "チェックリスト:"
echo "  ✓ certutilがインストールされています"
echo "  ✓ Firefoxプロファイルが作成されています: $PROFILE_DIR"
echo "  ✓ CA証明書がインポートされています (Trust: C,,)"
echo "  ✓ Firefox build v1496がインストールされています"
echo "  ✓ システム証明書ストアが更新されています"
echo ""
echo "これで証明書エラーなしでHTTPSサイトにアクセスできます！"
echo ""
