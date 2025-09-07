# Notion Public Page Scanner

NotionワークスペースにおけるPublicページを検出し、セキュリティリスクを評価するツールです。

## 特徴

- 全ページの公開状態を自動スキャン
- リスクレベルに基づく評価（高/中/低）
- JSON/CSV形式でのレポート出力
- 詳細なセキュリティ推奨事項の提供

## インストール

```bash
# リポジトリのクローン
git clone https://github.com/truefinder/notion_public_page_search.git
cd notion_public_page_search

# 依存パッケージのインストール
pip install requests
```

## セットアップ

1. [Notion Integrations](https://www.notion.so/my-integrations) にアクセス
2. 新しいインテグレーションを作成
3. 取得したトークンを `settings.py` に設定
4. ワークスペースにインテグレーションを連携

```python
# settings.py
NOTION_TOKEN = "your_notion_integration_token"
```

## 使用方法

```bash
# JSONレポートの生成
python main.py -f json -o report.json

# CSVレポートの生成
python main.py -f csv -o report.csv

# 両方のフォーマットで出力
python main.py -f both -o report.json
```

### コマンドラインオプション

- `-f, --format`: 出力形式を指定（必須）
  - `json`: JSONファイルのみ出力
  - `csv`: CSVファイルのみ出力
  - `both`: 両方の形式で出力
- `-o, --output`: 出力ファイル名を指定（拡張子含む）

## 出力形式

### JSON形式
```json
{
  "scan_timestamp": "2024-01-01T12:00:00",
  "total_pages_scanned": 100,
  "potential_public_pages": [...],
  "security_recommendations": [...],
  "risk_summary": {
    "high_risk": 0,
    "medium_risk": 0,
    "low_risk": 0
  }
}
```

### CSV形式
以下の列を含むCSVファイルが生成されます：
- ページタイトル
- URL
- リスクレベル
- 公開指標
- 最終編集日時

## セキュリティ評価基準

- **高リスク**: 複数の公開指標が検出された場合
- **中リスク**: 単一の公開指標が検出された場合
- **低リスク**: 公開指標が検出されない場合

## 注意事項

- このツールはNotion APIの制限により、100%の精度を保証するものではありません
- 定期的なスキャンと手動での確認を推奨します
- 重要な情報を含むページは特に注意して管理してください

## ライセンス

Apache 2.0 License 

## 作者

Seunghyun Seo

## 貢献

1. このリポジトリをフォーク
2. 新しいブランチを作成 (`git checkout -b feature/improvement`)
3. 変更をコミット (`git commit -am 'Add new feature'`)
4. ブランチにプッシュ (`git push origin feature/improvement`)
5. プルリクエストを作成
