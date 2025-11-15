# 未解決の問題と今後の課題

**作成日**: 2025-11-15
**調査対象**: Firefox + Playwright プロキシ設定

## 🔴 未解決の問題

### 1. playwright-mcp + Firefoxでの完全な検証ができていない

**問題**:
- npx経由のplaywright MCPサーバーがFirefoxを見つけられない
- ブラウザインストールの問題により実際の動作確認ができず

**現状**:
- MCPサーバー自体は起動成功
- ツール一覧の取得も成功
- しかし`browser_navigate`実行時にエラー：
  ```
  Error: Browser specified in your config is not installed.
  ```

**影響**:
- playwright MCPサーバーでproxy.pyなしの動作が確認できていない
- Claude Code組み込みのMCPクライアントでのテストも未完了

**必要な対応**:
1. npx playwright install firefoxの適切な実行方法を確認
2. グローバルにインストールする方法を試す
3. MCPサーバーがFirefoxを見つけられるようにパスを設定

**参照**:
- テストスクリプト: `investigation/playwright/test_03_mcp_with_python_client.py`
- レポート: `investigation/playwright/FIREFOX_PROXY_INVESTIGATION_REPORT.md` (行145)

---

### 2. extraHTTPHeaders方式のMCP実装が未検証

**問題**:
- Python Playwrightでは動作確認済み
- しかしplaywright MCPサーバーでextraHTTPHeadersを使う実装は未検証
- MCPサーバー側でこの機能をサポートしているか不明

**現状**:
- Python Playwrightのテストコード: ✅ 動作確認済み
  ```python
  context = browser.new_context(
      extra_http_headers={
          "Proxy-Authorization": f"Basic {auth_b64}"
      }
  )
  ```
- playwright MCPサーバー: ❓ 未検証

**影響**:
- proxy.pyなしのシンプルな構成が実現できない可能性
- MCPサーバー側の実装変更が必要な場合がある

**必要な対応**:
1. playwright MCPサーバーのソースコードを確認
2. extraHTTPHeadersをサポートしているか調査
3. サポートしていない場合：
   - カスタムMCPサーバーの実装を検討
   - またはプルリクエストを提出

**参照**:
- テストスクリプト: `investigation/playwright/test_07_extra_http_headers.py`
- レポート: `investigation/playwright/FIREFOX_PROXY_INVESTIGATION_REPORT.md` (行355-404)

---

### 3. Chromiumでの詳細な検証が不十分

**問題**:
- Firefoxの調査に注力したため、Chromiumでの同様のテストは一部のみ
- Chromiumでproxy.pyが本当に必須かは確認済みだが、より詳細な検証は未実施

**現状**:
- Chromium + route(): ❌ 失敗確認済み（Unsafe header）
- Chromium + extraHTTPHeaders: ❌ 失敗確認済み（ERR_INVALID_ARGUMENT）
- Chromium + proxy.py: ⚠️ 過去のテストでは成功しているが、今回は未実施

**影響**:
- Chromiumでのベストプラクティスが不明確
- proxy.py以外の代替手段があるかもしれない

**必要な対応**:
1. Chromiumでproxy.py経由のテストを再実施
2. Chromium固有の設定やオプションを調査
3. Chromiumでの最適な構成を文書化

**参照**:
- テストスクリプト: `investigation/playwright/test_06_route_chromium.py`
- テストスクリプト: `investigation/playwright/test_07_extra_http_headers.py`

---

### 4. 他の環境での動作確認が未実施

**問題**:
- すべてのテストはClaude Code Web環境で実施
- 他の環境（ローカルマシン、CI/CD環境）での動作は未確認

**現状**:
- Claude Code Web環境: ✅ 動作確認済み
- ローカルマシン: ❓ 未検証
- GitHub Actions: ❓ 未検証
- Docker環境: ❓ 未検証

**影響**:
- 環境依存の問題が潜んでいる可能性
- 他の開発者が同じ手順で再現できない可能性

**必要な対応**:
1. ローカル開発環境でのテストを実施
2. CI/CD環境での動作確認
3. 環境ごとの差異を文書化

---

### 5. パフォーマンス比較が未実施

**問題**:
- proxy.py経由とextraHTTPHeaders方式のパフォーマンス差は未測定
- レイテンシやスループットの比較データなし

**現状**:
- 定性的な比較のみ（「レイテンシが若干改善」など）
- 定量的なデータなし

**影響**:
- 実際のパフォーマンス差が不明
- どちらの方式を選ぶべきか判断材料が不足

**必要な対応**:
1. 同じURLに対して複数回アクセスして時間を測定
2. proxy.py経由とextraHTTPHeaders方式を比較
3. 結果をグラフやテーブルで可視化

**測定項目**:
- ブラウザ起動時間
- ページ読み込み時間
- スクリーンショット取得時間
- メモリ使用量

---

### 6. セキュリティ面の評価が不十分

**問題**:
- extraHTTPHeadersでProxy-Authorizationを設定することのセキュリティリスク評価が未実施
- proxy.pyとの比較でのセキュリティ上の利点・欠点の整理が不十分

**現状**:
- 機能的な検証のみ
- セキュリティ面の詳細な分析なし

**懸念事項**:
1. **認証情報の漏洩リスク**
   - extraHTTPHeadersで設定した情報がどこまで伝播するか
   - ログに記録される可能性

2. **中間者攻撃への耐性**
   - proxy.pyとextraHTTPHeadersでの違い
   - 証明書検証の動作差異

3. **認証情報の管理**
   - 環境変数からの読み込み
   - メモリ上での保持期間

**必要な対応**:
1. セキュリティ専門家によるレビュー
2. 認証情報の取り扱いに関するベストプラクティスの文書化
3. ログ出力の確認と機密情報のマスキング検討

---

## 🟡 制限事項（現時点で解決困難）

### 7. Chromiumでproxy.pyなしの実現は不可能

**理由**:
- Chromiumは`Proxy-Authorization`を「Unsafe header」として扱う
- セキュリティポリシーによりPlaywrightからの設定を拒否

**影響**:
- Chromiumを使う場合はproxy.pyが必須
- Firefox限定の最適化となる

**対応方針**:
- Chromiumではproxy.pyを使い続ける
- Firefoxのみ使用する場合はextraHTTPHeadersを検討

---

### 8. playwright MCPサーバーのカスタマイズが必要な可能性

**問題**:
- 標準のplaywright MCPサーバーがextraHTTPHeadersをサポートしていない可能性
- カスタムMCPサーバーの実装が必要かもしれない

**影響**:
- proxy.pyなしの構成を実現するためにはMCPサーバーの開発が必要
- メンテナンスコストの増加

**対応方針**:
1. まずは標準MCPサーバーの機能を確認
2. サポートしていない場合：
   - アップストリームにフィーチャーリクエストを提出
   - または独自のMCPサーバー実装を検討

---

## 🟢 今後の推奨アクション

### 短期（1週間以内）

1. **playwright-mcp + Firefoxの問題を解決**
   - Firefoxのインストール方法を調査
   - MCPサーバーでの動作確認を完了

2. **ドキュメントの充実**
   - 未解決の問題を明記
   - 制限事項を明確化

### 中期（1ヶ月以内）

3. **playwright MCPサーバーの調査**
   - extraHTTPHeadersのサポート状況を確認
   - 必要に応じてカスタム実装を検討

4. **パフォーマンス測定**
   - proxy.py vs extraHTTPHeadersのベンチマーク実施
   - 結果を文書化

### 長期（3ヶ月以内）

5. **セキュリティ評価**
   - セキュリティ専門家によるレビュー
   - ベストプラクティスの策定

6. **他環境での検証**
   - ローカル環境、CI/CD環境でのテスト
   - 環境依存の問題を特定

---

## 📊 優先度マトリクス

| 問題 | 重要度 | 緊急度 | 優先度 |
|------|-------|-------|--------|
| 1. playwright-mcp検証 | 高 | 高 | **最優先** |
| 2. extraHTTPHeaders MCP実装 | 高 | 中 | **高** |
| 3. Chromium詳細検証 | 中 | 低 | 中 |
| 4. 他環境での動作確認 | 中 | 低 | 中 |
| 5. パフォーマンス比較 | 低 | 低 | 低 |
| 6. セキュリティ評価 | 高 | 中 | **高** |

---

## 📝 まとめ

### 現時点での推奨

**Firefoxを使う場合**:
- 当面はproxy.pyを使用する実装を維持（安定性重視）
- playwright-mcpの問題解決後、extraHTTPHeaders方式を検討

**Chromiumを使う場合**:
- proxy.pyが必須（代替手段なし）

### 次のステップ

1. ✅ 調査レポート作成完了
2. ⏳ playwright-mcp + Firefoxの問題解決（最優先）
3. ⏳ セキュリティ評価の実施（高優先）
4. ⏳ extraHTTPHeaders MCP実装の検討（高優先）
