# Claude Code Webの環境での注意事項

CLAUDE_CODE_REMOTE 環境変数が設定されているかどうかで、Claude Code Webの環境かどうかを判断します。

```
if [ -n "$CLAUDE_CODE_REMOTE" ]; then echo "Claude Code Webです"; else echo "Claude Code Webではありません"; fi
```

## 環境セットアップ

pythonの実行をするまえに、.claude/claude_code_web_setup.sh を実行することで、環境セットアップを行うようにしてください。

```bash
./.claude/claude_code_web_setup.sh
```

"setup script completed" が出力されていれば成功です。
失敗した場合は、スクリプトを参考に、submoduleと.venvを手動でセットアップしてください。


## pythonの実行（セットアップが完了している場合）

```bash
python3 src/package/path/to/script.py
```

```bash
python3 -m pytest tests
```
